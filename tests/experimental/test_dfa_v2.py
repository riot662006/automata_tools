# tests/test_dfav2.py
import pytest

from typing import Dict, Tuple

from automata.experimental.dfa_v2 import DFAV2, _Index  # type: ignore

Delta = Dict[Tuple[str, str], set[str]]
DFA_Params = Tuple[set[str], set[str],
                   dict[tuple[str, str], str], str, set[str]]
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
        dfa._add_states({"X"})  # type: ignore
    with pytest.raises(RuntimeError):
        dfa._add_letters({"c"})  # type: ignore
    with pytest.raises(RuntimeError):
        # type: ignore # would replace, but outside edit
        dfa._add_transitions({("S", "a"): "S"})  # type: ignore


def test_add_state_and_letter_then_transition_inside_edit(built_simple_dfa: DFAV2):
    dfa = built_simple_dfa
    with dfa.edit():
        dfa._add_states({"Z"})  # type: ignore
        dfa._add_letters({"c"})  # type: ignore
        # Make it total by wiring Z on all symbols including new 'c'
        # For existing states, we must also add transitions for 'c'
        for s in ("S", "A", "Z"):
            for sym in ("a", "b", "c"):
                # send everything on 'c' to S to keep it deterministic
                dst = "S" if sym == "c" else (
                    "A" if (s, sym) in {("S", "a"), ("A", "a")} else "S"
                )
                dfa._add_transitions({(s, sym): dst})  # type: ignore

    assert dfa.is_valid_dfa()
    # New letter 'c' must appear in alphabet
    assert "c" in dfa.char_to_aid
    # New state 'Z' must be alive
    assert not dfa._get_state("Z").is_dead()  # type: ignore


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
            sid = dfa._sid_of("S")  # type: ignore
            aid = dfa._aid_of("a")  # type: ignore
            # sneaky low-level add; your public API prevents this, but test the invariant anyway
            dfa.tx.add(sid, aid, dfa._sid_of("S"))  # type: ignore


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

# --- Property tests: Q, Σ, δ, q0, F ---


def test_properties_basic(built_simple_dfa: DFAV2):
    dfa = built_simple_dfa

    # Q: all non-dead state names
    assert isinstance(dfa.Q, set)
    assert dfa.Q == {"S", "A"}

    # Σ: all letter chars (letters are never "dead" in current design)
    assert isinstance(dfa.Σ, set)
    assert dfa.Σ == {"a", "b"}

    # δ: dict[(src_name, sym_char)] -> set[dst_names] (exclude dead src/dst)
    assert isinstance(dfa.δ, dict)
    # Build an expected δ with sets of names
    expected_delta = {
        ("S", "a"): {"A"},
        ("S", "b"): {"S"},
        ("A", "a"): {"A"},
        ("A", "b"): {"S"},
    }
    assert dfa.δ == expected_delta

    # q0: start state name
    assert isinstance(dfa.q0, str)
    assert dfa.q0 == "S"

    # F: finals set of names (non-dead only)
    assert isinstance(dfa.F, set)
    assert dfa.F == {"A"}


def test_properties_after_killing_nonfinal_state(simple_dfa_spec: DFA_Params):
    _, _, delta, _, _ = simple_dfa_spec

    # Kill A (final) in a separate test below; here kill a non-final for contrast.
    # First build a DFA where S is final and A is not final so we can kill A.
    Q2, Sigma2, delta2, q02, F2 = {"S", "A"}, {
        "a", "b"}, dict(delta), "S", {"S"}
    dfa2 = DFAV2(Q2, Sigma2, delta2, q02, F2)

    # Mark A as dead (no edit() required; kill only flips metadata)
    dfa2._get_state("A").kill()  # type: ignore

    # Q excludes the dead state
    assert dfa2.Q == {"S"}

    # Σ unchanged
    assert dfa2.Σ == {"a", "b"}

    # δ: pairs with dead source are omitted; dead destinations are filtered out
    # ("A", *) should not appear at all; ("S","a") used to go to "A", now empty set
    expected_delta: dict[tuple[str, str], set[str]] = {
        ("S", "a"): set(),     # A is dead, so destination filtered out
        ("S", "b"): {"S"},
    }
    assert dfa2.δ == expected_delta

    # F excludes dead states (A wasn't final here anyway)
    assert dfa2.F == {"S"}


def test_properties_after_killing_final_state(built_simple_dfa: DFAV2):
    dfa = built_simple_dfa

    # Kill A (which is final in the base fixture)
    dfa._get_state("A").kill()  # type: ignore

    # Q now excludes A
    assert dfa.Q == {"S"}

    # F now excludes A -> becomes empty
    assert dfa.F == set()

    # δ: entries with source A gone; destinations that were A are removed
    expected_delta: Delta = {
        ("S", "a"): set(),  # used to be {"A"}, but A is dead
        ("S", "b"): {"S"},
    }
    assert dfa.δ == expected_delta


def test_q0_name_even_if_start_state_is_killed(built_simple_dfa: DFAV2):
    dfa = built_simple_dfa
    # Kill the start state "S"
    dfa._get_state("S").kill()  # type: ignore

    # q0 still reports the original start state's *name*
    assert dfa.q0 == "S"

    # But Q excludes the dead start state
    assert "S" not in dfa.Q
    # δ will exclude any pairs with dead source "S"
    # Only pairs from "A" remain (since A is alive here)
    expected_keys = {("A", "a"), ("A", "b")}
    assert set(dfa.δ.keys()) == expected_keys


@pytest.mark.parametrize(
    "kill_state, expected_Q, expected_F",
    [
        # kill start (non-final) -> finals unaffected here
        pytest.param("S", {"A"}, {"A"}, id="kill_start"),
        # kill final -> finals drop A
        pytest.param("A", {"S"}, set[str](), id="kill_final"),
    ],
)
def test_Q_and_F_type_and_semantics_under_kill(built_simple_dfa: DFAV2, kill_state: str, expected_Q: set[str], expected_F: set[str]):
    dfa = built_simple_dfa
    dfa._get_state(kill_state).kill()  # type: ignore

    # Types
    assert isinstance(dfa.Q, set)
    assert isinstance(dfa.F, set)

    # Values
    assert dfa.Q == expected_Q
    assert dfa.F == expected_F


def test_δ_types_and_keyspace(built_simple_dfa: DFAV2):
    dfa = built_simple_dfa
    d = dfa.δ
    # dict[(str,str)] -> set[str]
    assert all(isinstance(k, tuple) and len(k) == 2 and isinstance(
        k[0], str) and isinstance(k[1], str) for k in d.keys())
    assert all(isinstance(v, set) and all(isinstance(x, str)
               for x in v) for v in d.values())

    # All keys correspond to live sources and defined letters
    live_sources = dfa.Q
    letters = dfa.Σ
    assert all(k[0] in live_sources and k[1] in letters for k in d.keys())
