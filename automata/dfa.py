from dataclasses import dataclass
from typing import Set, Dict, Tuple

@dataclass
class DFA:
    Q: Set[str]                                   # states
    Σ: Set[str]                                   # alphabet
    δ: Dict[Tuple[str, str], str]                 # transition function
    q0: str                                       # start state
    F: Set[str]                                   # accept states

    def get_tuples(self):
        """Return the DFA components as a tuple."""
        return self.Q, self.Σ, self.δ, self.q0, self.F

    def transition(self, state: str, symbol: str) -> str:
        """Apply δ to move from state under symbol."""
        if (state, symbol) not in self.δ:
            raise ValueError(f"No transition defined for ({state}, {symbol})")
        return self.δ[(state, symbol)]

    def accepts(self, word: str) -> bool:
        """
        Run the DFA on a given input word (string of symbols).
        Returns True if the DFA ends in an accept state, False otherwise.
        """
        state = self.q0
        for sym in word:
            if sym not in self.Σ:
                raise ValueError(f"Symbol {sym!r} not in alphabet Σ = {self.Σ}")
            state = self.transition(state, sym)
        return state in self.F
