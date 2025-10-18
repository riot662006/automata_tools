from automata.automaton import Epsilon
from automata.operation_funcs import kleene_star
from tests.conftest import make_nfa


# ───────────────────────────────
# 🔹 1) Basic star on a+ : (a+)*
# ───────────────────────────────
def test_kleene_star_basic_structure_and_prefixing():
    # a+ : q0 -a-> q1, q1 -a-> q1, F={q1}
    nfa = make_nfa(
        Q={"q0", "q1"},
        Σ={"a"},
        δ={
            ("q0", "a"): {"q1"},
            ("q1", "a"): {"q1"},
        },
        q0="q0",
        F={"q1"},
    )

    s = kleene_star(nfa, should_minimize=False)

    # Σ preserved
    assert s.Σ == {"a"}

    # New start and prefixed copies
    assert s.q0 == "q_start"
    assert {"q_start", "nfa_q0", "nfa_q1"}.issubset(s.Q)

    # F includes new start and all prefixed accepts
    assert "q_start" in s.F and "nfa_q1" in s.F

    # ε from new start to original start
    assert s.δ[("q_start", Epsilon)] == frozenset({"nfa_q0"})

    # All original transitions copied with prefix
    assert s.δ[("nfa_q0", "a")] == frozenset({"nfa_q1"})
    assert s.δ[("nfa_q1", "a")] == frozenset({"nfa_q1"})

    # ε back-edges from each accepting state to original start
    assert s.δ[("nfa_q1", Epsilon)] == frozenset({"nfa_q0"})


# ───────────────────────────────
# 🔹 2) Input already accepts ε (q0 ∈ F) → star still has q_start in F
# ───────────────────────────────
def test_kleene_star_when_input_accepts_epsilon():
    # ε-language: start is accepting, no edges
    nfa = make_nfa(
        Q={"s"},
        Σ=set(),
        δ={},
        q0="s",
        F={"s"},
    )

    s = kleene_star(nfa, should_minimize=False)

    # q_start is accepting and ε-edge to nfa_s exists
    assert "q_start" in s.F and "nfa_s" in s.F
    assert s.δ[("q_start", Epsilon)] == frozenset({"nfa_s"})

    # Since q0∈F, star adds ε from nfa_s back to nfa_s (loop via spec)
    assert s.δ[("nfa_s", Epsilon)] == frozenset({"nfa_s"})


# ───────────────────────────────
# 🔹 3) With minimization ON: input has empty language → star collapses to {ε}
#     (only q_start remains, accepting, no edges)
# ───────────────────────────────
def test_kleene_star_minimize_on_empty_language_input():
    # accepts ∅ : no accepting states, no edges
    nfa = make_nfa(
        Q={"x0"},
        Σ={"a"},
        δ={},
        q0="x0",
        F=set(),
    )

    s = kleene_star(nfa, should_minimize=True)

    # Minimizer should trim all dead prefixed states; keep only q_start accepting ε
    assert s.Q == {"q_start"}
    assert s.F == {"q_start"}
    assert s.δ == {}
    # Σ may remain as original Σ or be trimmed by your impl; allow either:
    assert s.Σ == {"a"} or s.Σ == set()


# ───────────────────────────────
# 🔹 4) Multiple accepting states → each gets ε back to start
# ───────────────────────────────
def test_kleene_star_multiple_accepting_states_back_edges():
    nfa = make_nfa(
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

    s = kleene_star(nfa, should_minimize=False)

    # Both accepting states should have ε back to original start
    assert s.δ[("nfa_f1", Epsilon)] == frozenset({"nfa_q0"})
    assert s.δ[("nfa_f2", Epsilon)] == frozenset({"nfa_q0"})

    # F contains q_start and both prefixed accepts
    assert {"q_start", "nfa_f1", "nfa_f2"}.issubset(s.F)


# ───────────────────────────────
# 🔹 5) No cross-symbol leakage; only original alphabet used
# ───────────────────────────────
def test_kleene_star_preserves_alphabet_only():
    nfa = make_nfa(
        Q={"q0", "q1"},
        Σ={"x"},
        δ={("q0", "x"): {"q1"}, ("q1", "x"): {"q1"}},
        q0="q0",
        F={"q1"},
    )

    s = kleene_star(nfa, should_minimize=False)

    assert s.Σ == {"x"}
    # No invented transitions on other symbols
    assert ("nfa_q0", "y") not in s.δ and ("nfa_q1", "y") not in s.δ
