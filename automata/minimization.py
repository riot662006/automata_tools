
from automata.dfa import DFA
from automata.nfa import NFA


def find_dead_states(auto: DFA | NFA) -> set[str]:
    visited: set[str] = set()
    useful: set[str] = set()

    def rec(state: str) -> bool:
        if state in visited:
            return state in useful

        visited.add(state)

        is_useful = False

        if state in auto.F:
            useful.add(state)
            is_useful = True

        for ns in auto.edges.get(state, {}):
            if rec(ns):
                useful.add(state)
                is_useful = True

        return is_useful

    rec(auto.q0)

    return set(state for state in auto.Q if state not in useful)


def minimize(auto: DFA | NFA) -> DFA | NFA:
    dead_states = find_dead_states(auto)

    return auto.remove_states(dead_states - {auto.q0})
