from automata.automaton import Epsilon
from automata.sampler import Sampler
from tests.conftest import make_dfa, make_nfa


# ───────────────────────────────
# 🔹 1) DFA a+ : ordering, determinism, totality-friendly
# ───────────────────────────────
def test_sampler_dfa_a_plus_order_and_values():
    dfa = make_dfa(
        Q={"q0", "q1"},
        Σ={"a"},
        δ={
            ("q0", "a"): "q1",
            ("q1", "a"): "q1",
        },
        q0="q0",
        F={"q1"},
    )
    s = Sampler(dfa)
    out = s.sample(max_samples=6, max_depth=6)
    assert out == ["a", "aa", "aaa", "aaaa", "aaaaa", "aaaaaa"]


# ───────────────────────────────
# 🔹 2) NFA with ε at start (accepts ε): "" must appear
# ───────────────────────────────
def test_sampler_nfa_epsilon_accepts_empty_string():
    nfa = make_nfa(
        Q={"s"},
        Σ=set(),
        δ={},          # no moves; start is accepting
        q0="s",
        F={"s"},
    )
    s = Sampler(nfa)
    out = s.sample(max_samples=3, max_depth=3)
    assert "" in out
    # Only ε is possible here
    assert out == [""]


# ───────────────────────────────
# 🔹 3) max_samples is respected (cap)
# ───────────────────────────────
def test_sampler_respects_max_samples_cap():
    dfa = make_dfa(
        Q={"q0", "q1"},
        Σ={"a"},
        δ={("q0", "a"): "q1", ("q1", "a"): "q1"},
        q0="q0",
        F={"q1"},
    )
    out = Sampler(dfa).sample(max_samples=2, max_depth=10)
    assert out == ["a", "aa"]


# ───────────────────────────────
# 🔹 4) max_depth limits growth (only shortest words discovered)
#     Depth definition: root depth=1 (q0), after one symbol depth=2, etc.
# ───────────────────────────────
def test_sampler_respects_max_depth():
    dfa = make_dfa(
        Q={"q0", "q1"},
        Σ={"a"},
        δ={("q0", "a"): "q1", ("q1", "a"): "q1"},
        q0="q0",
        F={"q1"},
    )
    # With max_depth=2, only one symbol from start is explored
    out = Sampler(dfa).sample(max_samples=10, max_depth=2)
    assert out == ["a", "aa"]


# ───────────────────────────────
# 🔹 5) Dead-end pruning: words that must pass through a dead sink never appear
#     DFA: 'a' leads toward accept; 'b' goes to dead sink.
# ───────────────────────────────
def test_sampler_prunes_dead_end_states():
    dfa = make_dfa(
        Q={"q0", "acc", "dead"},
        Σ={"a", "b"},
        δ={
            ("q0", "a"): "acc",
            ("q0", "b"): "dead",
            ("acc", "a"): "acc",
            ("acc", "b"): "dead",
            ("dead", "a"): "dead",
            ("dead", "b"): "dead",
        },
        q0="q0",
        F={"acc"},
    )
    # Ask for several samples; none should start with 'b'
    out = Sampler(dfa).sample(max_samples=5, max_depth=5)
    assert all(not w.startswith("b") for w in out)
    # And legal 'a'-strings should be there
    assert out[:2] == ["a", "aa"]


# ───────────────────────────────
# 🔹 6) path_between_exists sanity (reachable vs dead)
# ───────────────────────────────
def test_sampler_path_between_exists():
    dfa = make_dfa(
        Q={"q0", "acc", "dead"},
        Σ={"a", "b"},
        δ={
            ("q0", "a"): "acc",
            ("q0", "b"): "dead",
            ("acc", "a"): "acc",
            ("acc", "b"): "dead",
            ("dead", "a"): "dead",
            ("dead", "b"): "dead",
        },
        q0="q0",
        F={"acc"},
    )
    s = Sampler(dfa)
    assert s.path_between_exists("q0", {"acc"}) is True
    assert s.path_between_exists("dead", {"acc"}) is False


# ───────────────────────────────
# 🔹 7) NFA with ε edges: can produce "", single-symbol, and multi-step words
# ───────────────────────────────
def test_sampler_nfa_with_epsilon_paths_generates_varied_words():
    # NFA: p0 --ε--> p1 ; p1 -a-> p2 ; p2 -a-> p2 ; F={p2}
    nfa = make_nfa(
        Q={"p0", "p1", "p2"},
        Σ={"a"},
        δ={
            ("p0", Epsilon): {"p1"},
            ("p1", "a"): {"p2"},
            ("p2", "a"): {"p2"},
        },
        q0="p0",
        F={"p2"},
    )
    out = Sampler(nfa).sample(max_samples=3, max_depth=5)
    # minimal accepting word "a" (via ε then 'a'), then "aa", "aaa"
    assert out == ["a", "aa", "aaa"]


# ───────────────────────────────
# 🔹 8) Deterministic ordering: sort by (len, lex)
# ───────────────────────────────
def test_sampler_deterministic_sorting():
    # DFA accepting (a|b)+
    dfa = make_dfa(
        Q={"q0", "q1", "dead"},
        Σ={"a", "b"},
        δ={
            ("q0", "a"): "q1", ("q0", "b"): "q1",
            ("q1", "a"): "q1", ("q1", "b"): "q1",
            ("dead", "a"): "dead", ("dead", "b"): "dead",
        },
        q0="q0",
        F={"q1"},
    )
    out = Sampler(dfa).sample(max_samples=6, max_depth=4)
    # Shorter first; among equals, lexicographic: 'a' < 'b' < 'aa' < 'ab' < 'ba' < 'bb'
    assert out == ["a", "b", "aa", "ab", "ba", "bb"]
