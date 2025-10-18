from automata.automaton import Epsilon
from automata.minimization import find_dead_states, group_indistinguishable_states, minimize
from tests.conftest import make_dfa, make_nfa


# ───────────────────────────────
# 🔹 1. Basic DFA with one dead state
# ───────────────────────────────
def test_find_dead_states_basic_dfa():
    dfa = make_dfa(
        Q={"q0", "q1", "q_dead"},
        Σ={"a", "b"},
        δ={
            ("q0", "a"): "q1",
            ("q0", "b"): "q_dead",
            ("q1", "a"): "q1",
            ("q1", "b"): "q_dead",
            ("q_dead", "a"): "q_dead",
            ("q_dead", "b"): "q_dead",
        },
        q0="q0",
        F={"q1"},
    )
    assert find_dead_states(dfa) == {"q_dead"}


# ───────────────────────────────
# 🔹 2. DFA with all states dead (no accepting states)
# ───────────────────────────────
def test_all_dead_states_no_accepting():
    dfa = make_dfa(
        Q={"x", "y"},
        Σ={"a"},
        δ={("x", "a"): "y", ("y", "a"): "x"},
        q0="x",
        F=set(),
    )
    assert find_dead_states(dfa) == {"x", "y"}


# ───────────────────────────────
# 🔹 3. DFA where no states are dead (all reach acceptance)
# ───────────────────────────────
def test_no_dead_states():
    dfa = make_dfa(
        Q={"s0", "s1"},
        Σ={"a"},
        δ={("s0", "a"): "s1", ("s1", "a"): "s0"},
        q0="s0",
        F={"s0", "s1"},
    )
    assert find_dead_states(dfa) == set()


# ───────────────────────────────
# 🔹 4. NFA where one branch leads to acceptance, another dies
# ───────────────────────────────
def test_nfa_partial_dead():
    nfa = make_nfa(
        Q={"q0", "q1", "q2"},
        Σ={"a"},
        δ={
            ("q0", "a"): {"q1", "q2"},
            ("q1", "a"): {"q1"},
        },
        q0="q0",
        F={"q1"},
    )
    assert find_dead_states(nfa) == {"q2"}


# ───────────────────────────────
# 🔹 5. NFA with epsilon transitions (ε)
# ───────────────────────────────
def test_nfa_with_epsilon_transitions():
    nfa = make_nfa(
        Q={"p0", "p1", "p2"},
        Σ={"a"},
        δ={
            ("p0", Epsilon): {"p1"},  # epsilon transition
            ("p1", "a"): {"p2"},
            ("p2", "a"): {"p2"},
        },
        q0="p0",
        F={"p2"},
    )
    assert find_dead_states(nfa) == set()  # all can reach p2


# ───────────────────────────────
# 🔹 6. Unreachable state (not visited from q0)
# ───────────────────────────────
def test_unreachable_dead_state():
    dfa = make_dfa(
        Q={"q0", "q1", "q2"},
        Σ={"a"},
        δ={
            ("q0", "a"): "q1",
            ("q1", "a"): "q1",
            ("q2", "a"): "q2",
        },
        q0="q0",
        F={"q1"},
    )
    assert find_dead_states(dfa) == {"q2"}  # q2 unreachable


# ───────────────────────────────
# 🔹 7. DFA with self-looping final state
# ───────────────────────────────
def test_final_state_self_loop():
    dfa = make_dfa(
        Q={"start", "accept"},
        Σ={"a"},
        δ={("start", "a"): "accept", ("accept", "a"): "accept"},
        q0="start",
        F={"accept"},
    )
    assert find_dead_states(dfa) == set()


# ───────────────────────────────
# 🔹 8. DFA with multiple disconnected components
# ───────────────────────────────
def test_multiple_disconnected_components():
    dfa = make_dfa(
        Q={"A", "B", "C", "D"},
        Σ={"a"},
        δ={
            ("A", "a"): "B",
            ("B", "a"): "A",
            ("C", "a"): "D",
            ("D", "a"): "C",
        },
        q0="A",
        F={"B"},
    )
    # Only C, D are unreachable from q0 and can’t reach B
    assert find_dead_states(dfa) == {"C", "D"}


