from dataclasses import dataclass, field
from typing import Mapping, Tuple, Dict, List
from types import MappingProxyType

from automata.automaton import Automaton


@dataclass(frozen=True)
class NFA(Automaton):
    def get_tuples(self) -> Tuple[frozenset[str], frozenset[str], Mapping[Tuple[str, str], set[str]], str, frozenset[str]]:
        return set(self.Q), set(self.Σ), self.δ, self.q0, set(self.F)

    @property
    def edges(self) -> Mapping[str, Mapping[str, Tuple[str, ...]]]:
        return self._edges

    def transition(self, state: str, symbol: str) -> set[str]:
        raise NotImplementedError()
    
    def words_for_path(self, state_seq: list[str]) -> set[str]:
        raise NotImplementedError()

    def accepts(self, word: str) -> bool:
        raise NotImplementedError()
