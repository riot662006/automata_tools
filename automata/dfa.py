from dataclasses import dataclass, field
from typing import Mapping, Tuple, Dict, List
from types import MappingProxyType

@dataclass(frozen=True)
class DFA:
    Q: frozenset[str]
    Σ: frozenset[str]
    δ: Mapping[tuple[str, str], str]
    q0: str
    F: frozenset[str]

    _edges: Mapping[str, Mapping[str, Tuple[str, ...]]] = field(init=False, repr=False)

    def __post_init__(self):
        object.__setattr__(self, "Q", frozenset(self.Q))
        object.__setattr__(self, "Σ", frozenset(self.Σ))
        object.__setattr__(self, "F", frozenset(self.F))
        if not isinstance(self.δ, MappingProxyType):
            object.__setattr__(self, "δ", MappingProxyType(dict(self.δ)))

        by_src: Dict[str, Dict[str, List[str]]] = {}
        for (src, sym), dst in self.δ.items():
            by_src.setdefault(src, {}).setdefault(dst, []).append(sym)

        # freeze, sort symbols, and wrap read-only
        frozen: Dict[str, Mapping[str, Tuple[str, ...]]] = {}
        for src, dst_map in by_src.items():
            inner: Dict[str, Tuple[str, ...]] = {
                dst: tuple(sorted(syms)) for dst, syms in dst_map.items()
            }
            frozen[src] = MappingProxyType(inner)
        object.__setattr__(self, "_edges", MappingProxyType(frozen))

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
                raise ValueError(f"Symbol {sym!r} not in alphabet Σ = {self.Σ}")
            state = self.transition(state, sym)
        return state in self.F