# ───────────────────────────────
# 🔹 9. DFA with cycles leading to acceptance (no dead states)
# ───────────────────────────────
def test_cyclic_dfa_no_dead_states():
    dfa = make_dfa(
        Q={"q0", "q1", "q2"},
        Σ={"a"},
        δ={("q0", "a"): "q1", ("q1", "a"): "q2", ("q2", "a"): "q0"},
        q0="q0",
        F={"q2"},
    )
    assert find_dead_states(dfa) == set()


# ───────────────────────────────
# 🔹 10. DFA with unreachable accepting state
# ───────────────────────────────
def test_unreachable_accepting_state():
    dfa = make_dfa(
        Q={"q0", "q1", "q2"},
        Σ={"a"},
        δ={("q0", "a"): "q1", ("q1", "a"): "q1", ("q2", "a"): "q2", },
        q0="q0",
        F={"q2"},
    )
    # q2 is accepting but unreachable, q0/q1 can’t reach it → all dead
    assert find_dead_states(dfa) == {"q0", "q1", "q2"}

# ───────────────────────────────
# 🔹 Testing Finding Indistinguishable States
# ───────────────────────────────


def _as_set_of_fsets(groups: list[set[str]]) -> set[frozenset[str]]:
    """Helper to make assertions order-agnostic."""
    return {frozenset(g) for g in groups}


# ───────────────────────────────
# 🔹 1) DFA: two states share identical rows → same group
# ───────────────────────────────
def test_group_indistinguishable_states_dfa_row_collapse():
    dfa = make_dfa(
        Q={"q0", "q1", "q2"},
        Σ={"a", "b"},
        δ={
            ("q0", "a"): "q1",
            ("q0", "b"): "q2",
            ("q1", "a"): "q0",
            ("q1", "b"): "q0",
            ("q2", "a"): "q0",
            ("q2", "b"): "q0",
        },
        q0="q0",
        F={"q0"},
    )
    groups = group_indistinguishable_states(dfa)
    expected = _as_set_of_fsets([{"q0"}, {"q1", "q2"}])
    assert groups == expected


# ───────────────────────────────
# 🔹 2) DFA: all rows distinct → all singleton groups
# ───────────────────────────────
def test_group_indistinguishable_states_dfa_all_distinct():
    dfa = make_dfa(
        Q={"s0", "s1", "s2"},
        Σ={"a"},
        δ={
            ("s0", "a"): "s1",
            ("s1", "a"): "s2",
            ("s2", "a"): "s2",
        },
        q0="s0",
        F={"s2"},
    )
    groups = group_indistinguishable_states(dfa)
    expected = _as_set_of_fsets([{"s0"}, {"s1"}, {"s2"}])
    assert groups == expected


# ───────────────────────────────
# 🔹 3) NFA: identical rows incl. ε → same group
# ───────────────────────────────
def test_group_indistinguishable_states_nfa_with_epsilon_collapse():
    nfa = make_nfa(
        Q={"p0", "p1", "p2"},
        Σ={"a"},
        δ={
            ("p0", Epsilon): {"p1"},          # ε
            ("p0", "a"): {"p1"},
            ("p1", Epsilon): {"p0"},          # ε
            ("p1", "a"): {"p0", "p1"},
            ("p2", Epsilon): {"p0"},          # ε
            ("p2", "a"): {"p0", "p1"},   # identical to p1
        },
        q0="p0",
        F={"p0"},
    )
    groups = group_indistinguishable_states(nfa)
    expected = _as_set_of_fsets([{"p0"}, {"p1", "p2"}])
    assert groups == expected


# ───────────────────────────────
# 🔹 4) NFA: ε differs → separate groups
# ───────────────────────────────
def test_group_indistinguishable_states_nfa_epsilon_differs():
    nfa = make_nfa(
        Q={"u0", "u1"},
        Σ={"a"},
        δ={
            ("u0", Epsilon): {"u1"},      # ε present here only
            ("u0", "a"): {"u0"},
            ("u1", "a"): {"u0"},
            # ("u1", ""): ∅
        },
        q0="u0",
        F=set(),
    )
    groups = group_indistinguishable_states(nfa)
    expected = _as_set_of_fsets([{"u0"}, {"u1"}])
    assert groups == expected


