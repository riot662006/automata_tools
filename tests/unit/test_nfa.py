import pytest
from types import MappingProxyType
from typing import Mapping, Tuple

from automata.automaton import Epsilon, Symbol, sym_sort_key
from automata.nfa import NFA


def make_nfa(
    Q: set[str],
    Σ: set[str],
    δ: Mapping[Tuple[str, Symbol], set[str]],
    q0: str,
    F: set[str],
) -> NFA:
    """
    Helper: construct NFA with given components. Your NFA/Automaton __post_init__
    will freeze sets and generate edges as nested MappingProxyType with tuple labels.
    """
    return NFA(
        Q=frozenset(Q),
        Σ=frozenset(Σ),
        δ={(k[0], k[1]): frozenset(v) for k, v in δ.items()},
        q0=q0,
        F=frozenset(F),
    )


@pytest.fixture
def nfa_with_epsilon_and_multi() -> NFA:
    # States: q0 start; qf accept
    # Epsilon from q0 to q1 and q2
    # q1 --a|b--> qf
    # q2 --b--> qf and --a--> q2 (loop)
    Q = {"q0", "q1", "q2", "qf"}
    Σ = {"a", "b"}  # ε is not in Σ (by convention)
    δ: Mapping[Tuple[str, Symbol], set[str]] = {
        ("q0", Epsilon): {"q1", "q2"},  # ε-split
        ("q1", "a"): {"qf"},  # single symbol to single dst
        ("q1", "b"): {"qf"},
        # multi-dest set already handled, but here single
        ("q2", "b"): {"qf"},
        ("q2", "a"): {"q2"},  # self-loop on 'a'
        # also allow ε-loop on q1 (exercise stringification)
        ("q1", Epsilon): {"q1"},
    }
    return make_nfa(Q, Σ, δ, q0="q0", F={"qf"})


@pytest.fixture
def nfa_mixed_labels() -> NFA:
    """
    q0 -- 'b','a',ε --> q1
    q0 -- 'c','1',ε --> q2
    q1 -- 'a'        --> q1  (self loop)
    """
    Q = {"q0", "q1", "q2"}
    Σ = {"0", "1", "a", "b", "c"}  # ε is not in Σ by convention
    δ: Mapping[Tuple[str, Symbol], set[str]] = {
        ("q0", "b"): {"q1"},
        ("q0", "a"): {"q1"},
        ("q0", Epsilon): {"q1", "q2"},
        ("q0", "c"): {"q2"},
        ("q0", "1"): {"q2"},
        ("q1", "a"): {"q1"},
    }
    return make_nfa(Q, Σ, δ, q0="q0", F={"q1"})


def test_edges_shape_readonly(nfa_with_epsilon_and_multi: NFA):
    e = nfa_with_epsilon_and_multi.edges
    assert isinstance(e, Mapping)
    assert isinstance(e, MappingProxyType)
    # inner maps read-only too
    for _, dst_map in e.items():
        assert isinstance(dst_map, Mapping)
        assert isinstance(dst_map, MappingProxyType)
        for _, labels in dst_map.items():
            assert isinstance(labels, tuple)  # not list/set
            # deterministic order
            assert list(labels) == sorted(labels, key=sym_sort_key)


def test_edges_grouping_and_label_strings(nfa_with_epsilon_and_multi: NFA):
    e = nfa_with_epsilon_and_multi.edges

    # q0 --ε--> q1 and q2  (labels are stringified, so 'ε')
    assert set(e["q0"].keys()) == {"q1", "q2"}
    assert e["q0"]["q1"] == (Epsilon,)
    assert e["q0"]["q2"] == (Epsilon,)

    # q1 --a|b--> qf  and ε-loop q1->q1
    assert set(e["q1"].keys()) == {"qf", "q1"}
    assert e["q1"]["qf"] == ("a", "b")  # sorted
    assert e["q1"]["q1"] == (Epsilon,)

    # q2 --a--> q2 and --b--> qf
    assert set(e["q2"].keys()) == {"q2", "qf"}
    assert e["q2"]["q2"] == ("a",)
    assert e["q2"]["qf"] == ("b",)


