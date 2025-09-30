from dataclasses import dataclass
from typing import Mapping, Optional, Tuple

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

    def _transition_impl(self, state: str, symbol: str) -> set[str]:
        def epsilon_closure(state: str, visited: Optional[set[str]] = None) -> set[str]:
            if visited is None:
                visited = set()
            if state in visited:
                return visited

            visited.add(state)
            for dst, syms in self._edges.get(state, {}).items():
                if Epsilon in syms:
                    epsilon_closure(dst, visited)
            return visited

        next_states: set[str] = set()

        for es in epsilon_closure(state):
            next_states.update(self.δ.get((es, symbol), set()))
            for ns in list(self.δ.get((es, symbol), set())):
                next_states.update(epsilon_closure(ns))

        return set(next_states)

    def transition(self, state: str, symbol: str) -> set[str]:
        return set(super().transition(state, symbol))

    def words_for_path(self, state_seq: list[str]) -> set[str]:
        raise NotImplementedError()

    def accepts(self, word: str) -> bool:
        raise NotImplementedError()
