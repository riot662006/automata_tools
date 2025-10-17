from automata.automaton import Epsilon
from automata.operation_funcs import union
from tests.conftest import make_nfa

# ───────────────────────────────
# 🔹 1) Basic union: disjoint alphabets (a+) ∪ (b+)
# ───────────────────────────────


def test_union_basic_structure_and_prefixing():
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

    u = union(nfa1, nfa2)

    # Alphabet is union
    assert u.Σ == {"a", "b"}

    # Start & prefixes exist
    assert "q_start" in u.Q
    assert "nfa1_q0" in u.Q and "nfa1_q1" in u.Q
    assert "nfa2_p0" in u.Q and "nfa2_p1" in u.Q

    # ε-edges from union start to both original starts
    assert ("q_start", Epsilon) in u.δ
    assert u.δ[("q_start", Epsilon)] == frozenset({"nfa1_q0", "nfa2_p0"})

    # Accepting set mapped with prefixes
    assert u.F == {"nfa1_q1", "nfa2_p1"}

    # Transitions copied with proper prefixes (no cross-prefix leakage)
    assert u.δ[("nfa1_q0", "a")] == frozenset({"nfa1_q1"})
    assert u.δ[("nfa1_q1", "a")] == frozenset({"nfa1_q1"})
    assert ("nfa1_q0", "b") not in u.δ and ("nfa1_q1", "b") not in u.δ

    assert u.δ[("nfa2_p0", "b")] == frozenset({"nfa2_p1"})
    assert u.δ[("nfa2_p1", "b")] == frozenset({"nfa2_p1"})
    assert ("nfa2_p0", "a") not in u.δ and ("nfa2_p1", "a") not in u.δ


# ───────────────────────────────
# 🔹 2) Union preserves ε-acceptance when an operand accepts ε
#     (nfa1 accepts ε via q0∈F; nfa2 accepts a+)
# ───────────────────────────────
def test_union_preserves_empty_string_acceptance_via_epsilon():
    nfa1 = make_nfa(
        Q={"s"},
        Σ=set(),
        δ={},            # no edges; start is accepting => accepts ε
        q0="s",
        F={"s"},
    )
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

    u = union(nfa1, nfa2)

    # Accepting set includes prefixed accepting start of nfa1
    assert "nfa1_s" in u.F

    # ε-link exists to both starts, enabling ε to reach an accepting state
    assert u.δ[("q_start", Epsilon)] == frozenset({"nfa1_s", "nfa2_t0"})


# ───────────────────────────────
# 🔹 3) Union with one empty-language operand (no accepting states)
#     Should behave like the other operand; minimize may prune the dead side.
# ───────────────────────────────
def test_union_with_empty_language_operand():
    # nfa1 accepts nothing
    nfa1 = make_nfa(
        Q={"x0"},
        Σ={"a"},
        δ={},            # no path to acceptance
        q0="x0",
        F=set(),
    )
    # nfa2 accepts b+
    nfa2 = make_nfa(
        Q={"y0", "y1"},
        Σ={"b"},
        δ={
            ("y0", "b"): {"y1"},
            ("y1", "b"): {"y1"},
        },
        q0="y0",
        F={"y1"},
    )

    u = union(nfa1, nfa2, should_minimize=False)

    # Alphabet is union even if one side is empty-language
    assert u.Σ == {"a", "b"}

    # ε-link from union start always points to both prefixed starts
    assert ("q_start", Epsilon) in u.δ
    assert u.δ[("q_start", Epsilon)] == frozenset({"nfa1_x0", "nfa2_y0"})

    # Accepting set mirrors the non-empty operand
    assert u.F == {"nfa2_y1"}

    # Ensure nfa2 transitions survived with proper prefix
    assert u.δ[("nfa2_y0", "b")] == frozenset({"nfa2_y1"})
    assert u.δ[("nfa2_y1", "b")] == frozenset({"nfa2_y1"})

    # No stray "a" transitions were invented
    assert ("nfa2_y0", "a") not in u.δ and ("nfa2_y1", "a") not in u.δ


# ───────────────────────────────
# 🔹 4) Σ union with overlap; transitions for shared symbols kept separate
# ───────────────────────────────
def test_union_overlapping_alphabet_no_cross_wiring():
    # nfa1: on 'a' go to f1 (accept), loop on 'a'
    nfa1 = make_nfa(
        Q={"q0", "f1"},
        Σ={"a"},
        δ={("q0", "a"): {"f1"}, ("f1", "a"): {"f1"}},
        q0="q0",
        F={"f1"},
    )
    # nfa2: also uses 'a', but different structure
    nfa2 = make_nfa(
        Q={"p0", "p1"},
        Σ={"a"},
        δ={("p0", "a"): {"p0", "p1"}, ("p1", "a"): {"p1"}},
        q0="p0",
        F={"p1"},
    )

    u = union(nfa1, nfa2)

    # Both prefixed structures present and independent
    assert u.δ[("nfa1_q0", "a")] == frozenset({"nfa1_f1"})
    assert u.δ[("nfa1_f1", "a")] == frozenset({"nfa1_f1"})

    assert u.δ[("nfa2_p0", "a")] == frozenset({"nfa2_p0", "nfa2_p1"})
    assert u.δ[("nfa2_p1", "a")] == frozenset({"nfa2_p1"})

    # No cross-prefix destinations
    assert "nfa2_p0" not in u.δ[("nfa1_q0", "a")]
    assert "nfa1_f1" not in u.δ[("nfa2_p0", "a")]

