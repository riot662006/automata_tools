from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Tuple


@dataclass
class State:
    name: str
    meta: dict[str, Any] = field(default_factory=dict)  # type: ignore

    def kill(self) -> None:
        self.meta["dead"] = True

    def ensure_alive(self) -> None:
        self.meta["dead"] = False

    def is_dead(self) -> bool:
        return self.meta.get("dead", False)


@dataclass
class Letter:
    char: str
    meta: dict[str, Any] = field(default_factory=dict)  # type: ignore

    def kill(self) -> None:
        self.meta["dead"] = True

    def ensure_alive(self) -> None:
        self.meta["dead"] = False

    def is_dead(self) -> bool:
        return self.meta.get("dead", False)


class _Index:
    def __init__(self) -> None:
        # Core transition map
        self.delta: dict[tuple[int, int], set[int]] = {}

        # Lazy caches
        self._out: dict[int, dict[int, set[int]]] | None = None
        self._inn: dict[int, dict[int, set[int]]] | None = None
        self._edges: dict[int, list[tuple[int, int, int]]] | None = None

    # -------------------------------------------------------------
    # Internal cache invalidation
    # -------------------------------------------------------------
    def _invalidate(self) -> None:
        """Clear all derived caches."""
        self._out = None
        self._inn = None
        self._edges = None

    # -------------------------------------------------------------
    # Lazy construction utilities
    # -------------------------------------------------------------
    def _ensure_out_inn(self) -> None:
        if self._out is not None and self._inn is not None:
            return
        out: dict[int, dict[int, set[int]]] = {}
        inn: dict[int, dict[int, set[int]]] = {}
        for (src, sym), dsts in self.delta.items():
            out.setdefault(src, {}).setdefault(sym, set()).update(dsts)
            for dst in dsts:
                inn.setdefault(dst, {}).setdefault(sym, set()).add(src)
        self._out = out
        self._inn = inn

    def _ensure_edges(self) -> None:
        if self._edges is not None:
            return
        edges: dict[int, list[tuple[int, int, int]]] = {}
        for (src, sym), dsts in self.delta.items():
            edges.setdefault(src, []).extend((src, sym, dst) for dst in dsts)
        self._edges = edges

    # -------------------------------------------------------------
    # Public read-only accessors
    # -------------------------------------------------------------
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

    # -------------------------------------------------------------
    # Mutation methods (always clear caches)
    # -------------------------------------------------------------
    def add(self, src: int, sym: int, dst: int) -> None:
        """Add a single transition (src, sym -> dst)."""
        row = self.delta.setdefault((src, sym), set())
        if dst not in row:
            row.add(dst)
            self._invalidate()

    def remove(self, src: int, sym: int, dst: int) -> None:
        """Remove a single transition if present."""
        row = self.delta.get((src, sym))
        if not row or dst not in row:
            return
        row.remove(dst)
        if not row:
            del self.delta[(src, sym)]
        self._invalidate()

    def set(self, src: int, sym: int, dsts: Iterable[int]) -> None:
        """Replace all transitions for (src, sym)."""
        self.delta[(src, sym)] = set(dsts)
        if not self.delta[(src, sym)]:
            del self.delta[(src, sym)]
        self._invalidate()

    def clear(self) -> None:
        """Clear all transitions."""
        self.delta.clear()
        self._invalidate()


