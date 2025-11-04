# tests/test_regauto.py
# ---------------------------------------------------------------------
# Imports & type aliases
# ---------------------------------------------------------------------
import pytest
from typing import Dict, Tuple
from automata.experimental.dfa_v2 import RegAuto  # adjust path to your module

Delta = Dict[Tuple[str, str], set[str]]
DFA_Params = Tuple[set[str], set[str],
                   dict[tuple[str, str], str], str, set[str]]


# ---------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------
@pytest.fixture
def simple_dfa_spec() -> DFA_Params:
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
def built_simple_dfa(simple_dfa_spec: DFA_Params) -> RegAuto:
    Q, Sigma, delta, q0, F = simple_dfa_spec
    return RegAuto(Q, Sigma, delta, q0, F)


# ---------------------------------------------------------------------
# _Index lazy caches (via inner class)
# ---------------------------------------------------------------------
def test_index_lazy_views_build_and_refresh():
    idx = RegAuto._Index()  # type: ignore
    assert idx.out == {}
    assert idx.inn == {}
    assert idx.edges == {}

    idx.add(0, 0, 1)
    assert idx.out[0][0] == {1}
    assert idx.inn[1][0] == {0}
    assert (0, 0, 1) in idx.edges[0]

    idx.add(0, 0, 2)
    assert idx.out[0][0] == {1, 2}
    assert idx.inn[2][0] == {0}
    assert any(t == (0, 0, 2) for t in idx.edges[0])

    idx.remove(0, 0, 1)
    assert idx.out[0][0] == {2}
    assert 1 not in idx.inn

    idx.set(0, 1, (3,))
    assert idx.out[0][1] == {3}
    assert idx.inn[3][1] == {0}

    idx.set(0, 1, ())
    assert 1 not in idx.out.get(0, {})
    assert 1 not in idx.inn.get(3, {})

    idx.clear()
    assert idx.delta == {}
    assert idx.out == {}
    assert idx.inn == {}
    assert idx.edges == {}


# ---------------------------------------------------------------------
# Construction / validity
# ---------------------------------------------------------------------
def test_construct_valid_dfa(built_simple_dfa: RegAuto):
    dfa = built_simple_dfa
    assert len(dfa.states) == 2
    assert len(dfa.alphabet) == 2
    assert dfa.is_valid_dfa()
    for sid in range(len(dfa.states)):
        for aid in range(len(dfa.alphabet)):
            dsts = dfa._tx.delta.get((sid, aid))  # raw delta
            assert dsts is not None and len(dsts) == 1


def test_empty_Q_or_Sigma_is_invalid():
    with pytest.raises(ValueError):
        RegAuto(set(), {"a"}, {}, "S", set())
    with pytest.raises(ValueError):
        RegAuto({"S"}, set(), {}, "S", set())


def test_start_and_final_mapping(simple_dfa_spec: DFA_Params):
    Q, Sigma, delta, q0, F = simple_dfa_spec
    dfa = RegAuto(Q, Sigma, delta, q0, F)
    assert dfa.states[dfa.start_sid].name == "S"
    finals = {dfa.states[sid].name for sid in dfa.final_sids}
    assert finals == {"A"}


def test_invalid_when_missing_transition(simple_dfa_spec: DFA_Params):
    Q, Sigma, delta, q0, F = simple_dfa_spec
    delta = dict(delta)
    delta.pop(("A", "b"))
    with pytest.raises(ValueError):
        RegAuto(Q, Sigma, delta, q0, F)


def test_invalid_when_multiple_dsts_for_pair(simple_dfa_spec: DFA_Params):
    Q, Sigma, delta, q0, F = simple_dfa_spec
    dfa = RegAuto(Q, Sigma, delta, q0, F)
    with pytest.raises(ValueError):
        with dfa.edit():
            sid = dfa._sid_of("S")  # type: ignore
            aid = dfa._aid_of("a")  # type: ignore
            # force nondeterminism  # type: ignore
            dfa._tx.add(sid, aid, dfa._sid_of("S"))


