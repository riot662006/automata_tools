# tests/test_dfav2.py
# ---------------------------------------------------------------------
# Imports & type aliases
# ---------------------------------------------------------------------
import pytest
from typing import Dict, Tuple

from automata.experimental.dfa_v2 import DFAV2, _Index  # type: ignore

Delta = Dict[Tuple[str, str], set[str]]
DFA_Params = Tuple[set[str], set[str],
                   dict[tuple[str, str], str], str, set[str]]


# ---------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------
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


# ---------------------------------------------------------------------
# _Index tests
# ---------------------------------------------------------------------
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


# ---------------------------------------------------------------------
# DFAV2 construction / validity
# ---------------------------------------------------------------------
def test_construct_valid_dfa(built_simple_dfa: DFAV2):
    dfa = built_simple_dfa
    # sanity
    assert len(dfa.states) == 2
    assert len(dfa.alphabet) == 2
    assert dfa.is_valid_dfa()
    # each (state, symbol) has exactly one dst in the raw index
    for sid in range(len(dfa.states)):
        for aid in range(len(dfa.alphabet)):
            dsts = dfa._tx.delta.get((sid, aid))  # type: ignore
            assert dsts is not None and len(dsts) == 1


def test_edit_required_for_mutations(built_simple_dfa: DFAV2):
    dfa = built_simple_dfa
    with pytest.raises(RuntimeError):
        dfa.add_states({"X"})
    with pytest.raises(RuntimeError):
        dfa.add_letters({"c"})
    with pytest.raises(RuntimeError):
        dfa.add_transitions({("S", "a"): "S"})


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


def test_invalid_when_missing_transition(simple_dfa_spec: DFA_Params):
    Q, Sigma, delta, q0, F = simple_dfa_spec
    # drop one transition -> invalid
    delta = dict(delta)
    delta.pop(("A", "b"))
    with pytest.raises(ValueError):
        DFAV2(Q, Sigma, delta, q0, F)


def test_invalid_when_multiple_dsts_for_pair(simple_dfa_spec: DFA_Params):
    Q, Sigma, delta, q0, F = simple_dfa_spec
    dfa = DFAV2(Q, Sigma, delta, q0, F)
    with pytest.raises(ValueError):
        with dfa.edit():
            # Force nondeterminism by hacking the internal index
            sid = dfa._sid_of("S")  # type: ignore
            aid = dfa._aid_of("a")  # type: ignore
            dfa._tx.add(sid, aid, dfa._sid_of("S"))  # type: ignore


# ---------------------------------------------------------------------
# DFAV2 mutations (add states/letters/transitions)
# ---------------------------------------------------------------------
def test_add_state_and_letter_then_transition_inside_edit(built_simple_dfa: DFAV2):
    dfa = built_simple_dfa
    with dfa.edit():
        dfa.add_states({"Z"})
        dfa.add_letters({"c"})
        # Make it total by wiring Z on all symbols including new 'c'
        for s in ("S", "A", "Z"):
            for sym in ("a", "b", "c"):
                # send everything on 'c' to S to keep it deterministic
                dst = "S" if sym == "c" else (
                    "A" if (s, sym) in {("S", "a"), ("A", "a")} else "S"
                )
                dfa.add_transitions({(s, sym): dst})

    assert dfa.is_valid_dfa()
    # New letter 'c' must appear in alphabet
    assert "c" in dfa.char_to_aid
    # New state 'Z' must be alive
    assert not dfa.get_state("Z").is_dead()


def test_add_transitions_accepts_iterable_values(simple_dfa_spec: DFA_Params):
    Q, Sigma, delta, q0, F = simple_dfa_spec
    dfa = DFAV2(Q, Sigma, delta, q0, F)

    with dfa.edit():
        dfa.add_letters({"c"})
        dfa.add_states({"Z"})
        # iterable-of-dsts form
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
    dfa = DFAV2(Q, Sigma, delta, q0, F)

    # Adding two distinct dsts for the same (src, sym) should make it invalid on exit
    with pytest.raises(ValueError):
        with dfa.edit():
            dfa.add_transitions({("S", "a"): ["A", "S"]})


