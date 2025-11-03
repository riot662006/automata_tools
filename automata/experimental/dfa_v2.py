from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Mapping, Optional, Set, Tuple


@dataclass
class State:
    name: str
    meta: dict[str, Any] = field(default_factory=dict)  # type: ignore

    def _kill(self) -> None:
        self.meta["dead"] = True

    def ensure_alive(self) -> None:
        self.meta["dead"] = False

    def is_dead(self) -> bool:
        return self.meta.get("dead", False)


@dataclass
class Letter:
    char: str
    meta: dict[str, Any] = field(default_factory=dict)  # type: ignore


class _Index:
    def __init__(self) -> None:
        # delta: (src_id, sym_id) -> set(dst_ids)
        self.delta: Dict[Tuple[int, int], Set[int]] = {}
        # out: src_id -> sym_id -> set(dst_ids)
        self.out: Dict[int, Dict[int, Set[int]]] = {}
        # inn: dst_id -> sym_id -> set(src_ids)
        self.inn: Dict[int, Dict[int, Set[int]]] = {}

    def add(self, src: int, sym: int, dst: int) -> None:
        self.delta.setdefault((src, sym), set()).add(dst)
        self.out.setdefault(src, {}).setdefault(sym, set()).add(dst)
        self.inn.setdefault(dst, {}).setdefault(sym, set()).add(src)

    def set(self, src: int, sym: int, dsts: Iterable[int]) -> None:
        # remove all prior edges for (src, sym)
        for dst in list(self.delta.get((src, sym), ())):
            self.remove(src, sym, dst)
        # add new set
        for dst in dsts:
            self.add(src, sym, dst)

    def remove(self, src: int, sym: int, dst: int) -> None:
        key = (src, sym)
        row = self.delta.get(key)
        if not row or dst not in row:
            return

        row.remove(dst)
        if not row:
            del self.delta[key]

        out_row = self.out.get(src, {}).get(sym)
        if out_row:
            out_row.discard(dst)
            if not out_row:
                self.out[src].pop(sym, None)
            if not self.out[src]:
                self.out.pop(src, None)

        inn_row = self.inn.get(dst, {}).get(sym)
        if inn_row:
            inn_row.discard(src)
            if not inn_row:
                self.inn[dst].pop(sym, None)
            if not self.inn[dst]:
                self.inn.pop(dst, None)


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

        self.tx = _Index()

        # Optional cache for a user-facing view of edges
        self.edges_cache: Optional[Dict[str,
                                        Dict[str, Tuple[str, ...]]]] = None
        self.dirty_edges = True

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
        return {letter.char for letter in self.alphabet}

    @property
    def δ(self) -> dict[tuple[str, str], set[str]]:
        return {(self.states[src].name, self.alphabet[sym].char):
                {self.states[dst].name for dst in dsts if not self.states[dst].is_dead()} for (src, sym), dsts in self.tx.delta.items() if not self.states[src].is_dead()}

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

    def add_transitions(self, transitions: Mapping[Tuple[str, str], Iterable[str] | str]) -> None:
        if not self._editing:
            raise RuntimeError(
                "Cannot add transitions outside of edit context.")
        # DFA semantics: exactly one dst per (src, sym) — use set() to hard-replace
        for (src, sym), dsts in transitions.items():
            if isinstance(dsts, str):
                dsts = [dsts]
            for dst in dsts:
                self.tx.add(self._sid_of(src), self._aid_of(
                    sym), self._sid_of(dst))
        self.dirty_edges = True

    # --- validation ---
    def is_valid_dfa(self) -> bool:
        # Every state must have exactly one outgoing edge per symbol
        num_states = len(self.states)
        num_syms = len(self.alphabet)
        if num_states == 0 or num_syms == 0:
            return False
        for sid in range(num_states):
            # if you later support "dead" states, you can skip them here if desired
            if self.states[sid].is_dead():
                continue

            for aid in range(num_syms):
                dsts = self.tx.delta.get((sid, aid), set())
                if len(dsts) != 1:
                    return False
        return True

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
