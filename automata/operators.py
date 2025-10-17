from typing import Dict, Tuple
from automata.automaton import Symbol
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

