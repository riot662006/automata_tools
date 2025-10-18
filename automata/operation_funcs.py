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

    union_Q = frozenset({f"q_start"} | {f"nfa1_{q}" for q in nfa1.Q} | {
                        f"nfa2_{q}" for q in nfa2.Q})
    union_Σ = nfa1.Σ | nfa2.Σ
    union_q0 = "q_start"
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

def concatenate(nfa1: NFA, nfa2: NFA, should_minimize: bool = True) -> NFA:
    """Create a new NFA that is the concatenation of two NFAs.

    Args:
        nfa1: The first NFA.
        nfa2: The second NFA.

    Returns:
        An NFA that accepts the concatenation of the languages of nfa1 and nfa2.
    """

    concat_Q = frozenset({f"nfa1_{q}" for q in nfa1.Q} |
                         {f"nfa2_{q}" for q in nfa2.Q})
    concat_Σ = nfa1.Σ | nfa2.Σ
    concat_q0 = f"nfa1_{nfa1.q0}"
    concat_F = frozenset({f"nfa2_{q}" for q in nfa2.F})
    concat_δ: Dict[Tuple[str, Symbol], frozenset[str]] = {}

    for (src, sym), dsts in nfa1.δ.items():
        concat_δ[(f"nfa1_{src}", sym)] = frozenset(
            {f"nfa1_{d}" for d in dsts})

    for (src, sym), dsts in nfa2.δ.items():
        concat_δ[(f"nfa2_{src}", sym)] = frozenset(
            {f"nfa2_{d}" for d in dsts})

    # Epsilon transitions from nfa1's accepting states to nfa2's start state
    for f_state in nfa1.F:
        concat_δ[(f"nfa1_{f_state}", Epsilon)] = frozenset(
            {f"nfa2_{nfa2.q0}"})

    raw_nfa = NFA(
        Q=concat_Q,
        Σ=concat_Σ,
        δ=concat_δ,
        q0=concat_q0,
        F=concat_F
    )

    return minimize(raw_nfa) if should_minimize else raw_nfa

def kleene_star(nfa: NFA, should_minimize: bool = True) -> NFA:
    """Create a new NFA that is the Kleene star of the given NFA.

    Args:
        nfa: The NFA to apply Kleene star to.

    Returns:
        An NFA that accepts the Kleene star of the language of the input NFA.
    """

    star_Q = frozenset({f"q_start"} | {f"nfa_{q}" for q in nfa.Q})
    star_Σ = nfa.Σ
    star_q0 = "q_start"
    star_F = frozenset({f"q_start"} | {f"nfa_{q}" for q in nfa.F})
    star_δ: Dict[Tuple[str, Symbol], frozenset[str]] = {}

    # Epsilon transition from new start state to nfa's start state
    star_δ[(star_q0, Epsilon)] = frozenset({f"nfa_{nfa.q0}"})

    for (src, sym), dsts in nfa.δ.items():
        star_δ[(f"nfa_{src}", sym)] = frozenset({f"nfa_{d}" for d in dsts})

    # Epsilon transitions from nfa's accepting states back to nfa's start state
    for f_state in nfa.F:
        star_δ[(f"nfa_{f_state}", Epsilon)] = frozenset(
            {f"nfa_{nfa.q0}"})

    raw_nfa = NFA(
        Q=star_Q,
        Σ=star_Σ,
        δ=star_δ,
        q0=star_q0,
        F=star_F
    )

    return minimize(raw_nfa) if should_minimize else raw_nfa