def test_remove_transitions_iterable_values(simple_dfa_spec: DFA_Params):
    Q, Sigma, delta, q0, F = simple_dfa_spec
    dfa = DFAV2(Q, Sigma, delta, q0, F)

    # First make ("S","a") nondeterministic by adding a second edge
    with pytest.raises(ValueError):
        with dfa.edit():
            dfa.add_transitions({("S", "a"): "S"})
            # Now remove that extra edge using iterable form and ALSO remove a required edge to force invalidity
            dfa.remove_transitions({("S", "a"): ["S"]})
            dfa.remove_transitions({("S", "b"): ["S"]})

    # Do add then remove cleanly and end valid
    dfa = DFAV2(Q, Sigma, delta, q0, F)
    with dfa.edit():
        dfa.add_transitions({("S", "a"): "S"})
        dfa.remove_transitions({("S", "a"): ["S"]})
    assert dfa.is_valid_dfa()


# ---------------------------------------------------------------------
# Automaton properties: Q, Σ, δ, q0, F
# ---------------------------------------------------------------------
def test_properties_basic(built_simple_dfa: DFAV2):
    dfa = built_simple_dfa

    # Q: all non-dead state names
    assert isinstance(dfa.Q, set)
    assert dfa.Q == {"S", "A"}

    # Σ: all letter chars
    assert isinstance(dfa.Σ, set)
    assert dfa.Σ == {"a", "b"}

    # δ: dict[(src_name, sym_char)] -> set[dst_names] (exclude dead src/dst)
    assert isinstance(dfa.δ, dict)
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

    # Build a DFA where S is final, A is not final; then kill A
    Q2, Sigma2, delta2, q02, F2 = {"S", "A"}, {
        "a", "b"}, dict(delta), "S", {"S"}
    dfa2 = DFAV2(Q2, Sigma2, delta2, q02, F2)

    dfa2.get_state("A").kill()

    assert dfa2.Q == {"S"}
    assert dfa2.Σ == {"a", "b"}

    expected_delta: dict[tuple[str, str], set[str]] = {
        ("S", "a"): set(),     # A is dead, so destination filtered out
        ("S", "b"): {"S"},
    }
    assert dfa2.δ == expected_delta
    assert dfa2.F == {"S"}


def test_properties_after_killing_final_state(built_simple_dfa: DFAV2):
    dfa = built_simple_dfa
    dfa.get_state("A").kill()

    assert dfa.Q == {"S"}
    assert dfa.F == set()

    expected_delta: Delta = {
        ("S", "a"): set(),  # used to be {"A"}, but A is dead
        ("S", "b"): {"S"},
    }
    assert dfa.δ == expected_delta


def test_q0_name_even_if_start_state_is_killed(built_simple_dfa: DFAV2):
    dfa = built_simple_dfa
    dfa.get_state("S").kill()

    assert dfa.q0 == "S"
    assert "S" not in dfa.Q
    expected_keys = {("A", "a"), ("A", "b")}
    assert set(dfa.δ.keys()) == expected_keys


@pytest.mark.parametrize(
    "kill_state, expected_Q, expected_F",
    [
        pytest.param("S", {"A"}, {"A"}, id="kill_start"),
        pytest.param("A", {"S"}, set[str](), id="kill_final"),
    ],
)
def test_Q_and_F_type_and_semantics_under_kill(
    built_simple_dfa: DFAV2, kill_state: str, expected_Q: set[str], expected_F: set[str]
):
    dfa = built_simple_dfa
    dfa.get_state(kill_state).kill()
    assert isinstance(dfa.Q, set)
    assert isinstance(dfa.F, set)
    assert dfa.Q == expected_Q
    assert dfa.F == expected_F


def test_δ_types_and_keyspace(built_simple_dfa: DFAV2):
    dfa = built_simple_dfa
    d = dfa.δ
    # dict[(str,str)] -> set[str]
    assert all(
        isinstance(k, tuple) and len(k) == 2 and isinstance(
            k[0], str) and isinstance(k[1], str)
        for k in d.keys()
    )
    assert all(isinstance(v, set) and all(isinstance(x, str)
               for x in v) for v in d.values())

    # All keys correspond to live sources and defined letters
    live_sources = dfa.Q
    letters = dfa.Σ
    assert all(k[0] in live_sources and k[1] in letters for k in d.keys())


# ---------------------------------------------------------------------
# Remove states (ignore edges; require rewiring)
# ---------------------------------------------------------------------
def test_remove_states_requires_edit(built_simple_dfa: DFAV2):
    dfa = built_simple_dfa
    with pytest.raises(RuntimeError):
        dfa.remove_states(["A"])


def test_delta_property_filters_dead_and_uses_tx_not_private(built_simple_dfa: DFAV2):
    dfa = built_simple_dfa
    dfa.get_state("A").kill()
    assert ("A", "a") not in dfa.δ
    assert ("A", "b") not in dfa.δ
    assert dfa.δ[("S", "a")] == set()  # A is dead, so filtered out
    assert dfa.δ[("S", "b")] == {"S"}