class DFAV2:
    def __init__(
        self,
        Q: set[str],
        Σ: set[str],
        δ: dict[tuple[str, str], str],
        q0: str,
        F: set[str],
    ):
        self.states: list[State] = []
        self.name_to_sid: dict[str, int] = {}

        self.alphabet: list[Letter] = []
        self.char_to_aid: dict[str, int] = {}

        self._tx = _Index()

        # Important: define _editing before entering the context
        self._editing = False

        with self.edit():
            self.add_states(Q)
            self.add_letters(Σ)
            self.add_transitions(δ)

        # Lookups after construction
        self.start_sid = self._sid_of(q0)
        self.final_sids: set[int] = {self._sid_of(f) for f in F}

    # --- id helpers ---
    def _sid_of(self, state: str | State) -> int:
        name = state.name if isinstance(state, State) else state
        return self.name_to_sid[name]

    def _aid_of(self, char: str | Letter) -> int:
        c = char.char if isinstance(char, Letter) else char
        return self.char_to_aid[c]

    def get_state(self, name: str) -> State:
        return self.states[self._sid_of(name)]

    def get_letter(self, char: str) -> Letter:
        return self.alphabet[self.char_to_aid[char]]

    # --- automaton properties ----
    @property
    def Q(self) -> set[str]:
        return {state.name for state in self.states if not state.is_dead()}

    @property
    def Σ(self) -> set[str]:
        # only live letters
        return {letter.char for letter in self.alphabet if not letter.is_dead()}

    @property
    def δ(self) -> dict[tuple[str, str], set[str]]:
        # live view: ignore dead sources and dead symbols; filter dead destinations
        out: dict[tuple[str, str], set[str]] = {}
        for (src_id, sym_id), dsts in self._tx.delta.items():
            src = self.states[src_id]
            sym = self.alphabet[sym_id]
            if src.is_dead() or sym.is_dead():
                continue
            live_dsts = {
                self.states[dst].name for dst in dsts if not self.states[dst].is_dead()}
            out[(src.name, sym.char)] = live_dsts
        return out

    @property
    def q0(self) -> str:
        return self.states[self.start_sid].name

    @property
    def F(self) -> set[str]:
        return {state.name for state in (self.states[state_id] for state_id in self.final_sids) if not state.is_dead()}

    # --- mutators (guarded by edit) ---
    def add_states(self, states: Iterable[str]) -> None:
        if not self._editing:
            raise RuntimeError("Cannot add states outside of edit context.")
        for name in states:
            if name not in self.name_to_sid:
                state = State(name)
                self.name_to_sid[name] = len(self.states)
                self.states.append(state)
            else:
                state = self.get_state(name)
            state.ensure_alive()

    def add_letters(self, letters: Iterable[str]) -> None:
        if not self._editing:
            raise RuntimeError("Cannot add letters outside of edit context.")
        for char in letters:
            if char not in self.char_to_aid:
                letter = Letter(char)
                self.char_to_aid[char] = len(self.alphabet)
                self.alphabet.append(letter)
            else:
                self.get_letter(char).ensure_alive()

    def add_transitions(self, transitions: Mapping[Tuple[str, str], Iterable[str] | str]) -> None:
        if not self._editing:
            raise RuntimeError(
                "Cannot add transitions outside of edit context.")

        # Bucket by (sid, aid) to minimize index mutations
        buckets: dict[tuple[int, int], set[int]] = {}

        for (src, sym), dsts in transitions.items():
            if isinstance(dsts, str):
                dst_iter = (dsts,)
            else:
                dst_iter = dsts
            sid = self._sid_of(src)
            aid = self._aid_of(sym)
            b = buckets.setdefault((sid, aid), set())
            for dst in dst_iter:
                b.add(self._sid_of(dst))

        # Additive semantics: keep existing + union new (do NOT purge; you rely on “ignore dead”)
        for (sid, aid), new_dids in buckets.items():
            for did in new_dids:
                self._tx.add(sid, aid, did)

    def remove_states(self, states: Iterable[str]) -> None:
        if not self._editing:
            raise RuntimeError(
                "Cannot remove states outside of edit context.")
        for name in states:
            self.states[self._sid_of(name)].kill()

    def remove_letters(self, letters: Iterable[str]) -> None:
        """
        Mark letters as dead (do not purge edges). Live view/validity will ignore them.
        Must be called inside `with self.edit():`.
        """
        if not self._editing:
            raise RuntimeError(
                "Cannot remove letters outside of edit context.")
        for char in letters:
            self.get_letter(char).kill()

    def remove_transitions(self, transitions: Mapping[Tuple[str, str], Iterable[str] | str]) -> None:
        if not self._editing:
            raise RuntimeError(
                "Cannot remove transitions outside of edit context.")

        # Bucket and then remove (ignores non-existent edges)
        buckets: dict[tuple[int, int], set[int]] = {}

        for (src, sym), dsts in transitions.items():
            if isinstance(dsts, str):
                dst_iter = (dsts,)
            else:
                dst_iter = dsts
            sid = self._sid_of(src)
            aid = self._aid_of(sym)
            b = buckets.setdefault((sid, aid), set())
            for dst in dst_iter:
                b.add(self._sid_of(dst))

        for (sid, aid), dids in buckets.items():
            for did in dids:
                self._tx.remove(sid, aid, did)

    # --- validation ---
    def is_valid_dfa(self) -> bool:
        # Valid if every LIVE state has exactly one LIVE destination per LIVE symbol
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
                live_dsts = {
                    d for d in self._tx.delta.get((sid, aid), set())
                    if not self.states[d].is_dead()
                }
                if len(live_dsts) != 1:
                    return False
        return True

    def transition(self, s_id: int, a_id: int, throw_on_dead: bool = True) -> set[int]:
        state = self.states[s_id]
        symbol = self.alphabet[a_id]

        if throw_on_dead and state.is_dead():
            raise ValueError(f"State {state.name!r} not in Q = {self.Q}")
        if throw_on_dead and symbol.is_dead():
            raise ValueError(f"Symbol {symbol.char!r} not in Σ = {self.Σ}")

        dst_ids = self._tx.delta.get((s_id, a_id), set())

        return {
            did
            for did in dst_ids
            if not self.states[did].is_dead()
        }

    def accepts(self, word: str) -> bool:
        states = {self.start_sid}

        for sym in word:
            if sym not in self.Σ:
                raise ValueError(
                    f"Symbol {sym!r} not in alphabet Σ = {self.Σ}")

            new_states: set[int] = set()

            for state in states:
                new_states |= self.transition(state, self._aid_of(sym))

            states = new_states

            if not states:
                return False

        return any(state in self.final_sids for state in states)

    @contextmanager
    def edit(self):
        # Enter edit mode
        was_editing = self._editing
        self._editing = True
        try:
            yield self
        finally:
            # Exit edit mode
            self._editing = was_editing
            if not self.is_valid_dfa():
                raise ValueError(
                    "Invalid DFA after edit() — each (state, symbol) must have exactly one destination.")
