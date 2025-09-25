from dataclasses import dataclass
from typing import Mapping, Tuple

from automata.automaton import Automaton, Symbol


@dataclass(frozen=True)
class NFA(Automaton[Symbol, frozenset[str]]):
    def get_tuples(self) -> Tuple[frozenset[str], frozenset[str], Mapping[Tuple[str, Symbol], frozenset[str]], str, frozenset[str]]:
        return self.Q, self.Σ, self.δ, self.q0, self.F

    @property
    def edges(self) -> Mapping[str, Mapping[str, Tuple[Symbol, ...]]]:
        return self._edges

    def transition(self, state: str, symbol: Symbol) -> set[str]:
        raise NotImplementedError()

    def words_for_path(self, state_seq: list[str]) -> set[str]:
        raise NotImplementedError()

    def accepts(self, word: str) -> bool:
        raise NotImplementedError()
