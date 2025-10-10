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
        δ={("q0", "a"): "q1", ("q1", "a"): "q1"},
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
        δ={("q0", "a"): "q1", ("q1", "a"): "q1"},
        q0="q0",
        F={"q2"},
    )
    # q2 is accepting but unreachable, q0/q1 can’t reach it → all dead
    assert find_dead_states(dfa) == {"q0", "q1", "q2"}


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
        Σ={"a"},
        δ={
            ("x", "a"): "y",
            ("y", "a"): "x",
        },
        q0="x",
        F=set(),
    )
    m = minimize(dfa)
    assert m.Q == {"x"}   # only start state remains
    assert m.F == set()


# ───────────────────────────────
# 🔹 4) Unreachable accepting state is removed
# ───────────────────────────────
def test_minimize_unreachable_accepting_removed():
    dfa = make_dfa(
        Q={"q0", "q1", "q2"},
        Σ={"a"},
        δ={
            ("q0", "a"): "q1",
            ("q1", "a"): "q1",
            # q2 is isolated and accepting
        },
        q0="q0",
        F={"q2"},
    )
    m = minimize(dfa)
    # After removing dead states (except q0), only q0 should remain
    assert m.Q == {"q0"}
    assert m.F == set()


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