import pytest


@pytest.mark.parametrize(
    "content, is_valid",
    [
        # ---------- A clean valid baseline for sanity ----------
        pytest.param(
            """
            3 [q0, q1, q2]
            2 [a, b]
            1,0
            2,1
            2,0
            0
            1,2
            """,
            True,
            id="simple_valid",
        ),

        # ---------- Fewer states than declared ----------
        pytest.param(
            """
            2 [q0]
            2 [a, b]
            1,0
            0,1
            0
            1
            """,
            False,
            id="fewer_states_than_declared",
        ),

        # ---------- Invalid symbol in alphabet ----------
        pytest.param(
            """
            2 [q0, q1]
            1 [!]
            1
            0
            0
            1
            """,
            False,
            id="invalid_symbol",
        ),

        # ---------- Symbols count mismatch ----------
        pytest.param(
            """
            2 [q0, q1]
            2 [a] 
            0
            1
            0
            1
            """,
            False,
            id="fewer_symbols_than_declared",
        ),

        # ---------- Symbols count mismatch ----------
        pytest.param(
            """
            2 [q0, q1]
            1 [a, b]
            0,1
            1,0
            0
            1
            """,
            False,
            id="more_symbols_than_declared",
        ),

        # ---------- States count mismatch ----------
        pytest.param(
            """
            2 [q0, q1, q2] 
            1 [a]
            1
            0
            0
            1
            """,
            False,
           id= "more_states_than_declared",
        ),

        # ---------- Invalid final/accept state index ----------
        pytest.param(
            """
            3 [q0, q1, q2]
            1 [a]
            1
            2
            2
            0
            5              
            """,
            False,
            id="invalid_final_state_index",
        ),

        # ---------- Not enough transition entries in a line ----------
        pytest.param(
            """
            3 [q0, q1, q2]
            2 [a, b]
            1               
            2,1
            2,0
            0
            1,2
            """,
            False,
            id="not_enough_transition_entries_in_row",
        ),

        # ---------- Too many transition entries in a line ----------
        pytest.param(
            """
            3 [q0, q1, q2]
            2 [a, b]
            1,0,0         
            2,1
            2,0
            0
            1,2
            """,
            False,
            id="too_many_transition_entries_in_row",
        ),

        # ---------- Not enough transition lines (fewer than |Q|) ----------
        pytest.param(
            """
            3 [q0, q1, q2]
            2 [a, b]
            1,0
            2,1             
            0
            1,2
            """,
            False,
            id="not_enough_transition_lines",
        ),

        # ---------- Too many transition lines (more than |Q|) ----------
        pytest.param(
            """
            2 [q0, q1]
            2 [a, b]
            1,0
            0,1
            1,1     
            0
            1
            """,
            False,
            id="too_many_transition_lines",
        ),

        # ---------- Not enough lines overall (missing accept states line) ----------
        pytest.param(
            """
            2 [q0, q1]
            1 [a]
            1
            0
            0 
            """,
            False,
            id="not_enough_lines_overall",
        ),
    ],
)
def test_parse_dfa_file(tmp_path, content, is_valid):
    from automata.parser import parse_dfa_file

    p = tmp_path / "dfa.dfauto"
    p.write_text(content.strip() + "\n", encoding="utf-8")

    if is_valid:
        dfa = parse_dfa_file(str(p))

        assert isinstance(dfa.Q, frozenset)
        assert isinstance(dfa.Σ, frozenset)
        assert isinstance(dfa.q0, str) and dfa.q0 in dfa.Q
        assert isinstance(dfa.F, frozenset) and dfa.F.issubset(dfa.Q)
    else:
        with pytest.raises((ValueError, KeyError, IndexError)):
            parse_dfa_file(str(p))
