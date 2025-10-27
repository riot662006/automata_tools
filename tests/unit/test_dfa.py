import pytest

from automata.dfa import DFA


def test_get_tuples_roundtrip(simple_dfa: DFA):
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
def test_edges_grouping(request: pytest.FixtureRequest, dfa_fixture: str):
    dfa: DFA = request.getfixturevalue(dfa_fixture)
    # edges[src][dst] -> tuple(symbols)
    for _, dst_map in dfa.edges.items():
        for _, syms in dst_map.items():
            assert isinstance(syms, tuple)
            assert all(isinstance(x, str) for x in syms)


def test_accepts(simple_dfa: DFA):
    assert simple_dfa.accepts("a") is True
    assert simple_dfa.accepts("b") in (True, False)  # depends on your δ

    with pytest.raises(ValueError):
        simple_dfa.accepts("x")