def test_is_valid_dfa_counts_only_live_edges(simple_dfa_spec: DFA_Params):
    Q, Sigma, delta, q0, F = simple_dfa_spec
    dfa = DFAV2(Q, Sigma, delta, q0, F)

    assert dfa.is_valid_dfa()

    with pytest.raises(ValueError):
        with dfa.edit():
            dfa.remove_states(["A"])  # killing A leaves S --a--> (no live dst)
            # exit should fail validity


def test_index_edges_remain_for_rollback_even_after_kill(simple_dfa_spec: DFA_Params):
    Q, Sigma, delta, q0, F = simple_dfa_spec
    dfa = DFAV2(Q, Sigma, delta, q0, F)

    sid_S = dfa._sid_of("S")  # type: ignore
    sid_A = dfa._sid_of("A")  # type: ignore
    aid_a = dfa._aid_of("a")  # type: ignore

    with pytest.raises(ValueError):
        with dfa.edit():
            dfa.remove_states(["A"])
            # Raw index still holds the edge (for rollback)
            assert dfa._tx.delta.get((sid_S, aid_a)) == {sid_A}  # type: ignore
            # But δ (live view) shows none:
            assert dfa.δ.get(("S", "a")) == set()


def test_rewire_after_kill_restores_validity(simple_dfa_spec: DFA_Params):
    Q, Sigma, delta, q0, F = simple_dfa_spec
    dfa = DFAV2(Q, Sigma, delta, q0, F)

    with dfa.edit():
        dfa.remove_states(["A"])

        # Add a sink Z and wire all letters to itself
        dfa.add_states({"Z"})
        for sym in Sigma:
            dfa.add_transitions({("Z", sym): "Z"})

        # For every live (src, sym) with 0 LIVE destinations, point to Z
        for s_name in dfa.Q:
            for sym in dfa.Σ:
                sid = dfa._sid_of(s_name)  # type: ignore
                aid = dfa._aid_of(sym)     # type: ignore
                dst_ids = dfa._tx.delta[(sid, aid)]  # type: ignore

                live_dsts = {
                    d for d in dst_ids
                    if not dfa.states[d].is_dead()
                }
                if len(live_dsts) == 0:
                    dfa.add_transitions({(s_name, sym): "Z"})

    assert dfa.is_valid_dfa()
    # spot-check S on 'a' now goes to Z (live)
    sid_S = dfa._sid_of("S")  # type: ignore
    aid_a = dfa._aid_of("a")  # type: ignore
    sid_Z = dfa._sid_of("Z")  # type: ignore
    live_dsts = {
        d for d in dfa._tx.delta[(sid_S, aid_a)]  # type: ignore
        if not dfa.states[d].is_dead()
    }
    assert live_dsts == {sid_Z}


def test_remove_states_only_kills_and_requires_edit(built_simple_dfa: DFAV2):
    dfa = built_simple_dfa
    with pytest.raises(RuntimeError):
        dfa.remove_states(["S"])
    with pytest.raises(ValueError):
        with dfa.edit():
            dfa.remove_states(["S"])
            assert dfa.get_state("S").is_dead()
            # exit raises because other states (A) now have a missing live dst on 'b' or 'a' depending on wiring

# ---------------------------------------------------------------------
# Killable letters
# ---------------------------------------------------------------------


def test_remove_letters_requires_edit(built_simple_dfa: DFAV2):
    dfa = built_simple_dfa
    with pytest.raises(RuntimeError):
        dfa.remove_letters(["a"])  # type: ignore[attr-defined]


def test_killing_letter_shrinks_sigma_and_delta(built_simple_dfa: DFAV2):
    dfa = built_simple_dfa

    # Kill 'a' -> Σ should drop 'a'; δ should only have 'b' keys
    with dfa.edit():
        dfa.remove_letters(["a"])  # type: ignore[attr-defined]

    assert dfa.Σ == {"b"}
    assert set(dfa.δ.keys()) == {("S", "b"), ("A", "b")}
    # Still valid: we only require one live dst per LIVE letter
    assert dfa.is_valid_dfa()


def test_kill_all_letters_makes_invalid(built_simple_dfa: DFAV2):
    dfa = built_simple_dfa
    with pytest.raises(ValueError):
        with dfa.edit():
            dfa.remove_letters(["a", "b"])  # type: ignore[attr-defined]
            # exit should fail (no live letters)


