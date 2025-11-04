# tests/experimental/test_nfa.py
import pytest
from typing import Dict, Iterable, Tuple

from automata.experimental.nfa import NFA

NFA_Delta = Dict[Tuple[str, str], Iterable[str] | str]
NFA_Params = Tuple[set[str], set[str],
                   NFA_Delta, str, set[str]]


@pytest.fixture
def simple_nfa_spec() -> NFA_Params:
    """
    NFA that accepts strings ending with 'a' and also allows an ε jump
    from S to A (so empty string is rejected, 'a' accepted, 'ba' accepted).
    """
    Q = {"S", "A"}
    Sigma = {"a", "b"}  # user Σ excludes ε; ε will be added internally
    delta: NFA_Delta = {
        ("S", "a"): "A",
        ("S", "b"): "S",
        ("A", "a"): "A",
        ("A", "b"): "S",
        # ε edge S -> S (harmless) and S -> A to illustrate ε usage
        ("S", "ε"): ("S", "A"),
    }
    q0 = "S"
    F = {"A"}
    return Q, Sigma, delta, q0, F


@pytest.fixture
def built_nfa(simple_nfa_spec: NFA_Params) -> NFA:
    Q, Sigma, delta, q0, F = simple_nfa_spec
    return NFA(Q, Sigma, delta, q0, F)


# --- Epsilon basics ---------------------------------------------------
def test_epsilon_is_reserved_and_hidden_from_Sigma(built_nfa: NFA):
    nfa = built_nfa
    # Σ should exclude ε
    assert "ε" not in nfa.Σ
    # but ε transitions exist in δ / index
    assert any(sym == "ε" for (_, sym) in nfa.δ.keys())

    # cannot remove or rename ε
    with pytest.raises(RuntimeError):
        with nfa.edit():
            nfa.remove_letters(["ε"])
    with pytest.raises(RuntimeError):
        with nfa.edit():
            nfa.rename_letter("ε", "e")


# --- Accepts semantics with ε-closure --------------------------------
def test_accepts_with_epsilon_closure(built_nfa: NFA):
    nfa = built_nfa
    # S --ε--> A means even from start, closure includes A
    assert nfa.accepts("a")
    assert nfa.accepts("ba")
    assert nfa.accepts("")
    assert nfa.accepts("b")
    assert nfa.accepts("abb")


def test_accepts_raises_on_unknown_symbol(built_nfa: NFA):
    nfa = built_nfa
    with pytest.raises(ValueError):
        nfa.accepts("ac")  # 'c' not in Σ


# --- Transition semantics ---------------------------------------------
def test_transition_uses_closure_for_non_epsilon(built_nfa: NFA):
    nfa = built_nfa
    sid_S = nfa._sid_of("S")  # type: ignore
    aid_a = nfa._aid_of("a")  # type: ignore

    # From ε-closure(S) = {S,A} on 'a' we should land in closure({A}) = {A} (since A --ε--> ? none)
    dsts = nfa.transition(sid_S, aid_a)
    names = {nfa.states[s].name for s in dsts}
    assert names == {"A"}


def test_raw_epsilon_transition_still_callable(built_nfa: NFA):
    nfa = built_nfa
    sid_S = nfa._sid_of("S")  # type: ignore
    aid_eps = nfa._aid_of("ε")  # type: ignore

    # Calling transition with ε directly behaves like base: returns ε-moves
    dsts = nfa.transition(sid_S, aid_eps)
    names = {nfa.states[s].name for s in dsts}
    assert names >= {"S", "A"}  # at least the two we added


# --- Edit validation ---------------------------------------------------
def test_killing_epsilon_is_forbidden_and_would_raise(built_nfa: NFA):
    nfa = built_nfa
    with pytest.raises(ValueError):
        with nfa.edit():
            # Try to sneak-kill ε through the internal letter object
            eps = nfa.get_letter("ε")
            eps.kill()  # forbidden by validation on exit (epsilon must remain live)

# ------------------------------------------------------------
# ε drives acceptance only after reading something (nontrivial)
# ------------------------------------------------------------


def test_epsilon_enables_accept_after_symbol():
    # Language: exactly "a" via X --ε--> F (empty string should reject)
    Q = {"S", "X", "F"}
    Sigma = {"a", "b"}
    delta: NFA_Delta = {
        ("S", "a"): "X",      # read 'a' to X
        ("X", "ε"): "F",      # ε-jump to final F
        # (no other edges)
    }
    q0 = "S"
    F = {"F"}
    nfa = NFA(Q, Sigma, delta, q0, F)

    assert nfa.accepts("a")      # uses ε from X -> F
    assert not nfa.accepts("")   # ε-closure(start) has no final
    assert not nfa.accepts("aa")
    assert not nfa.accepts("b")


# ------------------------------------------------------------
# ε used mid-string to bridge sub-automata (regex: "ab")
# ------------------------------------------------------------
def test_epsilon_midstring_concat():
    # Build NFA for "ab" where the jump from M to N is ε (S -a-> M -ε-> N -b-> F)

    Q = {"S", "M", "N", "F"}
    Sigma = {"a", "b"}
    delta: NFA_Delta = {
        ("S", "a"): "M",
        ("M", "ε"): "N",   # ε bridge between sub-automata
        ("N", "b"): "F",
    }
    q0 = "S"
    F = {"F"}
    nfa = NFA(Q, Sigma, delta, q0, F)

    assert nfa.accepts("ab")
    assert not nfa.accepts("")     # needs 'a' then ε then 'b'
    assert not nfa.accepts("a")    # stuck at N; must read 'b'
    assert not nfa.accepts("b")    # no path from start on 'b'
    assert not nfa.accepts("aba")  # extra symbol breaks


# ------------------------------------------------------------
# ε used to fork alternatives (regex: a* ∪ b)
# ------------------------------------------------------------
def test_epsilon_branch_union():
    # Two branches:
    #  - Branch A: S --ε--> A, A --a--> A, A final  (a*)
    #  - Branch B: S --b--> F (single 'b')

    Q = {"S", "A", "F"}
    Sigma = {"a", "b"}
    delta: NFA_Delta = {
        ("S", "ε"): "A",   # fork to a* branch
        ("A", "a"): "A",
        ("S", "b"): "F",
    }
    q0 = "S"
    F = {"A", "F"}         # accept a* or single b
    nfa = NFA(Q, Sigma, delta, q0, F)

    # a* accepted via ε→A then zero or more 'a'
    assert nfa.accepts("")
    assert nfa.accepts("a")
    assert nfa.accepts("aaa")

    # also accept a single 'b' via the other branch
    assert nfa.accepts("b")

    # but not 'bb' (only single b supported)
    assert not nfa.accepts("bb")
