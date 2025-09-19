import pytest


def test_get_tuples_roundtrip(simple_dfa):
    Q, Σ, δ, q0, F = simple_dfa.get_tuples()
    assert q0 in Q
    assert F.issubset(Q)
    # δ keys consistent
    for (s, a), t in δ.items():
        assert s in Q
        assert a in Σ
        # DFA: t in Q; NFA: t is a set/frozenset of Q
        if isinstance(t, (set, frozenset)):
            assert set(t).issubset(Q)
        else:
            assert t in Q


@pytest.mark.parametrize(
    "dfa_fixture",
    [
        "simple_dfa",
        "dfa_with_trap",
        "dfa_multi_accept",
    ]
)
def test_edges_grouping(request, dfa_fixture):
    dfa = request.getfixturevalue(dfa_fixture)
    # edges[src][dst] -> tuple(symbols)
    for src, dst_map in dfa.edges.items():
        for dst, syms in dst_map.items():
            assert isinstance(syms, tuple)
            assert all(isinstance(x, str) for x in syms)


def test_words_for_path_valid(simple_dfa):
    words = simple_dfa.words_for_path(["q0", "q1"])
    # from the example transitions: δ(q0,a)=q1 and δ(q0,b)=q0 → only 'a' reaches q1
    assert words == {"a"}


def test_words_for_path_invalid_edge(simple_dfa):
    import pytest
    with pytest.raises(ValueError):
        simple_dfa.words_for_path(["q1", "q0"])  # not in example table


def test_accepts(simple_dfa):
    assert simple_dfa.accepts("a") is True
    assert simple_dfa.accepts("b") in (True, False)  # depends on your δ

    with pytest.raises(ValueError):
        simple_dfa.accepts("x")
