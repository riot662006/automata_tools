from typing import Dict, Tuple
from itertools import chain, combinations

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


def convert_nfa_to_dfa(nfa: NFA) -> DFA:
    """Convert an NFA to an equivalent DFA using the subset construction method.

    Args:
        nfa: The NFA to convert.

    Returns:
        An equivalent DFA.
    """
    nfa_minimized = minimize(nfa)

    # power set of nfa states
    state_subsets = [frozenset(state_subset) for state_subset in chain.from_iterable(
        combinations(nfa_minimized.Q, r) for r in range(len(nfa_minimized.Q) + 1))]

    start_states = frozenset(nfa_minimized.epsilon_closure(nfa_minimized.q0))
    state_map: Dict[frozenset[str], str] = {
        state: f"q_{i}" for i, state in enumerate([s for s in state_subsets if s != start_states])
    }
    state_map[start_states] = "q_start"
    print("State map:", state_map)

    dfa_delta: Dict[Tuple[str, str], str] = {}

    for state_subset in state_map.keys():
        for symbol in nfa_minimized.Σ:
            next_states: set[str] = set()
            for state in state_subset:
                next_states.update(nfa_minimized.transition(state, symbol))
            next_states_frozen = frozenset(next_states)
            dfa_delta[(state_map[state_subset], symbol)
                        ] = state_map[next_states_frozen]

    dfa_F = frozenset({state_map[s]
                      for s in state_map.keys() if s & nfa_minimized.F})

    dfa = DFA(
        Q=frozenset(state_map.values()),
        Σ=nfa_minimized.Σ,
        δ=dfa_delta,
        q0=state_map[start_states],
        F=dfa_F
    )

    return dfa


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
