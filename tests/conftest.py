from pathlib import Path
import pytest
from automata.parser import parse_dfa_file


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