# ───────────────────────────────
# 🔹 5) DFA: empty alphabet → all rows identical → one big group
# ───────────────────────────────
def test_group_indistinguishable_states_empty_alphabet():
    dfa = make_dfa(
        Q={"x", "y", "z"},
        Σ=set(),
        δ={},
        q0="x",
        F=set(),
    )
    groups = group_indistinguishable_states(dfa)
    expected = _as_set_of_fsets([{"x", "y", "z"}])
    assert groups == expected


# ───────────────────────────────
# 🔹 6) DFA: two sinks with the SAME targets → same group
# ───────────────────────────────
def test_group_indistinguishable_states_two_sinks_same_targets():
    dfa = make_dfa(
        Q={"A", "B", "C", "D"},
        Σ={"a"},
        δ={
            ("A", "a"): "B",
            ("B", "a"): "D",
            ("C", "a"): "D",   # identical row to B
            ("D", "a"): "D",
        },
        q0="A",
        F=set(),
    )
    groups = group_indistinguishable_states(dfa)
    expected = _as_set_of_fsets([{"A"}, {"B", "C", "D"}])
    assert groups == expected

# ───────────────────────────────
# 🔹 Testing Minimize function
# ───────────────────────────────

# ───────────────────────────────
# 🔹 1) Remove unreachable state in DFA
# ───────────────────────────────


def test_minimize_removes_unreachable_dfa_state():
    dfa = make_dfa(
        Q={"q0", "q1", "q2"},
        Σ={"a"},
        δ={
            ("q0", "a"): "q1",
            ("q1", "a"): "q1",
            ("q2", "a"): "q2",
        },
        q0="q0",
        F={"q1"},
    )
    m = minimize(dfa)
    assert m.Q == {"q0", "q1"}
    assert m.F == {"q1"}


# ───────────────────────────────
# 🔹 2) Remove dead branch in NFA
# ───────────────────────────────
def test_minimize_removes_dead_branch_in_nfa():
    nfa = make_nfa(
        Q={"q0", "q1", "q2"},
        Σ={"a"},
        δ={
            ("q0", "a"): {"q1", "q2"},
            ("q1", "a"): {"q1"},
            # q2 has no path to acceptance
        },
        q0="q0",
        F={"q1"},
    )
    m = minimize(nfa)
    assert m.Q == {"q0", "q1"}
    assert m.F == {"q1"}


# ───────────────────────────────
# 🔹 3) Preserve q0 even if all states are dead
# ───────────────────────────────
def test_minimize_preserves_q0_even_if_dead():
    dfa = make_dfa(
        Q={"x", "y"},
        Σ=set(),
        δ={},
        q0="x",
        F=set(),
    )
    m = minimize(dfa)
    assert m.Q == {"x"}   # only start state remains
    assert m.F == set()
    assert m.δ == {}      # with Σ empty, totality holds with no transitions

# ───────────────────────────────
# 🔹 4) Unreachable accepting state is removed
# ───────────────────────────────


def test_minimize_preserves_q0_even_if_dead_with_sink():
    dfa = make_dfa(
        Q={"x", "y"},
        Σ={"a"},
        δ={("x", "a"): "y", ("y", "a"): "x"},
        q0="x",
        F=set(),
    )
    m = minimize(dfa)
    # expect a canonical sink ensuring totality
    assert "x" in m.Q
    assert any(s.startswith("q_sink")
               for s in m.Q)  # or check exact name if you fixed it
    sink = next(s for s in m.Q if s != "x")
    assert m.F == set()
    assert m.δ[("x", "a")] == sink
    assert m.δ[(sink, "a")] == sink


