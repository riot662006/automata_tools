from pathlib import Path

from automata.automaton import Epsilon
from tests.conftest import make_dfa, make_nfa


def read_text(p: Path) -> list[str]:
    return p.read_text(encoding="utf-8").splitlines()


# ───────────────────────────────
# 🔹 DFA save → .dfauto and format per spec
# ───────────────────────────────
def test_dfa_save_dfauto_format(tmp_path: Path):
    # DFA (total) for reference example:
    # Q={q0,q1,q2}, Σ={a,b}
    # δ(q0,a)=q1, δ(q0,b)=q0
    # δ(q1,a)=q2, δ(q1,b)=q1
    # δ(q2,a)=q2, δ(q2,b)=q0
    # q0 start; F={q1,q2}
    dfa = make_dfa(
        Q={"q0", "q1", "q2"},
        Σ={"a", "b"},
        δ={
            ("q0", "a"): "q1", ("q0", "b"): "q0",
            ("q1", "a"): "q2", ("q1", "b"): "q1",
            ("q2", "a"): "q2", ("q2", "b"): "q0",
        },
        q0="q0",
        F={"q1", "q2"},
    )

    out_base = tmp_path / "machine"
    dfa.save(str(out_base))  # should create machine.dfauto
    out_file = out_base.with_suffix(".dfauto")
    assert out_file.exists(), "DFA save must write a .dfauto file"

    lines = read_text(out_file)

    # Exact expected body per spec (no ε column for DFAs)
    expected = [
        "3 [q0, q1, q2]",
        "2 [a, b]",
        "1, 0",
        "2, 1",
        "2, 0",
        "0",
        "1, 2",  # indices of {q1,q2}; compact form is acceptable
    ]
    assert lines == expected


# ───────────────────────────────
# 🔹 NFA save → .nfauto and format per spec
# ───────────────────────────────
def test_nfa_save_nfauto_format(tmp_path: Path):
    # NFA with ε from q0→q1, no other edges; F={q1}
    # Q={q0,q1}, Σ={a,b}
    # Transition table has M+1 columns (a,b,ε); blanks are empty entries.
    nfa = make_nfa(
        Q={"q0", "q1"},
        Σ={"a", "b"},
        δ={
            ("q0", "a"): set(),
            ("q0", "b"): set(),
            # if your Epsilon is a symbol object, conftest maps it
            ("q0", Epsilon): {"q1"},
            ("q1", "a"): set(),
            ("q1", "b"): set(),
            # q1 has no ε
        },
        q0="q0",
        F={"q1"},
    )

    out_base = tmp_path / "machine_nfa"
    nfa.save(str(out_base))  # should create machine_nfa.nfauto
    out_file = out_base.with_suffix(".nfauto")
    assert out_file.exists(), "NFA save must write a .nfauto file"

    lines = read_text(out_file)

    # Expected body per spec (ε column present and last; empty entries allowed)
    # Sorted Q = [q0, q1], sorted Σ = [a, b]
    # Row for q0: a="", b="", ε="1"
    # Row for q1: a="", b="", ε=""
    expected = [
        "2 [q0, q1]",
        "2 [a, b]",
        ", , 1",
        ", , ",
        "0",
        "1",
    ]
    assert lines == expected


# ───────────────────────────────
# 🔹 NFA save with multi-destination entries (space-separated indices)
# ───────────────────────────────
def test_nfa_save_multi_destination_entries(tmp_path: Path):
    # NFA where q0 on 'a' goes to {q1,q2}; ε from q2 to q1; F={q1}
    nfa = make_nfa(
        Q={"q0", "q1", "q2"},
        Σ={"a"},
        δ={
            ("q0", "a"): {"q1", "q2"},
            ("q2", Epsilon): {"q1"},
        },
        q0="q0",
        F={"q1"},
    )

    out_base = tmp_path / "nfa_multi"
    nfa.save(str(out_base))
    out_file = out_base.with_suffix(".nfauto")
    assert out_file.exists()

    lines = read_text(out_file)

    # Sorted Q = [q0,q1,q2] → indices q0=0,q1=1,q2=2; Σ=[a]
    # For q0: a="1 2", ε=""              (space-separated destinations)
    # For q1: a="",   ε=""
    # For q2: a="",   ε="1"
    expected = [
        "3 [q0, q1, q2]",
        "1 [a]",
        "1 2, ",   # "a", then "ε" column
        ", ",
        ", 1",
        "0",
        "1",
    ]
    assert lines == expected