# ───────────────────────────────
# 🔹 5) With minimization ON (default): dead operand gets trimmed
#     nfa1 accepts ∅, nfa2 accepts b+  →  nfa1_* states pruned
# ───────────────────────────────


def test_union_trims_dead_operand_when_minimized():
    nfa1 = make_nfa(
        Q={"x0"},
        Σ={"a"},
        δ={},            # no path to acceptance
        q0="x0",
        F=set(),
    )
    nfa2 = make_nfa(
        Q={"y0", "y1"},
        Σ={"b"},
        δ={
            ("y0", "b"): {"y1"},
            ("y1", "b"): {"y1"},
        },
        q0="y0",
        F={"y1"},
    )

    u = union(nfa1, nfa2)  # default: should_minimize=True

    # All nfa1_* states should be gone after trim
    assert all(not s.startswith("nfa1_") for s in u.Q)

    # ε from start should now only target the live side's start
    assert ("q_start", Epsilon) in u.δ
    assert u.δ[("q_start", Epsilon)] == frozenset({"nfa2_y0"})

    # Language preserved: the b+ structure is intact
    assert u.F == {"nfa2_y1"}
    assert u.δ[("nfa2_y0", "b")] == frozenset({"nfa2_y1"})
    assert u.δ[("nfa2_y1", "b")] == frozenset({"nfa2_y1"})


# ───────────────────────────────
# 🔹 6) With minimization ON: both operands empty-language → only start remains
# ───────────────────────────────
def test_union_minimize_both_empty_language_keeps_only_start():
    nfa1 = make_nfa(Q={"a0"}, Σ={"x"}, δ={}, q0="a0", F=set())
    nfa2 = make_nfa(Q={"b0"}, Σ={"y"}, δ={}, q0="b0", F=set())

    u = union(nfa1, nfa2)  # minimize=True

    # Minimizer preserves q0 but prunes dead components and dead ε-edges
    assert u.Q == {"q_start"}
    assert u.F == set()
    assert u.δ == {}

# ───────────────────────────────
# 🔹 7) With minimization ON: dead operand is trimmed (simple prune)
#     nfa1 accepts ∅, nfa2 accepts b+ → only the live side remains referenced
# ───────────────────────────────


def test_union_trims_dead_operand_minimize_simple():
    nfa1 = make_nfa(
        Q={"x0"},
        Σ={"a"},
        δ={},            # no path to acceptance
        q0="x0",
        F=set(),
    )
    nfa2 = make_nfa(
        Q={"y0", "y1"},
        Σ={"b"},
        δ={
            ("y0", "b"): {"y1"},
            ("y1", "b"): {"y1"},
        },
        q0="y0",
        F={"y1"},
    )

    u = union(nfa1, nfa2)  # default should_minimize=True

    # All nfa1_* states are pruned (dead component)
    assert all(not s.startswith("nfa1_") for s in u.Q)

    # ε from union start only points to live start
    assert ("q_start", Epsilon) in u.δ
    assert u.δ[("q_start", Epsilon)] == frozenset({"nfa2_y0"})

    # Live side intact
    assert u.F == {"nfa2_y1"}
    assert u.δ[("nfa2_y0", "b")] == frozenset({"nfa2_y1"})
    assert u.δ[("nfa2_y1", "b")] == frozenset({"nfa2_y1"})


# ───────────────────────────────
# 🔹 8) No cross-operand merges even if shapes match
#     (your minimizer only merges when "nexts are identical" *within the same prefix graph*).
# ───────────────────────────────
def test_union_no_cross_operand_merge_when_shapes_match():
    # Both NFAs have an accepting self-loop on 'a', but they are in different prefixed subgraphs
    nfa1 = make_nfa(
        Q={"q0", "acc"},
        Σ={"a"},
        δ={("q0", "a"): {"acc"}, ("acc", "a"): {"acc"}},
        q0="q0",
        F={"acc"},
    )
    nfa2 = make_nfa(
        Q={"p0", "acc"},
        Σ={"a"},
        δ={("p0", "a"): {"acc"}, ("acc", "a"): {"acc"}},
        q0="p0",
        F={"acc"},
    )

    u = union(nfa1, nfa2)  # minimize=True

    # Because destinations are prefixed differently, "nexts" are not identical across prefixes,
    # so a simple equivalence check should NOT merge them.
    assert "nfa1_acc" in u.Q
    assert "nfa2_acc" in u.Q
    assert u.F == {"nfa1_acc", "nfa2_acc"}

    # Each side's edges stay within its prefix
    assert u.δ[("nfa1_q0", "a")] == frozenset({"nfa1_acc"})
    assert u.δ[("nfa1_acc", "a")] == frozenset({"nfa1_acc"})
    assert u.δ[("nfa2_p0", "a")] == frozenset({"nfa2_acc"})
    assert u.δ[("nfa2_acc", "a")] == frozenset({"nfa2_acc"})