# ---------------------------------------------------------------------
# Edit guard: adding/removing/renaming
# ---------------------------------------------------------------------
def test_edit_required_for_mutations(built_simple_dfa: RegAuto):
    dfa = built_simple_dfa
    with pytest.raises(RuntimeError):
        dfa.add_states({"X"})
    with pytest.raises(RuntimeError):
        dfa.add_letters({"c"})
    with pytest.raises(RuntimeError):
        dfa.add_transitions({("S", "a"): "S"})
    with pytest.raises(RuntimeError):
        dfa.rename_state("S", "S1")
    with pytest.raises(RuntimeError):
        dfa.rename_letter("a", "c")
    with pytest.raises(RuntimeError):
        dfa.remove_states(["A"])
    with pytest.raises(RuntimeError):
        dfa.remove_letters(["a"])


def test_rename_state_and_letter_enforce_uniqueness(built_simple_dfa: RegAuto):
    dfa = built_simple_dfa
    with dfa.edit():
        dfa.rename_state("S", "S1")
        assert "S1" in dfa.Q and "S" not in dfa.Q
        with pytest.raises(ValueError):
            dfa.rename_state("A", "S1")  # duplicate

        dfa.rename_letter("a", "c")
        assert "c" in dfa.Σ and "a" not in dfa.Σ
        with pytest.raises(ValueError):
            dfa.rename_letter("b", "c")  # duplicate


# ---------------------------------------------------------------------
# Add states/letters/transitions
# ---------------------------------------------------------------------
def test_add_state_and_letter_then_transition_inside_edit(built_simple_dfa: RegAuto):
    dfa = built_simple_dfa
    with dfa.edit():
        dfa.add_states({"Z"})
        dfa.add_letters({"c"})
        for s in ("S", "A", "Z"):
            for sym in ("a", "b", "c"):
                dst = "S" if sym == "c" else (
                    "A" if (s, sym) in {("S", "a"), ("A", "a")} else "S")
                dfa.add_transitions({(s, sym): dst})
    assert dfa.is_valid_dfa()
    assert "c" in dfa.char_to_aid
    assert "Z" in dfa.Q


def test_add_transitions_accepts_iterable_values(simple_dfa_spec: DFA_Params):
    Q, Sigma, delta, q0, F = simple_dfa_spec
    dfa = RegAuto(Q, Sigma, delta, q0, F)
    with dfa.edit():
        dfa.add_letters({"c"})
        dfa.add_states({"Z"})
        dfa.add_transitions({
            ("S", "c"): ["S"],
            ("A", "c"): ["S"],
            ("Z", "c"): ["S"],
            ("Z", "a"): ["S"],
            ("Z", "b"): ["S"],
        })
    assert dfa.is_valid_dfa()
    sid_S, sid_A, sid_Z = dfa._sid_of("S"), dfa._sid_of(  # type: ignore
        "A"), dfa._sid_of("Z")  # type: ignore
    aid_c = dfa._aid_of("c")  # type: ignore
    assert dfa._tx.delta[(sid_S, aid_c)] == {sid_S}  # type: ignore
    assert dfa._tx.delta[(sid_A, aid_c)] == {sid_S}  # type: ignore
    assert dfa._tx.delta[(sid_Z, aid_c)] == {sid_S}  # type: ignore


def test_add_transitions_multiple_dsts_makes_invalid(simple_dfa_spec: DFA_Params):
    Q, Sigma, delta, q0, F = simple_dfa_spec
    dfa = RegAuto(Q, Sigma, delta, q0, F)
    with pytest.raises(ValueError):
        with dfa.edit():
            dfa.add_transitions({("S", "a"): ["A", "S"]})


