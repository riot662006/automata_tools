from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from functools import lru_cache
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


SymT = TypeVar("SymT", bound=Hashable)  # symbol type
DstT = TypeVar("DstT")  # destination payload type


@dataclass(frozen=True, eq=False)
class Automaton(Generic[SymT, DstT], ABC):
    Q: frozenset[str]
    Σ: frozenset[str]
    δ: Mapping[tuple[str, SymT], DstT]
    q0: str
    F: frozenset[str]

    _edges: Mapping[str, Mapping[str, Tuple[SymT, ...]]
                    ] = field(init=False, repr=False)
    __hash__ = object.__hash__

    def _generate_edges(self):
        by_src: Dict[str, Dict[str, List[SymT]]] = {}
        for (src, sym), dst in self.δ.items():
            if isinstance(dst, (set, frozenset)):
                for d in dst:  # type: ignore[union-attr]
                    by_src.setdefault(src, {}).setdefault(d, []).append(  # type: ignore[union-attr]
                        sym
                    )
            else:
                by_src.setdefault(src, {}).setdefault(dst, []).append(  # type: ignore[union-attr]
                    sym
                )

        # freeze, sort symbols, and wrap read-only
        frozen: Dict[str, MappingProxyType[str, Tuple[SymT, ...]]] = {}
        for src, dst_map in by_src.items():
            inner: Dict[str, Tuple[SymT, ...]] = {
                dst: tuple(sorted(syms, key=sym_sort_key))
                for dst, syms in dst_map.items()
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

    def get_automaton_type(self) -> str:
        return str(self.__class__.__name__)

    @abstractmethod
    def _transition_impl(self, state: str, symbol: str) -> str | set[str]:
        pass

    @lru_cache(maxsize=None)
    def _transition_cached(self, state: str, symbol: str) -> str | set[str]:
        return self._transition_impl(state, symbol)

    def transition(self, state: str, symbol: str) -> str | set[str]:
        return self._transition_cached(state, symbol)

    @property
    def edges(self) -> Mapping[str, Mapping[str, Tuple[SymT, ...]]]:
        return self._edges

    @abstractmethod
    def get_tuples(
        self,
    ) -> Tuple[
        frozenset[str],
        frozenset[str],
        Mapping[Tuple[str, SymT], DstT],
        str,
        frozenset[str],
    ]:
        pass

    @abstractmethod
    def accepts(self, word: str) -> bool:
        pass

    @abstractmethod
    def formatted_transition(self, state: str, symbol: SymT) -> str:
        pass

    @abstractmethod
    def get_transition_table(self) -> list[list[str]]:
        pass

    @abstractmethod
    def remove_states(self, states: set[str]) -> "Automaton[SymT, DstT]":
        pass

    @abstractmethod
    def save(self, out_base: str) -> None:
        pass