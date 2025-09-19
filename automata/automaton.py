from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping


class Epsilon:
    pass


@dataclass(frozen=True)
class Automaton:
    Q: frozenset[str]
    Σ: frozenset[str]
    δ: Mapping[tuple[str, str | Epsilon], Any]
    q0: str
    F: frozenset[str]

    _edges: Mapping[str, Mapping[str, set[str]]] = field(init=False, repr=False)

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
