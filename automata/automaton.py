from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping


class _Epsilon:
    """Singleton sentinel for ε-transitions."""
    __slots__ = ()
    def __repr__(self) -> str:
        return "ε"

Epsilon = _Epsilon()

Symbol = str | _Epsilon

@dataclass(frozen=True)
class Automaton(ABC):
    Q: frozenset[str]
    Σ: frozenset[str]
    δ: Mapping[tuple[str, Symbol], Any]
    q0: str
    F: frozenset[str]

    _edges: Mapping[str, Mapping[str, set[str]]
                    ] = field(init=False, repr=False)

    @abstractmethod
    def _generate_edges(self):
        pass

    def _freeze_variables(self):
        object.__setattr__(self, "Q", frozenset(self.Q))
        object.__setattr__(self, "Σ", frozenset(self.Σ))
        object.__setattr__(self, "F", frozenset(self.F))

        frozen_δ = {
            key: (frozenset(value) if isinstance(value, set) else value)
            for key, value in self.δ.items()
        }

        if not isinstance(self.δ, MappingProxyType):
            object.__setattr__(self, "δ", MappingProxyType(frozen_δ))

    def __post_init__(self):
        self._freeze_variables()
        self._generate_edges()

    @abstractmethod
    def transition(self, state: str, symbol: Symbol) -> Any:
        pass

    @property
    def edges(self) -> Mapping[str, Mapping[str, set[str]]]:
        return self._edges

    @abstractmethod
    def get_tuples(self) -> tuple[frozenset[str], frozenset[str], Mapping[tuple[str, str], Any], str, frozenset[str]]:
        pass

    def transition(self, state: str, symbol: Symbol) -> Any:
        if (state, symbol) not in self.δ:
            raise ValueError(f"No transition defined for ({state}, {symbol})")
        return self.δ[(state, symbol)]

    def words_for_path(self, state_seq: list[str]) -> set[str]:
        """
        Given a sequence of states [s0, s1, ..., sk],
        return all strings that label that path.

        Raises:
            ValueError: if the path is invalid or no transitions exist.
        """
        if len(state_seq) < 2:
            raise ValueError("Path must contain at least two states.")

        words: set[str] = {""}
        for i in range(1, len(state_seq)):
            src, dst = state_seq[i - 1], state_seq[i]

            if src not in self.edges:
                raise ValueError(f"No outgoing transitions from state {src!r}")

            if dst not in self.edges[src]:
                raise ValueError(f"No transition from {src!r} to {dst!r}")

            letters = self.edges[src][dst]
            if not letters:
                raise ValueError(
                    f"Transition {src!r} -> {dst!r} has no symbols")

            words = {w + letter for w in words for letter in letters}

        return words

    @abstractmethod
    def accepts(self, word: str) -> bool:
        pass