def test_remove_transitions_iterable_values(simple_dfa_spec: DFA_Params):
    Q, Sigma, delta, q0, F = simple_dfa_spec
    dfa = RegAuto(Q, Sigma, delta, q0, F)
    with pytest.raises(ValueError):
        with dfa.edit():
            dfa.add_transitions({("S", "a"): "S"})
            dfa.remove_transitions({("S", "a"): ["S"]})
            dfa.remove_transitions({("S", "b"): ["S"]})
    dfa = RegAuto(Q, Sigma, delta, q0, F)
    with dfa.edit():
        dfa.add_transitions({("S", "a"): "S"})
        dfa.remove_transitions({("S", "a"): ["S"]})
    assert dfa.is_valid_dfa()


# ---------------------------------------------------------------------
# Properties: Q, Σ, δ, q0, F
# ---------------------------------------------------------------------
def test_properties_basic(built_simple_dfa: RegAuto):
    dfa = built_simple_dfa
    assert dfa.Q == {"S", "A"}
    assert dfa.Σ == {"a", "b"}
    expected_delta = {
        ("S", "a"): {"A"},
        ("S", "b"): {"S"},
        ("A", "a"): {"A"},
        ("A", "b"): {"S"},
    }
    assert dfa.δ == expected_delta
    assert dfa.q0 == "S"
    assert dfa.F == {"A"}


# ---------------------------------------------------------------------
# Kill guards (must be inside edit), dead filtering, rewiring
# ---------------------------------------------------------------------
def test_kill_state_outside_edit_is_forbidden(built_simple_dfa: RegAuto):
    dfa = built_simple_dfa
    with pytest.raises(RuntimeError):
        dfa.get_state("A").kill()


def test_kill_letter_outside_edit_is_forbidden(built_simple_dfa: RegAuto):
    dfa = built_simple_dfa
    with pytest.raises(RuntimeError):
        dfa.get_letter("a").kill()


def test_delta_filters_dead_sources_and_letters(built_simple_dfa: RegAuto):
    dfa = built_simple_dfa
    with pytest.raises(ValueError):
        with dfa.edit():
            dfa.remove_states(["A"])
            assert ("A", "a") not in dfa.δ
            assert dfa.δ[("S", "a")] == set()
            # exit invalid (missing live dst), hence ValueError
            assert dfa.δ[("S", "b")] == {"S"}


def test_index_edges_remain_for_rollback_even_after_kill(simple_dfa_spec: DFA_Params):
    Q, Sigma, delta, q0, F = simple_dfa_spec
    dfa = RegAuto(Q, Sigma, delta, q0, F)
    sid_S = dfa._sid_of("S")  # type: ignore
    sid_A = dfa._sid_of("A")  # type: ignore
    aid_a = dfa._aid_of("a")  # type: ignore
    with pytest.raises(ValueError):
        with dfa.edit():
            dfa.remove_states(["A"])
            assert dfa._tx.delta.get((sid_S, aid_a)) == {sid_A}  # type: ignore
            assert dfa.δ.get(("S", "a")) == set()


def test_rewire_after_kill_restores_validity(simple_dfa_spec: DFA_Params):
    Q, Sigma, delta, q0, F = simple_dfa_spec
    dfa = RegAuto(Q, Sigma, delta, q0, F)
    with dfa.edit():
        dfa.remove_states(["A"])
        dfa.add_states({"Z"})
        for sym in Sigma:
            dfa.add_transitions({("Z", sym): "Z"})
        for s_name in dfa.Q:
            for sym in dfa.Σ:
                sid = dfa._sid_of(s_name)  # type: ignore
                aid = dfa._aid_of(sym)     # type: ignore
                live = {d for d in dfa._tx.delta.get(  # type: ignore
                    (sid, aid), set()) if not dfa.states[d].is_dead()}
                if not live:
                    dfa.add_transitions({(s_name, sym): "Z"})
    assert dfa.is_valid_dfa()
    sid_S = dfa._sid_of("S")  # type: ignore
    aid_a = dfa._aid_of("a")  # type: ignore
    sid_Z = dfa._sid_of("Z")  # type: ignore
    live_dsts = {d for d in dfa._tx.delta[(  # type: ignore
        sid_S, aid_a)] if not dfa.states[d].is_dead()}
    assert live_dsts == {sid_Z}


