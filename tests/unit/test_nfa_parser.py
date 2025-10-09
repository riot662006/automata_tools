from pathlib import Path
import pytest
from typing import Mapping

from automata.automaton import Epsilon
from automata.parser import parse_nfa_file


def write_nfauto(tmp_path: Path, text: str):
    p = tmp_path / "nfa.nfauto"
    # allow short inline comments in test strings
    cleaned: list[str] = []
    for raw in text.strip().splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if line:
            cleaned.append(line)
    p.write_text("\n".join(cleaned) + "\n", encoding="utf-8")
    return p


def test_valid_nfa_with_epsilon_and_multi_targets(tmp_path: Path):
    """
    Format:
      line 1: |Q| [optional names]
      line 2: |Σ| [symbols]  (ε must NOT appear here)
      next |Q| lines: transitions: one column per Σ symbol, final column for ε
                      cells contain space-separated state indices (may be empty)
      start-state index
      accept-state indices (comma-separated)
    """
    content = """
    3 [q0, q1, qf]
    2 [a, b]
    1 2,        # q0: on 'a' -> {q1,q2}? (but q2 doesn't exist) – we use valid ones:
    1,          # fix below: we'll craft clean rows instead of comments
    """
    # Use a clean, explicit sample
    content = """
    3 [q0, q1, qf]
    2 [a, b]
    1,   , 1        # q0: a -> {q1}; b -> {}; ε -> {q1}
    2,   , 2        # q1: a -> {qf}; b -> {}; ε -> {qf}
    ,    ,          # qf: a -> {};   b -> {}; ε -> {}
    0
    2               # accept = {qf}
    """

    p = write_nfauto(tmp_path, content)
    nfa = parse_nfa_file(str(p))

    # sanity on tuple unpack
    Q, Σ, δ, q0, F = nfa.get_tuples()
    assert Q == frozenset({"q0", "q1", "qf"})
    assert Σ == frozenset({"a", "b"})
    assert q0 == "q0"
    assert F == frozenset({"qf"})

    # δ shape: Mapping[(state, symbol), frozenset[str]]
    assert isinstance(δ, Mapping)
    for (s, sym), dsts in δ.items():
        assert s in Q
        # symbols include str and the Epsilon sentinel
        if sym is not Epsilon:
            assert sym in Σ
        assert isinstance(dsts, frozenset)
        assert dsts.issubset(Q)

    # Specific transitions (space-separated lists were parsed)
    assert δ[("q0", "a")] == frozenset({"q1"})
    assert δ[("q0", "b")] == frozenset()
    assert δ[("q0", Epsilon)] == frozenset({"q1"})

    assert δ[("q1", "a")] == frozenset({"qf"})
    assert δ[("q1", "b")] == frozenset()
    assert δ[("q1", Epsilon)] == frozenset({"qf"})

    # no outgoing from qf in this sample
    assert δ[("qf", "a")] == frozenset()
    assert δ[("qf", "b")] == frozenset()
    assert δ[("qf", Epsilon)] == frozenset()


def test_symbols_cannot_include_epsilon_literal(tmp_path: Path):
    content = """
    1 [q0]
    1 [ε]
    ,          # q0 row: 1 Σ col + 1 ε col → here both empty
    0
    0
    """
    p = write_nfauto(tmp_path, content)
    with pytest.raises(ValueError):
        parse_nfa_file(str(p))


def test_wrong_number_of_transition_columns(tmp_path: Path):
    """
    Each transition row must have |Σ| + 1 comma-separated parts (last is ε).
    """
    content = """
    2 [q0, q1]
    2 [a, b]
    1,          # only 1 item; expected 3 (a, b, ε)
    1, ,        # row2 is fine but parser should fail on row1 first
    0
    1
    """
    p = write_nfauto(tmp_path, content)
    with pytest.raises(ValueError):
        parse_nfa_file(str(p))


def test_q0_out_of_range(tmp_path: Path):
    content = """
    2 [q0, q1]
    1 [a]
    , ,
    , ,
    2          # invalid (must be 0..1)
    1
    """
    p = write_nfauto(tmp_path, content)
    with pytest.raises(ValueError):
        parse_nfa_file(str(p))


def test_accept_states_required_non_empty(tmp_path: Path):
    content = """
    2 [q0, q1]
    1 [a]
    , ,
    , ,
    0
             # empty accept list → error per implementation
    """
    p = write_nfauto(tmp_path, content)
    with pytest.raises(ValueError):
        parse_nfa_file(str(p))


def test_multiple_destinations_space_separated(tmp_path: Path):
    """
    Ensure cells like '1 0' (space-separated) parse into {q1,q0}.
    """
    content = """
    3 [q0, q1, q2]
    1 [a]
    1 2,         # q0 on 'a' -> {q1,q2}; ε -> {}
    ,            # q1: no 'a'; ε -> {}
    ,            # q2: no 'a'; ε -> {}
    0
    2
    """
    p = write_nfauto(tmp_path, content)
    nfa = parse_nfa_file(str(p))
    _, _, δ, _, _ = nfa.get_tuples()
    assert δ[("q0", "a")] == frozenset({"q1", "q2"})
    assert δ[("q1", "a")] == frozenset()
    assert δ[("q2", "a")] == frozenset()
    assert δ[("q0", Epsilon)] == frozenset()
    assert δ[("q1", Epsilon)] == frozenset()
    assert δ[("q2", Epsilon)] == frozenset()


def test_minimum_lines_guard(tmp_path: Path):
    """
    Must have at least: 2 header lines + |Q| transition lines + 2 footer lines.
    """
    content = """
    2 [q0, q1]
    1 [a]
    , ,
    # MISSING second transition row, start, accept
    """
    p = write_nfauto(tmp_path, content)
    with pytest.raises(ValueError):
        parse_nfa_file(str(p))


def test_default_sigma_generated_when_not_provided(tmp_path: Path):
    """
    If Σ names list is omitted (second line like '2 []' or just count),
    your parser generates 'a','b',... and ensures 'ε' isn't included.
    This test simulates Σ omitted by passing empty names after the count.
    """
    content = """
    2 [q0, q1]
    2 []          # Σ_num=2, no names → default becomes ['a','b']
    , ,
    , ,
    0
    1
    """
    p = write_nfauto(tmp_path, content)
    nfa = parse_nfa_file(str(p))
    _, Σ, δ, _, _ = nfa.get_tuples()
    assert Σ == frozenset({"a", "b"})
    # and ε transitions exist as last column per format
    assert ("q0", Epsilon) in δ and ("q1", Epsilon) in δ

def test_default_reaching_epsilon_state(tmp_path: Path):
    """
    If Σ names list is omitted (second line like '2 []' or just count),
    your parser generates 'a','b',... and ensures 'ε' isn't included.
    This test simulates to make sure that 'ε' is not a reachable state.
    """
    len_to_reach_ε = ord('ε') - ord('a') + 1
    content = f"""
    2 [q0, q1]
    {len_to_reach_ε} []          # Σ_num=2, no names → default becomes ['a','b']
    {", " * len_to_reach_ε}
    {", " * len_to_reach_ε}
    0
    0
    """
    p = write_nfauto(tmp_path, content)
    nfa = parse_nfa_file(str(p))

    _, Σ, _, _, _ = nfa.get_tuples()
    assert 'ε' not in Σ and len(Σ) == len_to_reach_ε

    