# ───────────────────────────────
# 🔹 5) Already-minimal DFA stays the same
# ───────────────────────────────
def test_minimize_already_minimal_returns_equivalent_structure():
    dfa = make_dfa(
        Q={"s0", "s1"},
        Σ={"a"},
        δ={
            ("s0", "a"): "s1",
            ("s1", "a"): "s0",
        },
        q0="s0",
        F={"s0", "s1"},
    )
    m = minimize(dfa)
    assert m.Q == {"s0", "s1"}
    assert m.F == {"s0", "s1"}


# ───────────────────────────────
# 🔹 6) NFA with epsilon paths remains unchanged
# ───────────────────────────────
def test_minimize_nfa_with_epsilon_paths():
    nfa = make_nfa(
        Q={"p0", "p1", "p2"},
        Σ={"a"},
        δ={
            ("p0", Epsilon): {"p1"},     # ε-transition
            ("p1", "a"): {"p2"},
            ("p2", "a"): {"p2"},
        },
        q0="p0",
        F={"p2"},
    )
    m = minimize(nfa)
    assert m.Q == {"p0", "p1", "p2"}
    assert m.F == {"p2"}


# ───────────────────────────────
# 🔹 7) Multiple disconnected components: keep only live component (and q0 if needed)
# ───────────────────────────────
def test_minimize_multiple_disconnected_components():
    dfa = make_dfa(
        Q={"A", "B", "C", "D"},
        Σ={"a"},
        δ={
            ("A", "a"): "B",
            ("B", "a"): "A",
            ("C", "a"): "D",
            ("D", "a"): "C",
        },
        q0="A",
        F={"B"},
    )
    m = minimize(dfa)
    assert m.Q == {"A", "B"}
    assert m.F == {"B"}

# ───────────────────────────────
# 🔹 8) DFA: Merge equivalent non-accepting sink states (lexicographic keeper)
# ───────────────────────────────


def test_minimize_dfa_merges_equivalent_dead_sinks_with_sink():
    dfa = make_dfa(
        Q={"q0", "qd1", "qd2"},
        Σ={"a", "b"},
        δ={
            ("q0", "a"): "qd1",
            ("q0", "b"): "qd2",
            ("qd1", "a"): "qd1",
            ("qd1", "b"): "qd1",
            ("qd2", "a"): "qd2",
            ("qd2", "b"): "qd2",
        },
        q0="q0",
        F=set(),
    )
    m = minimize(dfa)

    # q0 plus exactly one sink state remains
    assert len(m.Q) == 2 and "q0" in m.Q
    sink = next(s for s in m.Q if s != "q0")

    assert m.F == set()
    # q0 must route to sink on all symbols; sink self-loops to stay total
    assert m.δ[("q0", "a")] == sink
    assert m.δ[("q0", "b")] == sink
    assert m.δ[(sink, "a")] == sink
    assert m.δ[(sink, "b")] == sink


# ───────────────────────────────
# 🔹 9) DFA: Merge equivalent accepting sinks (lexicographic keeper)
# ───────────────────────────────
def test_minimize_dfa_merges_equivalent_accepting_sinks():
    dfa = make_dfa(
        Q={"q0", "qf1", "qf2"},
        Σ={"x"},
        δ={
            ("q0", "x"): "qf1",
            ("qf1", "x"): "qf1",
            ("qf2", "x"): "qf2",
        },
        q0="q0",
        F={"qf1", "qf2"},
    )
    m = minimize(dfa)
    # Both accepting loops are equivalent; keep lexicographically first "qf1"
    assert m.Q == {"q0", "qf1"}
    assert m.F == {"qf1"}
    assert m.δ[("q0", "x")] == "qf1"


# ───────────────────────────────
# 🔹 10) DFA: q0 merges with an equivalent state (q0 must be retained)
# ───────────────────────────────
def test_minimize_dfa_q0_retained_when_equivalent():
    dfa = make_dfa(
        Q={"q0", "s"},
        Σ={"a"},
        δ={
            ("q0", "a"): "q0",
            ("s", "a"): "s",  # identical behavior, non-accepting
        },
        q0="q0",
        F=set(),
    )
    m = minimize(dfa)
    assert m.Q == {"q0"}
    assert m.F == set()
    # No stray "s" in transitions
    assert set(k[0] for k in m.δ.keys()) == {"q0"}
    assert set(m.δ.values()) == {"q0"}


