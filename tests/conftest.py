import pytest
from automata.parser import parse_dfa_file

@pytest.fixture
def simple_dfauto(tmp_path):
    content = "\n".join([
        "3 [q0, q1, q2]",
        "2 [a, b]",
        "1,0",
        "2,1",
        "2,0",
        "0",
        "1,2",
    ])
    p = tmp_path / "example.dfauto"
    p.write_text(content, encoding="utf-8")
    return p

@pytest.fixture
def dfa(simple_dfauto):
    # works whether parse_dfa_file returns DFA/NFA dataclass or dict with .get_tuples()
    d = parse_dfa_file(str(simple_dfauto))
    return d
