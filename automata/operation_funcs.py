from typing import Dict, Tuple
from automata.automaton import Epsilon, Symbol
from automata.dfa import DFA
from automata.minimization import minimize
from automata.nfa import NFA


def convert_dfa_to_nfa(dfa: DFA) -> NFA:
    """Convert a DFA to an equivalent NFA by wrapping its transition function.

    Args:
        dfa: The DFA to convert.

    Returns:
        An equivalent NFA.
    """
    nfa_delta: Dict[Tuple[str, Symbol], frozenset[str]] = {}
    for (src, sym), dst in dfa.δ.items():
        nfa_delta[(src, sym)] = frozenset({dst})

    return minimize(NFA(
        Q=dfa.Q,
        Σ=dfa.Σ,
        δ=nfa_delta,
        q0=dfa.q0,
        F=dfa.F
    ))


def union(nfa1: NFA, nfa2: NFA, should_minimize: bool = True) -> NFA:
    """Create a new NFA that is the union of two NFAs.

    Args:
        nfa1: The first NFA.
        nfa2: The second NFA.

    Returns:
        An NFA that accepts the union of the languages of nfa1 and nfa2.
    """

    union_Q = frozenset({f"q_union_start"} | {f"nfa1_{q}" for q in nfa1.Q} | {
                        f"nfa2_{q}" for q in nfa2.Q})
    union_Σ = nfa1.Σ | nfa2.Σ
    union_q0 = "q_union_start"
    union_F = frozenset({f"nfa1_{q}" for q in nfa1.F} |
                        {f"nfa2_{q}" for q in nfa2.F})
    union_δ: Dict[Tuple[str, Symbol], frozenset[str]] = {}

    # Epsilon transitions from new start state to both NFAs' start states
    union_δ[(union_q0, Epsilon)] = frozenset(
        {f"nfa1_{nfa1.q0}", f"nfa2_{nfa2.q0}"})

    for (src, sym), dsts in nfa1.δ.items():
        union_δ[(f"nfa1_{src}", sym)] = frozenset({f"nfa1_{d}" for d in dsts})

    for (src, sym), dsts in nfa2.δ.items():
        union_δ[(f"nfa2_{src}", sym)] = frozenset({f"nfa2_{d}" for d in dsts})

    raw_nfa = NFA(
        Q=union_Q,
        Σ=union_Σ,
        δ=union_δ,
        q0=union_q0,
        F=union_F
    )

    return minimize(raw_nfa) if should_minimize else raw_nfa
