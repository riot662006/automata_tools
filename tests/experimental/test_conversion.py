import pytest
from typing import Dict, Tuple

from automata.experimental.dfa import DFA
from automata.experimental.nfa import NFA

DFA_Params = Tuple[set[str], set[str],
                   dict[tuple[str, str], str], str, set[str]]


# --- Fixtures ----------------------------------------------------------


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
def built_dfa(simple_dfa_spec: DFA_Params) -> DFA:
    Q, Sigma, delta, q0, F = simple_dfa_spec
    return DFA(Q, Sigma, delta, q0, F)


@pytest.fixture
def nfa_from_dfa(built_dfa: DFA) -> NFA:
    return NFA.from_dfa(built_dfa)


# --- NFA.from_dfa: structural properties -------------------------------


def test_from_dfa_copies_basic_structure(built_dfa: DFA, nfa_from_dfa: NFA):
    dfa = built_dfa
    nfa = nfa_from_dfa

    # same state names, same start, same finals
    assert nfa.Q == dfa.Q
    assert nfa.q0 == dfa.q0
    assert nfa.F == dfa.F

    # alphabet in NFA excludes ε but otherwise matches DFA
    assert nfa.Σ == dfa.Σ
    # epsilon must exist as a letter in NFA but not be visible in Σ
    assert "ε" not in nfa.Σ
    assert any(letter.char == "ε" for letter in nfa.alphabet)

    # transition table on visible symbols matches DFA's (ignoring that NFA.δ uses sets)
    expected_delta = {k: set(v) for k, v in dfa.δ.items()}
    assert {
        (src, sym): dsts
        for (src, sym), dsts in nfa.δ.items()
        if sym != "ε"
    } == expected_delta


def test_from_dfa_has_no_epsilon_transitions_initially(nfa_from_dfa: NFA):
    nfa = nfa_from_dfa
    # There should be no epsilon edges created by from_dfa itself
    assert all(sym != "ε" for (_, sym) in nfa.δ.keys())


# --- NFA.from_dfa: language equivalence --------------------------------


def test_from_dfa_language_equivalence_on_examples(built_dfa: DFA, nfa_from_dfa: NFA):
    dfa = built_dfa
    nfa = nfa_from_dfa

    # some strings accepted by both (ending with 'a')
    for w in ("a", "ba", "bba", "abba"):
        assert dfa.accepts(w)
        assert nfa.accepts(w)

    # some strings rejected by both
    for w in ("", "b", "abb", "bbb"):
        assert not dfa.accepts(w)
        assert not nfa.accepts(w)


# --- NFA.from_dfa: independence & mutability ---------------------------


def test_from_dfa_is_independent_of_original(built_dfa: DFA, nfa_from_dfa: NFA):
    dfa = built_dfa
    nfa = nfa_from_dfa

    # mutate NFA structure inside edit; DFA should be unchanged
    with nfa.edit():
        nfa.remove_states(["A"])
        nfa.add_states({"Z"})
        for sym in nfa.Σ:
            nfa.add_transitions({("Z", sym): "Z"})

    # DFA still behaves like the original language
    assert dfa.accepts("a")
    assert dfa.accepts("ba")
    assert not dfa.accepts("bb")

    # NFA may have different language now (we don't constrain it here),
    # but the important property is no crash & no shared mutable state.


# --- NFA.from_dfa: accepts uses epsilon-free path when no ε-edges -----


def test_from_dfa_uses_trivial_epsilon_closure(nfa_from_dfa: NFA):
    nfa = nfa_from_dfa

    # with no ε-edges, ε-closure({s}) should be just {s},
    # so transition semantics reduce to the DFA case.
    sid_S = nfa._sid_of("S")  # type: ignore
    aid_a = nfa._aid_of("a")  # type: ignore

    # From S on 'a' should go only to A
    dsts = nfa.transition(sid_S, aid_a)
    names = {nfa.states[sid].name for sid in dsts}
    assert names == {"A"}