def test_edges_consistent_with_delta(nfa_with_epsilon_and_multi: NFA):
    """Every (src, dst) implied by δ appears in edges with all symbols collected."""
    nfa = nfa_with_epsilon_and_multi
    e = nfa.edges

    implied: Mapping[Tuple[str, str], set[Symbol]] = {}
    for (src, sym), dsts in nfa.δ.items():
        for dst in dsts:
            implied.setdefault((src, dst), set()).add(sym)

    for (src, dst), labels in implied.items():
        assert src in e and dst in e[src], f"Missing edge {src}->{dst}"
        assert tuple(sorted(labels, key=sym_sort_key)) == e[src][dst]


def test_edges_missing_src_absent(nfa_with_epsilon_and_multi: NFA):
    # Any state with no outgoing transitions may be absent from edges
    # (depends on your builder; qf has no outgoing in this example)
    e = nfa_with_epsilon_and_multi.edges
    assert "qf" not in e


def test_edges_types_and_readonly(nfa_mixed_labels: NFA):
    e = nfa_mixed_labels.edges
    assert isinstance(e, Mapping)
    assert isinstance(e, MappingProxyType)

    for _, dst_map in e.items():
        assert isinstance(dst_map, Mapping)
        assert isinstance(dst_map, MappingProxyType)
        for _, labels in dst_map.items():
            # labels must be an immutable, deterministically-ordered tuple of Symbols
            assert isinstance(labels, tuple)
            for sym in labels:
                # sym is either a str from Σ or the Epsilon sentinel
                assert isinstance(sym, (str, type(Epsilon)))
            # should be sorted by your custom key (strings first, lexicographic; ε last)
            strings = [s for s in labels if isinstance(s, str)]
            epsilons = [s for s in labels if not isinstance(s, str)]
            assert strings == sorted(strings)
            if epsilons:
                # All ε at the end
                assert all(not isinstance(s, str) for s in labels[len(strings) :])


def test_edge_ordering_per_destination(nfa_mixed_labels: NFA):
    """
    Verify exact ordering on specific edges matches the key:
      strings sorted ascending, then ε.
    """
    e = nfa_mixed_labels.edges

    # q0 -> q1 has {'a','b',ε} => ('a','b',ε)
    assert e["q0"]["q1"] == ("a", "b", Epsilon)

    # q0 -> q2 has {'1','aa',ε} => ('1','c',ε)  ('1' < 'c' lexicographically)
    assert e["q0"]["q2"] == ("1", "c", Epsilon)

    # q1 -> q1 has only {'a'} => ('a',)
    assert e["q1"]["q1"] == ("a",)


def test_edges_do_not_inject_fake_labels(nfa_mixed_labels: NFA):
    """
    Ensure no extra labels get added beyond δ.
    """
    e = nfa_mixed_labels.edges
    # Recompute implied (src,dst)->labels from δ
    implied: Mapping[Tuple[str, str], set[Symbol]] = {}
    for (src, sym), dsts in nfa_mixed_labels.δ.items():
        for dst in dsts:
            implied.setdefault((src, dst), set()).add(sym)

    for (src, dst), syms in implied.items():
        # Expected ordering under the sort key
        strings = sorted([s for s in syms if isinstance(s, str)])
        tail = [s for s in syms if not isinstance(s, str)]
        expected = tuple(strings + tail)  # only Epsilon in tail here
        assert e[src][dst] == expected


def test_identity_of_epsilon_preserved(nfa_mixed_labels: NFA):
    """
    The tuple should hold the actual Epsilon sentinel (not the string 'ε').
    """
    assert (e := nfa_mixed_labels.edges)
    assert Epsilon in e["q0"]["q1"]
    assert Epsilon in e["q0"]["q2"]
    # also make sure we did not stringify ε
    for labels in (e["q0"]["q1"], e["q0"]["q2"]):
        assert "ε" not in labels  # no string 'ε'; only the sentinel instance


def test_transition_uses_pre_epsilon_closure():
    """
    q0 -ε-> q1,  (no direct q0-'a' edge)
    q1 -a-> q2
    Expect: transition(q0, 'a') includes q2.
    """
    Q = {"q0", "q1", "q2"}
    Σ = {"a"}
    δ: Mapping[Tuple[str, Symbol], set[str]] = {
        ("q0", Epsilon): {"q1"},
        ("q1", "a"): {"q2"},
    }
    nfa = make_nfa(Q, Σ, δ, q0="q0", F={"q2"})

    got = nfa.transition("q0", "a")
    assert got == {"q2"}