# ---------------------------------------------------------------------
# transition() and accepts()
# ---------------------------------------------------------------------
def test_transition_live_ids_basic(simple_dfa_spec: DFA_Params):
    Q, Sigma, delta, q0, F = simple_dfa_spec
    dfa = RegAuto(Q, Sigma, delta, q0, F)
    sid_S, sid_A = dfa._sid_of("S"), dfa._sid_of("A")  # type: ignore
    aid_a, aid_b = dfa._aid_of("a"), dfa._aid_of("b")  # type: ignore
    assert dfa.transition(sid_S, aid_a) == {sid_A}
    assert dfa.transition(sid_S, aid_b) == {sid_S}
    assert dfa.transition(sid_A, aid_b) == {sid_S}


def test_transition_throws_on_dead_state_or_letter_when_flag_true(simple_dfa_spec: DFA_Params):
    Q, Sigma, delta, q0, F = simple_dfa_spec
    dfa = RegAuto(Q, Sigma, delta, q0, F)
    sid_S, sid_A = dfa._sid_of("S"), dfa._sid_of("A")  # type: ignore
    aid_a = dfa._aid_of("a")  # type: ignore
    with pytest.raises(ValueError):
        with dfa.edit():
            dfa.remove_states(["A"])
            _ = dfa.transition(sid_A, aid_a, throw_on_dead=True)
    with pytest.raises(ValueError):
        with dfa.edit():
            dfa.remove_letters(["a"])
            _ = dfa.transition(sid_S, aid_a, throw_on_dead=True)


def test_transition_no_throw_on_dead_letter_returns_filtered_dsts(simple_dfa_spec: DFA_Params):
    Q, Sigma, delta, q0, F = simple_dfa_spec
    dfa = RegAuto(Q, Sigma, delta, q0, F)
    sid_S, sid_A = dfa._sid_of("S"), dfa._sid_of("A")  # type: ignore
    aid_a = dfa._aid_of("a")  # type: ignore
    with dfa.edit():
        dfa.remove_letters(["a"])
        assert dfa.transition(sid_S, aid_a, throw_on_dead=False) == {sid_A}


def test_accepts_basic_language(simple_dfa_spec: DFA_Params):
    Q, Sigma, delta, q0, F = simple_dfa_spec
    dfa = RegAuto(Q, Sigma, delta, q0, F)
    assert dfa.accepts("a")
    assert dfa.accepts("ba")
    assert dfa.accepts("bba")
    assert dfa.accepts("abba")
    assert not dfa.accepts("")
    assert not dfa.accepts("b")
    assert not dfa.accepts("abb")


def test_accepts_raises_on_unknown_symbol(built_simple_dfa: RegAuto):
    dfa = built_simple_dfa
    with pytest.raises(ValueError):
        dfa.accepts("ac")


def test_accepts_after_kill_and_rewire(simple_dfa_spec: DFA_Params):
    Q, Sigma, delta, q0, F = simple_dfa_spec
    dfa = RegAuto(Q, Sigma, delta, q0, F)
    with dfa.edit():
        dfa.remove_states(["A"])
        dfa.add_states({"Z"})
        for sym in Sigma:
            dfa.add_transitions({("Z", sym): "Z"})
        for s_name in dfa.Q:
            for sym in dfa.Σ:
                sid = dfa._sid_of(s_name)  # type: ignore
                aid = dfa._aid_of(sym)     # type: ignore
                live = {d for d in dfa._tx.delta.get(  # type: ignore
                    (sid, aid), set()) if not dfa.states[d].is_dead()}
                if not live:
                    dfa.add_transitions({(s_name, sym): "Z"})
    assert dfa.is_valid_dfa()
    assert not dfa.accepts("a")
    assert not dfa.accepts("ba")
    assert not dfa.accepts("bbb")
