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

    _edges: Mapping[str, Mapping[str, Tuple[str, ...]]
                    ] = field(init=False, repr=False)

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
        
    def __getitem__(self, key: tuple[str, str]) -> str:
        if not (isinstance(key, tuple) and len(key) == 2):
            raise TypeError("DFA indices must be a (state, symbol) tuple")
        state, symbol = key
        # Optional: fast sanity checks (kept lightweight since DFA is immutable)
        if state not in self.Q:
            raise KeyError(f"Unknown state {state!r}")
        if symbol not in self.Σ:
            raise KeyError(f"Symbol {symbol!r} not in alphabet Σ")
        try:
            return self.δ[(state, symbol)]
        except KeyError:
            raise KeyError(f"No transition defined for ({state!r}, {symbol!r})") from None

    @property
    def edges(self) -> Mapping[str, Mapping[str, Tuple[str, ...]]]:
        return self._edges

    def transition(self, state: str, symbol: str) -> str:
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

    def accepts(self, word: str) -> bool:
        state = self.q0
        for sym in word:
            if sym not in self.Σ:
                raise ValueError(
                    f"Symbol {sym!r} not in alphabet Σ = {self.Σ}")
            state = self.transition(state, sym)
        return state in self.F