def test_transition_applies_post_epsilon_closure():
    """
    q1 -a-> q2, q2 -ε-> qf
    From q1 on 'a' we reach q2, and post ε-closure adds qf.
    """
    Q = {"q1", "q2", "qf"}
    Σ = {"a"}
    δ: Mapping[Tuple[str, Symbol], set[str]] = {
        ("q1", "a"): {"q2"},
        ("q2", Epsilon): {"qf"},
    }
    nfa = make_nfa(Q, Σ, δ, q0="q1", F={"qf"})

    got = nfa.transition("q1", "a")
    assert got == {"q2", "qf"}


def test_transition_handles_epsilon_chain_both_sides():
    """
    q0 -ε-> q1 -ε-> q2,  q2 -a-> q3,  q3 -ε-> q4
    transition(q0,'a') should include {q3, q4}.
    """
    Q = {"q0", "q1", "q2", "q3", "q4"}
    Σ = {"a"}
    δ: Mapping[Tuple[str, Symbol], set[str]] = {
        ("q0", Epsilon): {"q1"},
        ("q1", Epsilon): {"q2"},
        ("q2", "a"): {"q3"},
        ("q3", Epsilon): {"q4"},
    }
    nfa = make_nfa(Q, Σ, δ, q0="q0", F={"q4"})

    got = nfa.transition("q0", "a")
    assert got == {"q3", "q4"}


def test_transition_with_epsilon_cycle_no_infinite_loop():
    """
    q0 -ε-> q1, q1 -ε-> q0 (cycle), q1 -a-> q2
    Should still terminate and include q2.
    """
    Q = {"q0", "q1", "q2"}
    Σ = {"a"}
    δ: Mapping[Tuple[str, Symbol], set[str]] = {
        ("q0", Epsilon): {"q1"},
        ("q1", Epsilon): {"q0"},
        ("q1", "a"): {"q2"},
    }
    nfa = make_nfa(Q, Σ, δ, q0="q0", F={"q2"})

    got = nfa.transition("q0", "a")
    assert got == {"q2"}


def test_transition_no_move_returns_empty_set():
    """
    No edge on given symbol reachable via pre-ε closure.
    """
    Q = {"q0", "q1"}
    Σ = {"a"}
    δ: Mapping[Tuple[str, Symbol], set[str]] = {
        ("q0", Epsilon): {"q1"},
        # no ('q1','a') edge
    }
    nfa = make_nfa(Q, Σ, δ, q0="q0", F=set())

    got = nfa.transition("q0", "a")
    assert got == set()


def test_transition_multiple_targets_and_post_closures():
    """
    q0 -ε-> q1
    q1 -a-> {q2,q3}
    q2 -ε-> qf
    q3 -ε-> qf
    Expect: {q2,q3,qf}
    """
    Q = {"q0", "q1", "q2", "q3", "qf"}
    Σ = {"a"}
    δ: Mapping[Tuple[str, Symbol], set[str]] = {
        ("q0", Epsilon): {"q1"},
        ("q1", "a"): {"q2", "q3"},
        ("q2", Epsilon): {"qf"},
        ("q3", Epsilon): {"qf"},
    }
    nfa = make_nfa(Q, Σ, δ, q0="q0", F={"qf"})

    got = nfa.transition("q0", "a")
    assert got == {"q2", "q3", "qf"}


def test_accepts_empty_when_start_is_final():
    """
    ε is accepted iff q0 ∈ F (or ε-closure(q0) intersects F).
    Here q0 is already final.
    """
    Q = {"q0"}
    Σ = {"a"}
    δ: Mapping[Tuple[str, Symbol], set[str]] = {}
    nfa = make_nfa(Q, Σ, δ, q0="q0", F={"q0"})
    assert nfa.accepts("") is True


def test_accepts_empty_via_epsilon_closure():
    """
    q0 -ε-> qf, qf ∈ F, so ε should be accepted even though q0 ∉ F.
    """
    Q = {"q0", "qf"}
    Σ = {"a"}
    δ: Mapping[Tuple[str, Symbol], set[str]] = {("q0", Epsilon): {"qf"}}
    nfa = make_nfa(Q, Σ, δ, q0="q0", F={"qf"})
    assert nfa.accepts("") is True


