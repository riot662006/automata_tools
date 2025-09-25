from dataclasses import dataclass, field
from typing import Mapping, Tuple, Dict, List
from types import MappingProxyType

from automata.automaton import Automaton


@dataclass(frozen=True)
class DFA(Automaton):
    def get_tuples(self) -> Tuple[frozenset[str], frozenset[str], Mapping[Tuple[str, str], str], str, frozenset[str]]:
        return set(self.Q), set(self.Σ), self.δ, self.q0, set(self.F)

    @property
    def edges(self) -> Mapping[str, Mapping[str, Tuple[str, ...]]]:
        return self._edges

    def transition(self, state: str, symbol: str) -> str:
        if (state, symbol) not in self.δ:
            raise ValueError(f"No transition defined for ({state}, {symbol})")
        return self.δ[(state, symbol)]

    def accepts(self, word: str) -> bool:
        state = self.q0
        for sym in word:
            if sym not in self.Σ:
                raise ValueError(
                    f"Symbol {sym!r} not in alphabet Σ = {self.Σ}")
            state = self.transition(state, sym)
        return state in self.F