# ───────────────────────────────
# 🔹 11) DFA: Idempotence (minimize twice == once)
# ───────────────────────────────
def test_minimize_dfa_idempotent():
    dfa = make_dfa(
        Q={"q0", "a1", "a2"},
        Σ={"a"},
        δ={
            ("q0", "a"): "a1",
            ("a1", "a"): "a1",
            ("a2", "a"): "a2",
        },
        q0="q0",
        F={"a1", "a2"},
    )
    m1 = minimize(dfa)
    m2 = minimize(m1)
    assert m1.Q == m2.Q
    assert m1.F == m2.F
    assert m1.δ == m2.δ


# ───────────────────────────────
# 🔹 12) NFA: Drop transitions that only led to pruned dead states
# ───────────────────────────────
def test_minimize_nfa_drops_edges_to_removed_states():
    nfa = make_nfa(
        Q={"q0", "alive", "dead"},
        Σ={"a"},
        δ={
            ("q0", "a"): {"dead"},     # this edge should vanish after prune
            ("alive", "a"): {"alive"},  # only live component
        },
        q0="alive",
        F={"alive"},
    )
    m = minimize(nfa)
    # "dead" pruned; q0 was unreachable and not q0 of the machine, so removed
    assert "dead" not in m.Q
    # Ensure no δ entry remains that points to an empty set; key should be gone
    assert ("q0", "a") not in m.δ  # because "q0" itself should be gone
    # Only the live self-loop remains
    assert ("alive", "a") in m.δ and m.δ[(
        "alive", "a")] == frozenset({"alive"})


# ───────────────────────────────
# 🔹 13) DFA: Unreachable non-q0 states removed even if accepting
# ───────────────────────────────
def test_minimize_dfa_unreachable_accepting_removed_but_q0_kept_if_isolated():
    dfa = make_dfa(
        Q={"q0", "iso"},
        Σ=set(),
        δ={
            # q0 has no outgoing edges; iso is isolated & accepting
        },
        q0="q0",
        F={"iso"},
    )
    m = minimize(dfa)
    assert m.Q == {"q0"}
    assert m.F == set()
    assert m.δ == {}


# ───────────────────────────────
# 🔹 14) DFA: Multiple symbols, merge equivalent middles and remap both symbols
# ───────────────────────────────
def test_minimize_dfa_multisymbol_remap_after_merge():
    dfa = make_dfa(
        Q={"q0", "m1", "m2", "acc"},
        Σ={"a", "b"},
        δ={
            ("q0", "a"): "m1",
            ("q0", "b"): "m2",
            ("m1", "a"): "acc", ("m1", "b"): "acc",
            ("m2", "a"): "acc", ("m2", "b"): "acc",
            ("acc", "a"): "acc", ("acc", "b"): "acc",
        },
        q0="q0",
        F={"acc"},
    )
    m = minimize(dfa)
    # m1 and m2 are equivalent; keep "m1"
    assert "m1" in m.Q and "m2" not in m.Q
    assert m.F == {"acc"}
    assert m.δ[("q0", "a")] == "m1"
    assert m.δ[("q0", "b")] == "m1"
    assert m.δ[("m1", "a")] == "acc"
    assert m.δ[("m1", "b")] == "acc"


# ───────────────────────────────
# 🔹 15) NFA: Idempotence (minimize twice == once)
# ───────────────────────────────
def test_minimize_nfa_idempotent():
    nfa = make_nfa(
        Q={"q0", "x", "y"},
        Σ={"a"},
        δ={
            ("q0", "a"): {"x", "y"},
            ("x", "a"): {"x"},
            ("y", "a"): {"y"},
        },
        q0="q0",
        F=set(),  # x and y are equivalent non-accepting loops
    )
    m1 = minimize(nfa)
    m2 = minimize(m1)
    assert m1.Q == m2.Q
    assert m1.F == m2.F
    assert m1.δ == m2.δ