def test_rejects_empty_when_no_path_to_final():
    Q = {"q0", "q1"}
    Σ = {"a"}
    δ: Mapping[Tuple[str, Symbol], set[str]] = {}
    nfa = make_nfa(Q, Σ, δ, q0="q0", F={"q1"})
    assert nfa.accepts("") is False


def test_simple_accept_single_symbol():
    """
    q0 -a-> qf, qf ∈ F
    """
    Q = {"q0", "qf"}
    Σ = {"a"}
    δ: Mapping[Tuple[str, Symbol], set[str]] = {("q0", "a"): {"qf"}}
    nfa = make_nfa(Q, Σ, δ, q0="q0", F={"qf"})
    assert nfa.accepts("a") is True
    assert nfa.accepts("aa") is False  # no second move


def test_accepts_uses_pre_epsilon_closure():
    """
    q0 -ε-> q1, q1 -a-> qf
    accept 'a' from q0 by starting on ε-reachable q1.
    """
    Q = {"q0", "q1", "qf"}
    Σ = {"a"}
    δ: Mapping[Tuple[str, Symbol], set[str]] = {
        ("q0", Epsilon): {"q1"},
        ("q1", "a"): {"qf"},
    }
    nfa = make_nfa(Q, Σ, δ, q0="q0", F={"qf"})
    assert nfa.accepts("a") is True


def test_accepts_applies_post_epsilon_closure():
    """
    q0 -a-> q1, q1 -ε-> qf
    After consuming 'a', ε-closure should add qf to current states.
    """
    Q = {"q0", "q1", "qf"}
    Σ = {"a"}
    δ: Mapping[Tuple[str, Symbol], set[str]] = {
        ("q0", "a"): {"q1"},
        ("q1", Epsilon): {"qf"},
    }
    nfa = make_nfa(Q, Σ, δ, q0="q0", F={"qf"})
    assert nfa.accepts("a") is True


def test_accepts_handles_epsilon_cycles():
    """
    q0 -ε-> q1, q1 -ε-> q0 (cycle), q1 -b-> qf
    """
    Q = {"q0", "q1", "qf"}
    Σ = {"b"}
    δ: Mapping[Tuple[str, Symbol], set[str]] = {
        ("q0", Epsilon): {"q1"},
        ("q1", Epsilon): {"q0"},
        ("q1", "b"): {"qf"},
    }
    nfa = make_nfa(Q, Σ, δ, q0="q0", F={"qf"})
    assert nfa.accepts("b") is True


def test_accepts_multiple_paths_nondeterministic_branching():
    """
    q0 -a-> q1 and q2; q1 -b-> qf, q2 -b-> qdead
    Accept if any path ends in F.
    """
    Q = {"q0", "q1", "q2", "qf", "qdead"}
    Σ = {"a", "b"}
    δ: Mapping[Tuple[str, Symbol], set[str]] = {
        ("q0", "a"): {"q1", "q2"},
        ("q1", "b"): {"qf"},
        ("q2", "b"): {"qdead"},
    }
    nfa = make_nfa(Q, Σ, δ, q0="q0", F={"qf"})
    assert nfa.accepts("ab") is True  # via q1
    assert nfa.accepts("aa") is False  # no 'a' out of q1/q2


def test_accepts_rejects_when_no_valid_move():
    """
    No available move on read symbol from any current state.
    """
    Q = {"q0", "q1"}
    Σ = {"a", "b"}
    δ: Mapping[Tuple[str, Symbol], set[str]] = {("q0", "a"): {"q1"}}
    nfa = make_nfa(Q, Σ, δ, q0="q0", F={"q1"})
    assert nfa.accepts("b") is False  # invalid symbol handled separately
    assert nfa.accepts("aa") is False  # second 'a' has no edge from q1


def test_accepts_raises_on_invalid_symbol():
    Q = {"q0", "q1"}
    Σ = {"a"}  # 'b' not in Σ
    δ: Mapping[Tuple[str, Symbol], set[str]] = {("q0", "a"): {"q1"}}
    nfa = make_nfa(Q, Σ, δ, q0="q0", F={"q1"})
    with pytest.raises(ValueError):
        nfa.accepts("ab")  # 'b' triggers ValueError per your code