def test_revive_letter_via_add_letters(built_simple_dfa: DFAV2):
    dfa = built_simple_dfa
    with dfa.edit():
        dfa.remove_letters(["a"])  # kill 'a'
        # revive 'a'
        dfa.add_letters({"a"})

        # To remain valid, there must be exactly 1 live dst for every live (state,'a')
        # Our original construction satisfies this already since edges were kept.
        # If you'd removed a state's 'a' edge earlier, you'd need to re-add it here.

    assert "a" in dfa.Σ
    assert dfa.is_valid_dfa()


def test_delta_filters_dead_letters_even_if_edges_exist(simple_dfa_spec: DFA_Params):
    Q, Sigma, delta, q0, F = simple_dfa_spec
    dfa = DFAV2(Q, Sigma, delta, q0, F)

    with dfa.edit():
        dfa.remove_letters(["a"])

    # Raw index still has ('*','a') edges
    sid_S, sid_A = dfa._sid_of("S"), dfa._sid_of("A")  # type: ignore
    aid_a = dfa._aid_of("a")  # type: ignore
    assert dfa._tx.delta.get((sid_S, aid_a)) == {sid_A}  # type: ignore

    # Live view hides them
    assert ("S", "a") not in dfa.δ
    assert ("A", "a") not in dfa.δ


def test_letter_kill_plus_state_kill_composition(simple_dfa_spec: DFA_Params):
    Q, Sigma, delta, q0, F = simple_dfa_spec
    dfa = DFAV2(Q, Sigma, delta, q0, F)

    with dfa.edit():
        dfa.remove_letters(["a"])
        dfa.remove_states(["A"])

    # Σ only 'b'; Q only 'S'
    assert dfa.Σ == {"b"}
    assert dfa.Q == {"S"}

    # δ only contains ("S","b") -> {"S"}
    assert dfa.δ == {("S", "b"): {"S"}}
    assert dfa.is_valid_dfa()

# ---------------------------------------------------------------------
# _Index lazy caches (no external version)
# ---------------------------------------------------------------------


def test_index_lazy_views_build_and_refresh():
    idx = _Index()

    # Initially empty; accessing views builds empty caches
    assert idx.out == {}
    assert idx.inn == {}
    assert idx.edges == {}

    # Add a few edges; caches should reflect updates after invalidation+rebuild
    idx.add(0, 0, 1)  # 0 --a--> 1
    assert idx.out[0][0] == {1}
    assert idx.inn[1][0] == {0}
    assert (0, 0, 1) in idx.edges[0]

    # Add another edge on same key
    idx.add(0, 0, 2)
    assert idx.out[0][0] == {1, 2}
    assert idx.inn[2][0] == {0}
    assert any(t == (0, 0, 2) for t in idx.edges[0])

    # Remove one edge
    idx.remove(0, 0, 1)
    assert idx.out[0][0] == {2}
    assert 1 not in idx.inn  # removed

    # Replace edges for a different symbol
    idx.set(0, 1, (3,))
    assert idx.out[0][1] == {3}
    assert idx.inn[3][1] == {0}

    # set empty → delete key
    idx.set(0, 1, ())
    assert 1 not in idx.out.get(0, {})
    assert 1 not in idx.inn.get(3, {})

    # Clear all
    idx.clear()
    assert idx.delta == {}
    assert idx.out == {}
    assert idx.inn == {}
    assert idx.edges == {}

# ---------------------------------------------------------------------
# transition() [ID-based] and accepts()
# ---------------------------------------------------------------------

def test_transition_live_ids_basic(simple_dfa_spec: DFA_Params):
    Q, Sigma, delta, q0, F = simple_dfa_spec
    dfa = DFAV2(Q, Sigma, delta, q0, F)
    sid_S, sid_A = dfa._sid_of("S"), dfa._sid_of("A")  # type: ignore
    aid_a, aid_b = dfa._aid_of("a"), dfa._aid_of("b")  # type: ignore

    # S --a--> {A}, S --b--> {S}
    assert dfa.transition(sid_S, aid_a) == {sid_A}
    assert dfa.transition(sid_S, aid_b) == {sid_S}

    # A --b--> {S}
    assert dfa.transition(sid_A, aid_b) == {sid_S}


