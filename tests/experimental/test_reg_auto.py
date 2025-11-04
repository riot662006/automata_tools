# tests/experimental/test_reg_auto.py
# ---------------------------------------------------------------------
# Imports & type aliases
# ---------------------------------------------------------------------
import pytest
from typing import Dict, Tuple

# adjust this import to your project path
from automata.experimental.reg_auto import RegAuto

Delta = Dict[Tuple[str, str], set[str]]
AutoParams = Tuple[set[str], set[str], dict[tuple[str, str], str], str, set[str]]


# ---------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------
@pytest.fixture
def simple_auto_spec() -> AutoParams:
    """
    A small automaton over {'a','b'} with states {S, A}.
    Transitions (deterministic), start=S, finals={A}.
    NOTE: RegAuto itself does not validate DFA invariants on edit exit;
    DFA (subclass) will. We still use a deterministic spec here.
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
def built_reg_auto(simple_auto_spec: AutoParams) -> RegAuto:
    Q, Sigma, delta, q0, F = simple_auto_spec
    return RegAuto(Q, Sigma, delta, q0, F)


# ---------------------------------------------------------------------
# _Index lazy caches (via inner class)
# ---------------------------------------------------------------------
def test_index_lazy_views_build_and_refresh():
    idx = RegAuto._Index() # type: ignore
    # empty caches build lazily
    assert idx.out == {}
    assert idx.inn == {}
    assert idx.edges == {}

    # add edges and see caches reflect
    idx.add(0, 0, 1)
    assert idx.out[0][0] == {1}
    assert idx.inn[1][0] == {0}
    assert (0, 0, 1) in idx.edges[0]

    # add another destination
    idx.add(0, 0, 2)
    assert idx.out[0][0] == {1, 2}
    assert idx.inn[2][0] == {0}
    assert any(t == (0, 0, 2) for t in idx.edges[0])

    # remove one edge
    idx.remove(0, 0, 1)
    assert idx.out[0][0] == {2}
    assert 1 not in idx.inn

    # replace (set) edges for a different symbol
    idx.set(0, 1, (3,))
    assert idx.out[0][1] == {3}
    assert idx.inn[3][1] == {0}

    # set empty -> key removed
    idx.set(0, 1, ())
    assert 1 not in idx.out.get(0, {})
    assert 1 not in idx.inn.get(3, {})

    # clear all
    idx.clear()
    assert idx.delta == {}
    assert idx.out == {}
    assert idx.inn == {}
    assert idx.edges == {}


# ---------------------------------------------------------------------
# Construction & basic properties (no DFA validity enforcement here)
# ---------------------------------------------------------------------
def test_construct_reg_auto_and_properties(built_reg_auto: RegAuto):
    a = built_reg_auto
    assert a.Q == {"S", "A"}
    assert a.Σ == {"a", "b"}

    expected_delta = {
        ("S", "a"): {"A"},
        ("S", "b"): {"S"},
        ("A", "a"): {"A"},
        ("A", "b"): {"S"},
    }
    assert a.δ == expected_delta
    assert a.q0 == "S"
    assert a.F == {"A"}


# ---------------------------------------------------------------------
# Edit-guarded mutations + rename uniqueness
# ---------------------------------------------------------------------
def test_edit_required_for_mutations(built_reg_auto: RegAuto):
    a = built_reg_auto
    with pytest.raises(RuntimeError):
        a.add_states({"X"})
    with pytest.raises(RuntimeError):
        a.add_letters({"c"})
    with pytest.raises(RuntimeError):
        a.add_transitions({("S", "a"): "S"})
    with pytest.raises(RuntimeError):
        a.remove_states(["A"])
    with pytest.raises(RuntimeError):
        a.remove_letters(["a"])
    with pytest.raises(RuntimeError):
        a.rename_state("S", "S1")
    with pytest.raises(RuntimeError):
        a.rename_letter("a", "c")


def test_rename_state_and_letter_uniqueness(built_reg_auto: RegAuto):
    a = built_reg_auto
    with a.edit():
        a.rename_state("S", "S1")
        assert "S1" in a.Q and "S" not in a.Q
        with pytest.raises(ValueError):
            a.rename_state("A", "S1")

        a.rename_letter("a", "c")
        assert "c" in a.Σ and "a" not in a.Σ
        with pytest.raises(ValueError):
            a.rename_letter("b", "c")


# ---------------------------------------------------------------------
# Kill guards (must be inside edit), dead filtering, transitions
# ---------------------------------------------------------------------
def test_kill_state_and_letter_outside_edit_forbidden(built_reg_auto: RegAuto):
    a = built_reg_auto
    with pytest.raises(RuntimeError):
        a.get_state("A").kill()
    with pytest.raises(RuntimeError):
        a.get_letter("a").kill()


def test_delta_filters_dead_states_and_letters(built_reg_auto: RegAuto):
    a = built_reg_auto
    with a.edit():
        a.remove_states(["A"])
        a.remove_letters(["a"])
        # dead sources & letters omitted; dead destinations filtered
        assert ("A", "a") not in a.δ
        assert ("A", "b") not in a.δ
        assert ("S", "a") not in a.δ  # letter 'a' is dead
        assert a.δ == {("S", "b"): {"S"}}


def test_add_remove_transitions_bucketed(built_reg_auto: RegAuto):
    a = built_reg_auto
    with a.edit():
        a.add_letters({"c"})
        a.add_states({"Z"})
        a.add_transitions({
            ("Z", "a"): "S",
            ("Z", "b"): "S",
            ("Z", "c"): "Z",
            ("S", "c"): "S",
            ("A", "c"): "S",
        })
        # and remove one
        a.remove_transitions({("Z", "a"): "S"})

    sid_Z, aid_c = a._sid_of("Z"), a._aid_of("c")  # type: ignore
    # Z --c--> Z should remain
    assert a._tx.delta[(sid_Z, aid_c)] == {sid_Z}  # type: ignore


# ---------------------------------------------------------------------
# transition() (ID-based) and accepts() (NFA-like union)
# ---------------------------------------------------------------------
def test_transition_id_based(built_reg_auto: RegAuto):
    a = built_reg_auto
    sid_S, sid_A = a._sid_of("S"), a._sid_of("A")  # type: ignore
    aid_a, aid_b = a._aid_of("a"), a._aid_of("b")  # type: ignore
    assert a.transition(sid_S, aid_a) == {sid_A}
    assert a.transition(sid_S, aid_b) == {sid_S}
    assert a.transition(sid_A, aid_b) == {sid_S}


def test_transition_throw_on_dead_flags(built_reg_auto: RegAuto):
    a = built_reg_auto
    sid_S, sid_A = a._sid_of("S"), a._sid_of("A")  # type: ignore
    aid_a = a._aid_of("a")  # type: ignore

    with a.edit():
        a.remove_states(["A"])
        # no throw -> filtered, returns empty set (dst was A, now dead)
        assert a.transition(sid_S, aid_a, throw_on_dead=False) == set()

    with a.edit():
        a.remove_letters(["a"])
        # throw_on_dead -> letter dead => ValueError
        with pytest.raises(ValueError):
            a.transition(sid_S, aid_a, throw_on_dead=True)


def test_accepts_basic_language_reg_auto(built_reg_auto: RegAuto):
    a = built_reg_auto
    # language: strings ending with 'a' (since finals={A})
    assert a.accepts("a")
    assert a.accepts("ba")
    assert a.accepts("bba")
    assert a.accepts("abba")

    assert not a.accepts("")
    assert not a.accepts("b")
    assert not a.accepts("abb")


def test_accepts_unknown_symbol_raises(built_reg_auto: RegAuto):
    a = built_reg_auto
    with pytest.raises(ValueError):
        a.accepts("ac")  # 'c' not in Σ

    with a.edit():
        a.remove_letters(["a"])
    with pytest.raises(ValueError):
        a.accepts("a")
