from automata.automaton import Epsilon
from automata.dfa import DFA
from automata.operation_funcs import convert_nfa_to_dfa
from tests.conftest import make_nfa


def _is_total_dfa(dfa: DFA):
    for q in dfa.Q:
        for a in dfa.Σ:
            if (q, a) not in dfa.δ:
                return False
    return True


# ───────────────────────────────
# 🔹 1) a+  → DFA with start then accepting loop
# ───────────────────────────────
def test_convert_simple_a_plus():
    # NFA for a+ : q0 -a-> q1 ; q1 -a-> q1 ; F={q1}
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

    dfa = convert_nfa_to_dfa(nfa)

    # start state's name is "q_start" per your function
    assert dfa.q0 == "q_start"
    # accepting sets are exactly those subsets that contain q1
    assert any("q_" in s or s == "q_start" for s in dfa.Q)
    assert dfa.F  # not empty
    # From start on 'a' we reach an accepting state; staying on 'a' keeps accepting
    s1 = dfa.δ[(dfa.q0, "a")]
    assert s1 in dfa.F
    s2 = dfa.δ[(s1, "a")]
    assert s2 in dfa.F


# ───────────────────────────────
# 🔹 2) ε-transition at start: q0 --ε--> q1, with q1 accepting (accepts ε)
#     ε-closure({q0}) includes q1 ⇒ q_start ∈ F, self-loop on 'a'
# ───────────────────────────────
def test_convert_epsilon_start_accepts_epsilon():
    nfa = make_nfa(
        Q={"p0", "p1"},
        Σ={"a"},
        δ={
            ("p0", Epsilon): {"p1"},
            ("p1", "a"): {"p1"},
        },
        q0="p0",
        F={"p1"},
    )

    dfa = convert_nfa_to_dfa(nfa)
    assert _is_total_dfa(dfa)

    # ε-closure of q0 hits p1, so start is accepting
    assert dfa.q0 in dfa.F
    # On 'a' we should remain accepting
    s1 = dfa.δ[(dfa.q0, "a")]
    assert s1 in dfa.F


# ───────────────────────────────
# 🔹 3) Empty language: no accepting states in NFA
#     DFA should also have empty F, include the ∅ subset, and be total.
# ───────────────────────────────
def test_convert_empty_language_has_empty_subset_and_no_F():
    nfa = make_nfa(
        Q={"x0"},
        Σ={"a", "b"},
        δ={},              # no transitions, no accepting
        q0="x0",
        F=set(),
    )

    dfa = convert_nfa_to_dfa(nfa)
    assert _is_total_dfa(dfa)
    assert dfa.F == set()

    # The empty subset must be one of the constructed states; find it by behavior:
    # From any state on any symbol, if there is no reachable NFA state, we end up
    # in a unique DFA state that loops to itself on all symbols.
    # (Because your subset construction includes ∅ in state_map.)
    # We'll detect a state that is a sink for all symbols.
    empty_like = [q for q in dfa.Q if all(dfa.δ[(q, a)] == q for a in dfa.Σ)]
    assert empty_like, "Expected a DFA state representing the empty subset (sink)."


# ───────────────────────────────
# 🔹 4) Multi-symbol NFA with branching: structural sanity + totality
#     NFA: from s, on 'a' go to A; on 'b' go to B; A/B self-loop on their symbols.
# ───────────────────────────────
def test_convert_multisymbol_branching_sanity():
    nfa = make_nfa(
        Q={"s", "A", "B"},
        Σ={"a", "b"},
        δ={
            ("s", "a"): {"A"},
            ("s", "b"): {"B"},
            ("A", "a"): {"A"},
            ("B", "b"): {"B"},
        },
        q0="s",
        F={"A", "B"},
    )

    dfa = convert_nfa_to_dfa(nfa)
    assert _is_total_dfa(dfa)

    # From start on 'a' we reach some accepting state; on 'b' reach (maybe different) accepting
    qa = dfa.δ[(dfa.q0, "a")]
    qb = dfa.δ[(dfa.q0, "b")]
    assert qa in dfa.F
    assert qb in dfa.F
    # And staying on their symbols keeps them in acceptance
    assert dfa.δ[(qa, "a")] in dfa.F
    assert dfa.δ[(qb, "b")] in dfa.F


# ───────────────────────────────
# 🔹 5) Overlapping transitions (nondet): union of next-sets is respected
#     NFA: s -a-> {x, y}; x -a-> x ; y -a-> y ; F={y}
#     DFA on 'a' from start must reach subset containing y ⇒ accepting.
# ───────────────────────────────
def test_convert_nondet_union_of_moves():
    nfa = make_nfa(
        Q={"s", "x", "y"},
        Σ={"a"},
        δ={
            ("s", "a"): {"x", "y"},
            ("x", "a"): {"x"},
            ("y", "a"): {"y"},
        },
        q0="s",
        F={"y"},
    )

    dfa = convert_nfa_to_dfa(nfa)
    assert _is_total_dfa(dfa)

    # From start on 'a' must be accepting because subset includes 'y'
    s1 = dfa.δ[(dfa.q0, "a")]
    assert s1 in dfa.F
