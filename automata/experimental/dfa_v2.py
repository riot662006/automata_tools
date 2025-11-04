from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Tuple
import weakref


class RegAuto:
    # ---------------------------- Inner classes ----------------------------
    @dataclass
    class State:
        name: str
        meta: dict[str, Any] = field(default_factory=dict)  # type: ignore
        _owner: weakref.ReferenceType["RegAuto"] | None = field(default=None, repr=False, compare=False)

        def set_owner(self, owner: "RegAuto") -> None:
            self._owner = weakref.ref(owner)

        def _require_editing(self) -> "RegAuto":
            owner = self._owner() if self._owner else None
            if owner is None or not owner._editing:
                raise RuntimeError("State mutations are only allowed inside RegAuto.edit().")
            return owner

        def kill(self) -> None:
            self._require_editing()
            self.meta["dead"] = True

        def ensure_alive(self) -> None:
            self._require_editing()
            self.meta["dead"] = False

        def is_dead(self) -> bool:
            return self.meta.get("dead", False)

    @dataclass
    class Letter:
        char: str
        meta: dict[str, Any] = field(default_factory=dict)  # type: ignore
        _owner: weakref.ReferenceType["RegAuto"] | None = field(default=None, repr=False, compare=False)

        def set_owner(self, owner: "RegAuto") -> None:
            self._owner = weakref.ref(owner)

        def _require_editing(self) -> "RegAuto":
            owner = self._owner() if self._owner else None
            if owner is None or not owner._editing:
                raise RuntimeError("Letter mutations are only allowed inside RegAuto.edit().")
            return owner

        def kill(self) -> None:
            self._require_editing()
            self.meta["dead"] = True

        def ensure_alive(self) -> None:
            self._require_editing()
            self.meta["dead"] = False

        def is_dead(self) -> bool:
            return self.meta.get("dead", False)

    class _Index:
        def __init__(self) -> None:
            self.delta: dict[tuple[int, int], set[int]] = {}
            self._out: dict[int, dict[int, set[int]]] | None = None
            self._inn: dict[int, dict[int, set[int]]] | None = None
            self._edges: dict[int, list[tuple[int, int, int]]] | None = None

        # cache mgmt
        def _invalidate(self) -> None:
            self._out = None
            self._inn = None
            self._edges = None

        def _ensure_out_inn(self) -> None:
            if self._out is not None and self._inn is not None:
                return
            out: dict[int, dict[int, set[int]]] = {}
            inn: dict[int, dict[int, set[int]]] = {}
            for (src, sym), dsts in self.delta.items():
                out.setdefault(src, {}).setdefault(sym, set()).update(dsts)
                for dst in dsts:
                    inn.setdefault(dst, {}).setdefault(sym, set()).add(src)
            self._out, self._inn = out, inn

        def _ensure_edges(self) -> None:
            if self._edges is not None:
                return
            edges: dict[int, list[tuple[int, int, int]]] = {}
            for (src, sym), dsts in self.delta.items():
                edges.setdefault(src, []).extend((src, sym, dst) for dst in dsts)
            self._edges = edges

        # read-only views
        @property
        def out(self) -> dict[int, dict[int, set[int]]]:
            self._ensure_out_inn()
            return self._out or {}

        @property
        def inn(self) -> dict[int, dict[int, set[int]]]:
            self._ensure_out_inn()
            return self._inn or {}

        @property
        def edges(self) -> dict[int, list[tuple[int, int, int]]]:
            self._ensure_edges()
            return self._edges or {}

        # mutations (invalidate caches)
        def add(self, src: int, sym: int, dst: int) -> None:
            row = self.delta.setdefault((src, sym), set())
            if dst in row:
                return
            row.add(dst)
            self._invalidate()

        def remove(self, src: int, sym: int, dst: int) -> None:
            row = self.delta.get((src, sym))
            if not row or dst not in row:
                return
            row.remove(dst)
            if not row:
                del self.delta[(src, sym)]
            self._invalidate()

        def set(self, src: int, sym: int, dsts: Iterable[int]) -> None:
            s = set(dsts)
            if s:
                self.delta[(src, sym)] = s
            else:
                self.delta.pop((src, sym), None)
            self._invalidate()

        def clear(self) -> None:
            if not self.delta:
                return
            self.delta.clear()
            self._invalidate()

    # ---------------------------- RegAuto proper ----------------------------
    def __init__(
        self,
        Q: set[str],
        Σ: set[str],
        δ: dict[tuple[str, str], str],
        q0: str,
        F: set[str],
    ):
        self.states: list[RegAuto.State] = []
        self.name_to_sid: dict[str, int] = {}

        self.alphabet: list[RegAuto.Letter] = []
        self.char_to_aid: dict[str, int] = {}

        self._tx = RegAuto._Index()
        self._editing = False

        with self.edit():
            self.add_states(Q)
            self.add_letters(Σ)
            self.add_transitions(δ)

        self.start_sid = self._sid_of(q0)
        self.final_sids: set[int] = {self._sid_of(f) for f in F}

    # --- id helpers ---
    def _sid_of(self, state: "str | RegAuto.State") -> int:
        name = state.name if isinstance(state, RegAuto.State) else state
        return self.name_to_sid[name]

    def _aid_of(self, char: "str | RegAuto.Letter") -> int:
        c = char.char if isinstance(char, RegAuto.Letter) else char
        return self.char_to_aid[c]

    def get_state(self, name: str) -> "RegAuto.State":
        return self.states[self._sid_of(name)]

    def get_letter(self, char: str) -> "RegAuto.Letter":
        return self.alphabet[self.char_to_aid[char]]

    # --- properties ---
    @property
    def Q(self) -> set[str]:
        return {s.name for s in self.states if not s.is_dead()}

    @property
    def Σ(self) -> set[str]:
        return {a.char for a in self.alphabet if not a.is_dead()}

    @property
    def δ(self) -> dict[tuple[str, str], set[str]]:
        out: dict[tuple[str, str], set[str]] = {}
        for (sid, aid), dsts in self._tx.delta.items():
            s = self.states[sid]
            a = self.alphabet[aid]
            if s.is_dead() or a.is_dead():
                continue
            live = {self.states[d].name for d in dsts if not self.states[d].is_dead()}
            out[(s.name, a.char)] = live
        return out

    @property
    def q0(self) -> str:
        return self.states[self.start_sid].name

    @property
    def F(self) -> set[str]:
        return {self.states[sid].name for sid in self.final_sids if not self.states[sid].is_dead()}

    # --- mutators (edit-guarded) ---
    def add_states(self, states: Iterable[str]) -> None:
        if not self._editing:
            raise RuntimeError("Cannot add states outside of edit context.")
        for name in states:
            if name in self.name_to_sid:
                st = self.get_state(name)
                st.set_owner(self)
                st.ensure_alive()
                continue
            st = RegAuto.State(name, _owner=weakref.ref(self))
            self.name_to_sid[name] = len(self.states)
            self.states.append(st)

    def add_letters(self, letters: Iterable[str]) -> None:
        if not self._editing:
            raise RuntimeError("Cannot add letters outside of edit context.")
        for ch in letters:
            if ch in self.char_to_aid:
                lt = self.get_letter(ch)
                lt.set_owner(self)
                lt.ensure_alive()
                continue
            lt = RegAuto.Letter(ch, _owner=weakref.ref(self))
            self.char_to_aid[ch] = len(self.alphabet)
            self.alphabet.append(lt)

    def rename_state(self, old: str, new: str) -> None:
        if not self._editing:
            raise RuntimeError("Cannot rename states outside of edit context.")
        if new in self.name_to_sid and new != old:
            raise ValueError(f"State name {new!r} already exists.")
        sid = self._sid_of(old)
        self.states[sid].name = new
        # rebuild map to prevent duplicate keys landing in dict
        self.name_to_sid = {s.name: i for i, s in enumerate(self.states)}

    def rename_letter(self, old: str, new: str) -> None:
        if not self._editing:
            raise RuntimeError("Cannot rename letters outside of edit context.")
        if new in self.char_to_aid and new != old:
            raise ValueError(f"Letter {new!r} already exists.")
        aid = self._aid_of(old)
        self.alphabet[aid].char = new
        self.char_to_aid = {a.char: i for i, a in enumerate(self.alphabet)}

    def add_transitions(self, transitions: Mapping[Tuple[str, str], Iterable[str] | str]) -> None:
        if not self._editing:
            raise RuntimeError("Cannot add transitions outside of edit context.")
        buckets: dict[tuple[int, int], set[int]] = {}
        for (src, sym), dsts in transitions.items():
            dst_iter = (dsts,) if isinstance(dsts, str) else dsts
            sid, aid = self._sid_of(src), self._aid_of(sym)
            b = buckets.setdefault((sid, aid), set())
            for dst in dst_iter:
                b.add(self._sid_of(dst))
        for (sid, aid), dids in buckets.items():
            for did in dids:
                self._tx.add(sid, aid, did)

    def remove_transitions(self, transitions: Mapping[Tuple[str, str], Iterable[str] | str]) -> None:
        if not self._editing:
            raise RuntimeError("Cannot remove transitions outside of edit context.")
        buckets: dict[tuple[int, int], set[int]] = {}
        for (src, sym), dsts in transitions.items():
            dst_iter = (dsts,) if isinstance(dsts, str) else dsts
            sid, aid = self._sid_of(src), self._aid_of(sym)
            b = buckets.setdefault((sid, aid), set())
            for dst in dst_iter:
                b.add(self._sid_of(dst))
        for (sid, aid), dids in buckets.items():
            for did in dids:
                self._tx.remove(sid, aid, did)

    def remove_states(self, states: Iterable[str]) -> None:
        if not self._editing:
            raise RuntimeError("Cannot remove states outside of edit context.")
        for name in states:
            self.states[self._sid_of(name)].kill()

    def remove_letters(self, letters: Iterable[str]) -> None:
        if not self._editing:
            raise RuntimeError("Cannot remove letters outside of edit context.")
        for ch in letters:
            self.get_letter(ch).kill()

    # --- validation / execution ---
    def is_valid_dfa(self) -> bool:
        if not any(not s.is_dead() for s in self.states):
            return False
        if not any(not a.is_dead() for a in self.alphabet):
            return False
        for sid, s in enumerate(self.states):
            if s.is_dead():
                continue
            for aid, a in enumerate(self.alphabet):
                if a.is_dead():
                    continue
                live_dsts = {d for d in self._tx.delta.get((sid, aid), set()) if not self.states[d].is_dead()}
                if len(live_dsts) != 1:
                    return False
        return True

    def transition(self, s_id: int, a_id: int, throw_on_dead: bool = True) -> set[int]:
        s, a = self.states[s_id], self.alphabet[a_id]
        if throw_on_dead and s.is_dead():
            raise ValueError(f"State {s.name!r} not in Q = {self.Q}")
        if throw_on_dead and a.is_dead():
            raise ValueError(f"Symbol {a.char!r} not in Σ = {self.Σ}")
        dst_ids = self._tx.delta.get((s_id, a_id), set())
        return {d for d in dst_ids if not self.states[d].is_dead()}

    def accepts(self, word: str) -> bool:
        states = {self.start_sid}
        for ch in word:
            if ch not in self.Σ:
                raise ValueError(f"Symbol {ch!r} not in alphabet Σ = {self.Σ}")
            aid = self._aid_of(ch)
            new_states: set[int] = set()
            for sid in states:
                new_states |= self.transition(sid, aid)
            states = new_states
            if not states:
                return False
        return any(sid in self.final_sids for sid in states)

    @contextmanager
    def edit(self):
        was = self._editing
        self._editing = True
        try:
            yield self
        finally:
            self._editing = was
            if not self.is_valid_dfa():
                raise ValueError(
                    "Invalid DFA after edit() — each (state, symbol) must have exactly one destination."
                )
