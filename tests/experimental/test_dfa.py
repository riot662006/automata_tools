# tests/experimental/test_dfa.py
# ---------------------------------------------------------------------
# Imports & type aliases
# ---------------------------------------------------------------------
import pytest
from typing import Dict, Tuple

# adjust this import to your project path
from automata.experimental.dfa import DFA

DFAParams = Tuple[set[str], set[str],
                  dict[tuple[str, str], str], str, set[str]]


# ---------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------
@pytest.fixture
def simple_dfa_spec() -> DFAParams:
    Q = {"S", "A"}
    Sigma = {"a", "b"}
    delta: Dict[Tuple[str, str], str] = {
        ("S", "a"): "A",
        ("S", "b"): "S",
        ("A", "a"): "A",
        ("A", "b"): "S",
    }
    q0 = "S"
    F = {"A"}
    return Q, Sigma, delta, q0, F


@pytest.fixture
def built_dfa(simple_dfa_spec: DFAParams) -> DFA:
    Q, Sigma, delta, q0, F = simple_dfa_spec
    return DFA(Q, Sigma, delta, q0, F)


# ---------------------------------------------------------------------
# Construction / validity enforcement
# ---------------------------------------------------------------------
def test_construct_valid_dfa(built_dfa: DFA):
    dfa = built_dfa
    assert dfa.is_valid_dfa()
    # raw index shows determinism at (sid, aid)
    for sid in range(len(dfa.states)):
        for aid in range(len(dfa.alphabet)):
            dsts = dfa._tx.delta.get((sid, aid))  # type: ignore
            assert dsts is not None and len(dsts) == 1


def test_empty_Q_or_Sigma_is_invalid_for_dfa():
    with pytest.raises(ValueError):
        DFA(set(), {"a"}, {}, "S", set())
    with pytest.raises(ValueError):
        DFA({"S"}, set(), {}, "S", set())


def test_invalid_when_missing_transition(simple_dfa_spec: DFAParams):
    Q, Sigma, delta, q0, F = simple_dfa_spec
    delta = dict(delta)
    delta.pop(("A", "b"))
    with pytest.raises(ValueError):
        DFA(Q, Sigma, delta, q0, F)


def test_invalid_when_multiple_dsts_for_pair(simple_dfa_spec: DFAParams):
    Q, Sigma, delta, q0, F = simple_dfa_spec
    dfa = DFA(Q, Sigma, delta, q0, F)
    with pytest.raises(ValueError):
        with dfa.edit():
            sid = dfa._sid_of("S")  # type: ignore
            aid = dfa._aid_of("a")  # type: ignore
            # force nondeterminism directly via index
            dfa._tx.add(sid, aid, dfa._sid_of("S"))  # type: ignore


# ---------------------------------------------------------------------
# Edit-guarded mutations still apply; DFA enforces validity on exit
# ---------------------------------------------------------------------
def test_kill_state_requires_rewire_or_raises(simple_dfa_spec: DFAParams):
    Q, Sigma, delta, q0, F = simple_dfa_spec
    dfa = DFA(Q, Sigma, delta, q0, F)
    with pytest.raises(ValueError):
        with dfa.edit():
            # makes some (state, 'a') have 0 live dsts
            dfa.remove_states(["A"])


def test_kill_letter_does_not_require_rewire(built_dfa: DFA):
    dfa = built_dfa
    # remove 'a' -> it ceases to exist in Σ; DFA should remain valid
    with dfa.edit():
        dfa.remove_letters(["a"])
    assert dfa.is_valid_dfa()
    # Σ updated
    assert dfa.Σ == {"b"}
    # Using removed letter now counts as unknown symbol in accepts()
    with pytest.raises(ValueError):
        dfa.accepts("a")
    # Transitions on remaining live letters still behave
    assert not dfa.accepts("")     # still rejects empty
    assert not dfa.accepts("b")    # still rejects single 'b'
    # depends on your final state; with finals={'A'}, still reject
    assert not dfa.accepts("bb")


def test_removed_letter_keeps_raw_edges_but_ignored_live(built_dfa: DFA):
    dfa = built_dfa
    aid_a = dfa._aid_of("a")  # type: ignore
    sid_S = dfa._sid_of("S")  # type: ignore
    with dfa.edit():
        dfa.remove_letters(["a"])
    # raw index still has entries for (S, 'a') from construction
    assert (sid_S, aid_a) in dfa._tx.delta  # type: ignore
    # live δ omits 'a' entirely
    assert all(sym != "a" for (_, sym) in dfa.δ.keys())


def test_rewire_after_kill_restores_validity(simple_dfa_spec: DFAParams):
    Q, Sigma, delta, q0, F = simple_dfa_spec
    dfa = DFA(Q, Sigma, delta, q0, F)

    with dfa.edit():
        # Kill A and add sink Z; wire Z to itself on all letters
        dfa.remove_states(["A"])
        dfa.add_states({"Z"})
        for sym in Sigma:
            dfa.add_transitions({("Z", sym): "Z"})

        # For every live (s, sym) with 0 LIVE dst, point to Z
        for s_name in list(dfa.Q):  # snapshot; Q changes if we revive/kill
            for sym in list(dfa.Σ):
                sid = dfa._sid_of(s_name)  # type: ignore
                aid = dfa._aid_of(sym)     # type: ignore
                live = {
                    d for d in dfa._tx.delta.get(  # type: ignore
                        (sid, aid), set())
                    if not dfa.states[d].is_dead()
                }
                if not live:
                    dfa.add_transitions({(s_name, sym): "Z"})

    # should be valid again
    assert dfa.is_valid_dfa()


# ---------------------------------------------------------------------
# accepts() under DFA semantics
# ---------------------------------------------------------------------
def test_accepts_basic_language_dfa(built_dfa: DFA):
    dfa = built_dfa
    # accepts strings ending with 'a'
    assert dfa.accepts("a")
    assert dfa.accepts("ba")
    assert dfa.accepts("bba")
    assert dfa.accepts("abba")

    assert not dfa.accepts("")
    assert not dfa.accepts("b")
    assert not dfa.accepts("abb")


def test_accepts_raises_on_unknown_symbol(built_dfa: DFA):
    dfa = built_dfa
    with pytest.raises(ValueError):
        dfa.accepts("ac")
