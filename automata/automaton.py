from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Dict, Generic, Hashable, List, Mapping, Tuple, TypeVar


class _Epsilon:
    """Singleton sentinel for ε-transitions."""
    __slots__ = ()

    def __repr__(self) -> str:
        return "ε"

    def __str__(self):
        return "ε"


Epsilon = _Epsilon()
Symbol = str | _Epsilon


def sym_sort_key(s: Any) -> tuple[int, str]:
    # strings first (lexicographically), then ε (or any non-str) after
    return (0, s) if isinstance(s, str) else (1, "")


SymT = TypeVar("SymT", bound=Hashable)      # symbol type
DstT = TypeVar("DstT")                      # destination payload type


@dataclass(frozen=True)
class Automaton(Generic[SymT, DstT], ABC):
    Q: frozenset[str]
    Σ: frozenset[str]
    δ: Mapping[tuple[str, SymT], DstT]
    q0: str
    F: frozenset[str]

    _edges: Mapping[str, Mapping[str, Tuple[SymT, ...]]
                    ] = field(init=False, repr=False)

    def _generate_edges(self):
        by_src: Dict[str, Dict[str, List[SymT]]] = {}
        for (src, sym), dst in self.δ.items():
            if isinstance(dst, (set, frozenset)):
                for d in dst:  # type: ignore[union-attr]
                    by_src.setdefault(src, {}).setdefault(
                        d, []).append(sym)  # type: ignore[union-attr]
            else:
                by_src.setdefault(src, {}).setdefault(
                    dst, []).append(sym)  # type: ignore[union-attr]

        # freeze, sort symbols, and wrap read-only
        frozen: Dict[str, MappingProxyType[str, Tuple[SymT, ...]]] = {}
        for src, dst_map in by_src.items():
            inner: Dict[str, Tuple[SymT, ...]] = {
                dst: tuple(sorted(syms, key=sym_sort_key)) for dst, syms in dst_map.items()
            }
            frozen[src] = MappingProxyType(inner)
        object.__setattr__(self, "_edges", MappingProxyType(frozen))

    def _freeze_variables(self):
        object.__setattr__(self, "Q", frozenset(self.Q))
        object.__setattr__(self, "Σ", frozenset(self.Σ))
        object.__setattr__(self, "F", frozenset(self.F))

        if not isinstance(self.δ, MappingProxyType):
            object.__setattr__(self, "δ", MappingProxyType(dict(self.δ)))

    def __post_init__(self):
        self._freeze_variables()
        self._generate_edges()

    @abstractmethod
    def transition(self, state: str, symbol: str) -> set[str] | str:
        pass

    @property
    def edges(self) -> Mapping[str, Mapping[str, Tuple[SymT, ...]]]:
        return self._edges

    @abstractmethod
    def get_tuples(self) -> Tuple[frozenset[str], frozenset[str], Mapping[Tuple[str, SymT], DstT], str, frozenset[str]]:
        pass

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
