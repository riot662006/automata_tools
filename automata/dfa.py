from dataclasses import dataclass
from typing import Mapping, Tuple

from automata.automaton import Automaton


@dataclass(frozen=True, eq=False)
class DFA(Automaton[str, str]):
    def __post_init__(self):
        super().__post_init__()

    def get_tuples(
        self,
    ) -> Tuple[
        frozenset[str],
        frozenset[str],
        Mapping[Tuple[str, str], str],
        str,
        frozenset[str],
    ]:
        return self.Q, self.Σ, self.δ, self.q0, self.F

    @property
    def edges(self) -> Mapping[str, Mapping[str, Tuple[str, ...]]]:
        return self._edges

    def _transition_impl(self, state: str, symbol: str) -> str:
        if (state, symbol) not in self.δ:
            raise ValueError(f"No transition defined for ({state}, {symbol})")
        return self.δ[(state, symbol)]

    def transition(self, state: str, symbol: str) -> str:
        return str(super().transition(state, symbol))

    def accepts(self, word: str) -> bool:
        state = self.q0
        for sym in word:
            if sym not in self.Σ:
                raise ValueError(
                    f"Symbol {sym!r} not in alphabet Σ = {self.Σ}")
            state = self.transition(state, sym)
        return state in self.F

    def formatted_transition(self, state: str, symbol: str) -> str:
        return self.δ.get((state, symbol), "-")

    def get_transition_table(self) -> list[list[str]]:
        Q_sorted = sorted(self.Q)
        Σ_sorted = sorted(self.Σ)

        rows: list[list[str]] = [['state'] + Σ_sorted]

        for state in Q_sorted:
            row = [state]
            for sym in Σ_sorted:
                row.append(self.formatted_transition(state, sym))
            rows.append(row)

        return rows
