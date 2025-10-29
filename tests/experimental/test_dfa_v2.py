# tests/test_dfav2.py
import pytest

from typing import Dict, Tuple

from automata.experimental.dfa_v2 import DFAV2, _Index # type: ignore

DFA_Params = Tuple[set[str], set[str], dict[tuple[str, str], str], str, set[str]]
# --- Fixtures ---

@pytest.fixture
def simple_dfa_spec() -> DFA_Params:
    """
    DFA over {'a','b'} with states {S, A} that recognizes strings ending with 'a'.
    Transition table:
      S --a--> A, S --b--> S
      A --a--> A, A --b--> S
    start=S, finals={A}
    """
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
def built_simple_dfa(simple_dfa_spec: DFA_Params) -> DFAV2:
    Q, Sigma, delta, q0, F = simple_dfa_spec
    return DFAV2(Q, Sigma, delta, q0, F)


# --- _Index tests ---

def test_index_add_remove_consistency():
    idx = _Index()
    # ids: s0=0, s1=1 ; a=0
    idx.add(0, 0, 1)
    assert idx.delta[(0, 0)] == {1}
    assert idx.out[0][0] == {1}
    assert idx.inn[1][0] == {0}

    # remove edge
    idx.remove(0, 0, 1)
    assert (0, 0) not in idx.delta
    assert 0 not in idx.out or 0 not in idx.out.get(0, {})
    assert 1 not in idx.inn or 0 not in idx.inn.get(1, {})

def test_index_set_overwrites_prior_edges():
    idx = _Index()
    idx.add(0, 0, 1)
    idx.add(0, 0, 2)
    # Now replace with single destination {3}
    idx.set(0, 0, (3,))
    assert idx.delta[(0, 0)] == {3}
    assert idx.out[0][0] == {3}
    assert idx.inn[3][0] == {0}
    # ensure old inn entries were cleaned
    assert 1 not in idx.inn
    assert 2 not in idx.inn


# --- DFAV2 construction / validity ---

def test_construct_valid_dfa(built_simple_dfa: DFAV2):
    dfa = built_simple_dfa
    # sanity
    assert len(dfa.states) == 2
    assert len(dfa.alphabet) == 2
    assert dfa.is_valid_dfa()
    # each (state, symbol) has exactly one dst
    for sid in range(len(dfa.states)):
        for aid in range(len(dfa.alphabet)):
            dsts = dfa.tx.delta.get((sid, aid))
            assert dsts is not None and len(dsts) == 1

def test_edit_required_for_mutations(built_simple_dfa: DFAV2):
    dfa = built_simple_dfa
    with pytest.raises(RuntimeError):
        dfa._add_states({"X"}) # type: ignore
    with pytest.raises(RuntimeError):
        dfa._add_letters({"c"}) # type: ignore
    with pytest.raises(RuntimeError):
        dfa._add_transitions({("S", "a"): "S"})  # type: ignore # would replace, but outside edit

def test_add_state_and_letter_then_transition_inside_edit(built_simple_dfa: DFAV2):
    dfa = built_simple_dfa
    with dfa.edit():
        dfa._add_states({"Z"}) # type: ignore
        dfa._add_letters({"c"}) # type: ignore
        # Make it total by wiring Z on all symbols including new 'c'
        # For existing states, we must also add transitions for 'c'
        for s in ("S", "A", "Z"):
            for sym in ("a", "b", "c"):
                # send everything on 'c' to S to keep it deterministic
                dst = "S" if sym == "c" else (
                    "A" if (s, sym) in {("S", "a"), ("A", "a")} else "S"
                )
                dfa._add_transitions({(s, sym): dst}) # type: ignore

    assert dfa.is_valid_dfa()
    # New letter 'c' must appear in alphabet
    assert "c" in dfa.char_to_aid
    # New state 'Z' must be alive
    assert not dfa._get_state("Z").is_dead() # type: ignore

def test_invalid_when_missing_transition(simple_dfa_spec: DFA_Params):
    Q, Sigma, delta, q0, F = simple_dfa_spec
    # drop one transition -> invalid
    delta.pop(("A", "b"))
    with pytest.raises(ValueError):
        DFAV2(Q, Sigma, delta, q0, F)

def test_invalid_when_multiple_dsts_for_pair(simple_dfa_spec: DFA_Params):
    Q, Sigma, delta, q0, F = simple_dfa_spec
    # Build valid DFA then try to add a second destination for ("S","a")
    dfa = DFAV2(Q, Sigma, delta, q0, F)
    with pytest.raises(ValueError):
        with dfa.edit():
            # emulate an NFA-like second edge: we do it by calling _Index.add directly via transitions
            # but _add_transitions uses .set() so to trigger invalidity we first make it valid
            # then add a conflicting edge explicitly by calling the index (simulate a faulty caller)
            sid = dfa._sid_of("S") # type: ignore
            aid = dfa._aid_of("a") # type: ignore
            # sneaky low-level add; your public API prevents this, but test the invariant anyway
            dfa.tx.add(sid, aid, dfa._sid_of("S")) # type: ignore

def test_empty_Q_or_Sigma_is_invalid():
    with pytest.raises(ValueError):
        DFAV2(set(), {"a"}, {}, "S", set())
    with pytest.raises(ValueError):
        DFAV2({"S"}, set(), {}, "S", set())

def test_start_and_final_mapping(simple_dfa_spec: DFA_Params):
    Q, Sigma, delta, q0, F = simple_dfa_spec
    dfa = DFAV2(Q, Sigma, delta, q0, F)
    assert dfa.states[dfa.start_sid].name == "S"
    finals = {dfa.states[sid].name for sid in dfa.final_sids}
    assert finals == {"A"}
