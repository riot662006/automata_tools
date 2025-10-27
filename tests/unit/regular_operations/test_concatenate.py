from automata.automaton import Epsilon
from automata.operations import concatenate
from tests.conftest import make_nfa


# ───────────────────────────────
# 🔹 1) Basic concat: (a+) · (b+)
# ───────────────────────────────
def test_concatenate_basic_structure_and_prefixing():
    # nfa1 accepts a+ : q0 -a-> q1, q1 -a-> q1, F={q1}
    nfa1 = make_nfa(
        Q={"q0", "q1"},
        Σ={"a"},
        δ={
            ("q0", "a"): {"q1"},
            ("q1", "a"): {"q1"},
        },
        q0="q0",
        F={"q1"},
    )
    # nfa2 accepts b+ : p0 -b-> p1, p1 -b-> p1, F={p1}
    nfa2 = make_nfa(
        Q={"p0", "p1"},
        Σ={"b"},
        δ={
            ("p0", "b"): {"p1"},
            ("p1", "b"): {"p1"},
        },
        q0="p0",
        F={"p1"},
    )

    u = concatenate(nfa1, nfa2, should_minimize=False)

    # Alphabet is union
    assert u.Σ == {"a", "b"}

    # Start & prefixes
    assert u.q0 == "nfa1_q0"
    assert "nfa1_q0" in u.Q and "nfa1_q1" in u.Q
    assert "nfa2_p0" in u.Q and "nfa2_p1" in u.Q

    # Accepting set = prefixed accepts of nfa2
    assert u.F == {"nfa2_p1"}

    # ε-edges from every nfa1 accepting state to nfa2 start
    assert u.δ[("nfa1_q1", Epsilon)] == frozenset({"nfa2_p0"})

    # Transitions copied with prefixes (no cross-prefix leakage)
    assert u.δ[("nfa1_q0", "a")] == frozenset({"nfa1_q1"})
    assert u.δ[("nfa1_q1", "a")] == frozenset({"nfa1_q1"})
    assert ("nfa1_q0", "b") not in u.δ and ("nfa1_q1", "b") not in u.δ

    assert u.δ[("nfa2_p0", "b")] == frozenset({"nfa2_p1"})
    assert u.δ[("nfa2_p1", "b")] == frozenset({"nfa2_p1"})
    assert ("nfa2_p0", "a") not in u.δ and ("nfa2_p1", "a") not in u.δ


# ───────────────────────────────
# 🔹 2) If nfa1 accepts ε (q0∈F), concat behaves like nfa2
# ───────────────────────────────
def test_concatenate_preserves_empty_prefix_jump():
    # nfa1 accepts ε (start is accepting)
    nfa1 = make_nfa(
        Q={"s"},
        Σ=set(),
        δ={},
        q0="s",
        F={"s"},
    )
    # nfa2 = a+
    nfa2 = make_nfa(
        Q={"t0", "t1"},
        Σ={"a"},
        δ={
            ("t0", "a"): {"t1"},
            ("t1", "a"): {"t1"},
        },
        q0="t0",
        F={"t1"},
    )

    u = concatenate(nfa1, nfa2, should_minimize=False)

    # Start is still in the nfa1 prefix, but ε-edge bridges immediately to nfa2 start
    assert u.q0 == "nfa1_s"
    assert u.δ[("nfa1_s", Epsilon)] == frozenset({"nfa2_t0"})
    assert u.F == {"nfa2_t1"}


# ───────────────────────────────
# 🔹 3) With minimization ON: if nfa2 accepts ∅, whole concat accepts ∅
#     (simple trim leaves only the start state with no transitions)
# ───────────────────────────────
def test_concatenate_minimize_when_second_is_empty_language():
    # nfa1 is non-empty language (a+)
    nfa1 = make_nfa(
        Q={"q0", "q1"},
        Σ={"a"},
        δ={("q0", "a"): {"q1"}, ("q1", "a"): {"q1"}},
        q0="q0",
        F={"q1"},
    )
    # nfa2 accepts nothing (no accepting states)
    nfa2 = make_nfa(
        Q={"p0"},
        Σ={"b"},
        δ={},   # no path to acceptance
        q0="p0",
        F=set(),
    )

    u = concatenate(nfa1, nfa2, should_minimize=True)

    # Minimizer should prune everything except start; no paths to acceptance remain
    assert u.Q == {"nfa1_q0"}
    assert u.F == set()
    assert u.δ == {}


# ───────────────────────────────
# 🔹 4) Multiple accepting states in nfa1 → each gets ε to nfa2 start
# ───────────────────────────────
def test_concatenate_multiple_accepting_states_bridge_each():
    # nfa1 with two accepting states on 'a'
    nfa1 = make_nfa(
        Q={"q0", "f1", "f2"},
        Σ={"a"},
        δ={
            ("q0", "a"): {"f1", "f2"},
            ("f1", "a"): {"f1"},
            ("f2", "a"): {"f2"},
        },
        q0="q0",
        F={"f1", "f2"},
    )
    # nfa2 = b+
    nfa2 = make_nfa(
        Q={"p0", "p1"},
        Σ={"b"},
        δ={("p0", "b"): {"p1"}, ("p1", "b"): {"p1"}},
        q0="p0",
        F={"p1"},
    )

    u = concatenate(nfa1, nfa2, should_minimize=False)

    # Both accepting states should have ε-edges to nfa2 start
    assert u.δ[("nfa1_f1", Epsilon)] == frozenset({"nfa2_p0"})
    assert u.δ[("nfa1_f2", Epsilon)] == frozenset({"nfa2_p0"})

    # Accepting set as defined: only the nfa2 accepts
    assert u.F == {"nfa2_p1"}
