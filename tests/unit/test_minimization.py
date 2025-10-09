from automata.minimization import find_dead_states
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
            ("p0", ""): {"p1"},  # epsilon transition
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