def test_transition_throws_on_dead_state_or_letter_when_flag_true(simple_dfa_spec: DFA_Params):
    Q, Sigma, delta, q0, F = simple_dfa_spec
    dfa = DFAV2(Q, Sigma, delta, q0, F)
    sid_S, sid_A = dfa._sid_of("S"), dfa._sid_of("A")  # type: ignore
    aid_a = dfa._aid_of("a")  # type: ignore

    # Kill A inside edit; call transition on A (dead) should raise if throw_on_dead=True
    with pytest.raises(ValueError):
        with dfa.edit():
            dfa.remove_states(["A"])
            _ = dfa.transition(sid_A, aid_a, throw_on_dead=True)

    # Kill letter 'a'; calling transition with that letter should raise if throw_on_dead=True
    with pytest.raises(ValueError):
        with dfa.edit():
            dfa.remove_letters(["a"])  # type: ignore[attr-defined]
            _ = dfa.transition(sid_S, aid_a, throw_on_dead=True)


def test_transition_no_throw_on_dead_letter_returns_filtered_dsts(simple_dfa_spec: DFA_Params):
    """
    With throw_on_dead=False, a dead LETTER should not raise. The function
    still returns live destinations (filtering dead states only).
    """
    Q, Sigma, delta, q0, F = simple_dfa_spec
    dfa = DFAV2(Q, Sigma, delta, q0, F)
    sid_S, sid_A = dfa._sid_of("S"), dfa._sid_of("A")  # type: ignore
    aid_a = dfa._aid_of("a")  # type: ignore

    with dfa.edit():
        dfa.remove_letters(["a"])  # type: ignore[attr-defined]
        # Do not throw; since A is alive, you'll still see {A}
        assert dfa.transition(sid_S, aid_a, throw_on_dead=False) == {sid_A}


def test_transition_filters_dead_destinations(simple_dfa_spec: DFA_Params):
    """
    Dead destinations are filtered out of the returned set.
    """
    Q, Sigma, delta, q0, F = simple_dfa_spec
    dfa = DFAV2(Q, Sigma, delta, q0, F)
    sid_S = dfa._sid_of("S")  # type: ignore
    aid_a = dfa._aid_of("a")  # type: ignore

    with pytest.raises(ValueError):
        with dfa.edit():
            dfa.remove_states(["A"])
            # raw edge S --a--> A exists in _tx, but A is dead; transition returns empty
            assert dfa.transition(sid_S, aid_a, throw_on_dead=False) == set()
            # edit() exit is invalid (S has no live dst on 'a'), so we expect ValueError


def test_accepts_basic_language(simple_dfa_spec: DFA_Params):
    # DFA recognizes strings ending with 'a'
    Q, Sigma, delta, q0, F = simple_dfa_spec
    dfa = DFAV2(Q, Sigma, delta, q0, F)

    # Accept
    assert dfa.accepts("a")
    assert dfa.accepts("ba")
    assert dfa.accepts("bba")
    assert dfa.accepts("abba")

    # Reject
    assert not dfa.accepts("")
    assert not dfa.accepts("b")
    assert not dfa.accepts("abb")


def test_accepts_raises_on_unknown_symbol(built_simple_dfa: DFAV2):
    dfa = built_simple_dfa
    with pytest.raises(ValueError):
        dfa.accepts("ac")  # 'c' not in live Σ


def test_accepts_respects_dead_letter(built_simple_dfa: DFAV2):
    dfa = built_simple_dfa
    with dfa.edit():
        dfa.remove_letters(["a"])  # type: ignore[attr-defined]
    # Now 'a' is not in Σ, so using it should raise
    with pytest.raises(ValueError):
        dfa.accepts("a")


def test_accepts_after_kill_and_rewire(simple_dfa_spec: DFA_Params):
    """
    Kill A, add sink Z, rewire missing edges to keep DFA valid, then
    evaluate acceptance with the new language.
    """
    Q, Sigma, delta, q0, F = simple_dfa_spec
    dfa = DFAV2(Q, Sigma, delta, q0, F)

    with dfa.edit():
        # Kill A
        dfa.remove_states(["A"])
        # Add sink Z and wire to itself on all letters
        dfa.add_states({"Z"})
        for sym in Sigma:
            dfa.add_transitions({("Z", sym): "Z"})
        # Fill missing live edges by pointing to Z
        for s_name in dfa.Q:
            for sym in dfa.Σ:
                sid = dfa._sid_of(s_name)  # type: ignore
                aid = dfa._aid_of(sym)     # type: ignore
                live = {
                    d for d in dfa._tx.delta.get((sid, aid), set())  # type: ignore
                    if not dfa.states[d].is_dead()
                }
                if not live:
                    dfa.add_transitions({(s_name, sym): "Z"})

    assert dfa.is_valid_dfa()

    # Language changed (no final A). Our wiring sends 'a' from S to Z (non-final),
    # so strings ending in 'a' now reject.
    assert not dfa.accepts("a")
    assert not dfa.accepts("ba")
    assert not dfa.accepts("bbb")
