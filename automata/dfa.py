from dataclasses import dataclass
from pathlib import Path
from typing import List, Mapping, Tuple

from automata.automaton import Automaton


@dataclass(frozen=True, eq=False)
class DFA(Automaton[str, str]):
    def __post_init__(self):
        super().__post_init__()

        # make sure DFA transition function is total
        for state in self.Q:
            for symbol in self.Σ:
                if (state, symbol) not in self.δ:
                    raise ValueError(
                        f"Transition function is not total: missing ({state}, {symbol})")

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

    def remove_states(self, states: set[str]) -> "DFA":
        if self.q0 in states:
            raise ValueError("Cannot remove the start state.")

        new_δ = {k: v for k, v in self.δ.items(
        ) if k[0] not in states and v not in states}

        return type(self)(
            Q=self.Q - states,
            Σ=self.Σ,
            δ=new_δ,
            q0=self.q0,
            F=self.F - states,
        )

    def save(self, out_base: str) -> Path:
        sorted_Q = sorted(self.Q)
        sorted_Σ = sorted(self.Σ)

        states = f"{len(self.Q)} [{", ".join(sorted_Q)}]"
        alphabet = f"{len(self.Σ)} [{', '.join(sorted_Σ)}]"
        transitions: List[str] = []

        for src in sorted(self.Q):
            transition_row: List[str] = []
            for sym in sorted(self.Σ):
                dst = self.δ.get((src, sym))
                transition_row.append(str(sorted_Q.index(dst)) if dst else "")

            transitions.append(", ".join(transition_row))

        lines = [states, alphabet] + transitions + [
            str(sorted_Q.index(self.q0)),
            f"{', '.join(sorted(str(sorted_Q.index(f)) for f in self.F))}"
        ]

        path_obj = Path(f"{out_base}.dfauto")

        with open(path_obj, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))

        return path_obj
