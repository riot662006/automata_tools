# tests/test_conversion_with_sampler.py

from automata.automaton import Epsilon
from automata.dfa import DFA
from automata.nfa import NFA
from automata.operation_funcs import convert_nfa_to_dfa
from automata.sampler import Sampler
from tests.conftest import make_nfa


def _samples(auto: DFA | NFA, *, max_samples: int = 12, max_depth: int = 6):
    """Helper: get a set of samples with consistent caps."""
    return set(Sampler(auto).sample(max_samples=max_samples, max_depth=max_depth))


# ───────────────────────────────
# 🔹 1) a+  → languages match
# ───────────────────────────────
def test_convert_a_plus_sampler_equivalence():
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

    nfa_samples = _samples(nfa, max_samples=6, max_depth=6)
    dfa_samples = _samples(dfa, max_samples=6, max_depth=6)

    assert nfa_samples == dfa_samples == {
        "a", "aa", "aaa", "aaaa", "aaaaa", "aaaaaa"}


# ───────────────────────────────
# 🔹 2) ε at start (accepts ε) → start closure respected
# ───────────────────────────────
def test_convert_epsilon_start_sampler_equivalence():
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

    nfa_samples = _samples(nfa, max_samples=5, max_depth=4)
    dfa_samples = _samples(dfa, max_samples=5, max_depth=4)

    # ε should be in both; then "a", "aa", ...
    assert "" in nfa_samples and "" in dfa_samples
    assert nfa_samples == dfa_samples


# ───────────────────────────────
# 🔹 3) Empty language → no samples for either side
# ───────────────────────────────
def test_convert_empty_language_sampler_equivalence():
    nfa = make_nfa(
        Q={"x0"},
        Σ={"a", "b"},
        δ={},          # no transitions, no accepting
        q0="x0",
        F=set(),
    )
    dfa = convert_nfa_to_dfa(nfa)

    assert _samples(nfa, max_samples=10, max_depth=6) == set()
    assert _samples(dfa, max_samples=10, max_depth=6) == set()


# ───────────────────────────────
# 🔹 4) Branching on multiple symbols → union of paths matches
# ───────────────────────────────
def test_convert_multisymbol_branching_sampler_equivalence():
    # From s: on 'a' -> A (acc, loops 'a'); on 'b' -> B (acc, loops 'b')
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

    nfa_samples = _samples(nfa, max_samples=6, max_depth=4)
    dfa_samples = _samples(dfa, max_samples=6, max_depth=4)

    # expected first few (order-agnostic): {"a","b","aa","bb","aaa","bbb"}
    expected = {"a", "b", "aa", "bb", "aaa", "bbb"}
    assert nfa_samples == dfa_samples == expected


# ───────────────────────────────
# 🔹 5) Nondeterministic union of moves → subset construction honored
# ───────────────────────────────
def test_convert_nondet_union_sampler_equivalence():
    # s -a-> {x,y}; x loops 'a' (non-accepting), y loops 'a' (accepting)
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

    nfa_samples = _samples(nfa, max_samples=5, max_depth=5)
    dfa_samples = _samples(dfa, max_samples=5, max_depth=5)

    expected = {"a", "aa", "aaa", "aaaa", "aaaaa"}
    assert nfa_samples == dfa_samples == expected
