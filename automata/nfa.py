from dataclasses import dataclass
from functools import lru_cache, cached_property
from types import MappingProxyType
from typing import Dict, List, Mapping, Optional, Tuple

from automata.automaton import Automaton, Epsilon, Symbol


@dataclass(frozen=True, eq=False)
class NFA(Automaton[Symbol, frozenset[str]]):
    def get_tuples(
        self,
    ) -> Tuple[
        frozenset[str],
        frozenset[str],
        Mapping[Tuple[str, Symbol], frozenset[str]],
        str,
        frozenset[str],
    ]:
        return self.Q, self.Σ, self.δ, self.q0, self.F

    @property
    def edges(self) -> Mapping[str, Mapping[str, Tuple[Symbol, ...]]]:
        return self._edges

    def _epsilon_closure_impl(
        self, state: str, visited: Optional[set[str]] = None
    ) -> set[str]:
        if visited is None:
            visited = set()
        if state in visited:
            return visited

        visited.add(state)
        for dst, syms in self._edges.get(state, {}).items():
            if Epsilon in syms:
                self._epsilon_closure_impl(dst, visited)
        return visited

    @lru_cache(maxsize=None)
    def epsilon_closure(self, state: str) -> set[str]:
        return self._epsilon_closure_impl(state)

    def _transition_impl(self, state: str, symbol: str) -> set[str]:
        next_states: set[str] = set()

        for es in self.epsilon_closure(state):
            next_states.update(self.δ.get((es, symbol), set()))
            for ns in list(self.δ.get((es, symbol), set())):
                next_states.update(self.epsilon_closure(ns))

        return set(next_states)

    def transition(self, state: str, symbol: str) -> set[str]:
        return set(super().transition(state, symbol))

    @cached_property
    def closed_edges(self) -> MappingProxyType[str, MappingProxyType[str, Tuple[str, ...]]]:
        """
        Like _edges, but computed using epsilon-closed transitions:
        d ∈ ε-closure(move(ε-closure(s), a))
        Returns:
            MappingProxyType:
                {
                src: MappingProxyType({
                        dst: (sym1, sym2, ...)
                    }),
                ...
                }
        """
        by_src: Dict[str, Dict[str, List[str]]] = {}

        for src in self.Q:
            for sym in self.Σ:
                # reuse your transition impl that already does ε before/after
                dests = self.transition(src, sym)
                if not dests:
                    continue
                dst_map = by_src.setdefault(src, {})
                for dst in dests:
                    dst_map.setdefault(dst, []).append(sym)

        # freeze, sort symbols, wrap read-only (same shape as _edges)
        frozen: Dict[str, MappingProxyType[str, Tuple[str, ...]]] = {}
        for src, dst_map in by_src.items():
            inner = {dst: tuple(sorted(syms)) for dst, syms in dst_map.items()}
            frozen[src] = MappingProxyType(inner)
        return MappingProxyType(frozen)

    def words_for_path(self, state_seq: list[str]) -> set[str]:
        raise NotImplementedError()

    def accepts(self, word: str) -> bool:
        pos_states = self.epsilon_closure(self.q0)

        for sym in word:
            if sym not in self.Σ:
                raise ValueError(
                    f"Symbol {sym!r} not in alphabet Σ = {self.Σ}")

            pos_states = {
                s for prev_state in pos_states for s in self.transition(prev_state, sym)
            }

        return len(pos_states & self.F) > 0

    def formatted_transition(self, state: str, symbol: Symbol) -> str:
        result = self.δ.get((state, symbol))
        if result:
            return ",".join(sorted(list(result)))
        return "-"

    def get_transition_table(self) -> list[list[str]]:
        Q_sorted = sorted(self.Q)
        Σ_sorted = sorted(self.Σ)

        rows: list[list[str]] = [['state'] + Σ_sorted + [str(Epsilon)]]

        for state in Q_sorted:
            row = [state]
            for sym in Σ_sorted + [Epsilon]:
                row.append(self.formatted_transition(state, sym))
            rows.append(row)

        return rows
