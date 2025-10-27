from pathlib import Path
from typing import Mapping, Tuple
import pytest
from automata.automaton import Symbol
from automata.dfa import DFA
from automata.nfa import NFA
from automata.parser import parse_dfa_file

DFATransition = Mapping[Tuple[str, str], str]
NFATransition = Mapping[Tuple[str, Symbol], set[str]]

def make_dfa(
    Q: set[str],
    Σ: set[str],
    δ: DFATransition,
    q0: str,
    F: set[str],
) -> DFA:
    """
    Helper: construct DFA with given components. Your DFA/Automaton __post_init__
    will freeze sets and generate edges as nested MappingProxyType with tuple labels.
    """
    return DFA(
        Q=frozenset(Q),
        Σ=frozenset(Σ),
        δ={(k[0], k[1]): v for k, v in δ.items()},
        q0=q0,
        F=frozenset(F),
    )


def make_nfa(
    Q: set[str],
    Σ: set[str],
    δ: NFATransition,
    q0: str,
    F: set[str],
) -> NFA:
    """
    Helper: construct NFA with given components. Your NFA/Automaton __post_init__
    will freeze sets and generate edges as nested MappingProxyType with tuple labels.
    """
    return NFA(
        Q=frozenset(Q),
        Σ=frozenset(Σ),
        δ={(k[0], k[1]): frozenset(v) for k, v in δ.items()},
        q0=q0,
        F=frozenset(F),
    )


def write_dfauto(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "dfa.dfauto"
    p.write_text(content.strip() + "\n", encoding="utf-8")
    return p


@pytest.fixture
def simple_dfa(tmp_path: Path):
    content = """
    3 [q0, q1, q2]
    2 [a, b]
    1,0
    2,1
    2,0
    0
    1,2
    """
    return parse_dfa_file(str(write_dfauto(tmp_path, content)))


@pytest.fixture
def dfa_with_trap(tmp_path: Path):
    content = """
    3 [q0, q1, qT]
    2 [a, b]
    1,2
    0,2
    2,2
    0
    1
    """
    return parse_dfa_file(str(write_dfauto(tmp_path, content)))


@pytest.fixture
def dfa_multi_accept(tmp_path: Path):
    content = """
    3 [q0, q1, q2]
    2 [0, 1]
    1,2
    0,2
    2,2
    0
    1,2
    """
    return parse_dfa_file(str(write_dfauto(tmp_path, content)))
