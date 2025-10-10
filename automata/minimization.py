
from typing import Any, Dict, FrozenSet, Set, Tuple
from automata.automaton import Epsilon
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


def group_indistinguishable_states(auto: DFA | NFA) -> Set[FrozenSet[str]]:
    """
    Group states by identical outgoing-transition 'rows' (including ε for NFAs).
    Returns a set of frozensets; each frozenset is one equivalence class.

    Note: This ONLY compares transition structure, not acceptance (F).
    """
    # Build a signature per state representing its transition row
    def row_signature(state: str) -> Tuple[Tuple[Any, Any], ...]:
        if isinstance(auto, NFA):
            # include ε alongside Σ
            syms = list(auto.Σ) + [Epsilon]
            # each destination is a set -> freeze for hashing
            pairs = tuple((sym, frozenset(auto.δ.get((state, sym), set())))
                          for sym in syms)
        else:
            syms = list(auto.Σ)
            pairs = tuple((sym, frozenset(auto.δ.get((state, sym), set())))
                          for sym in syms)
        # sort for deterministic grouping
        return tuple(sorted(pairs, key=lambda x: (str(x[0]), str(x[1]))))

    buckets: Dict[Tuple[Tuple[str, Any], ...], Set[str]] = {}
    for s in auto.Q - auto.F:
        sig = row_signature(s)
        buckets.setdefault(sig, set()).add(s)

    groups = {frozenset(g) for g in buckets.values()}
    buckets.clear()

    for s in auto.F:
        sig = row_signature(s)
        buckets.setdefault(sig, set()).add(s)

    groups.update({frozenset(g) for g in buckets.values()})
    return groups


def minimize(auto: DFA | NFA) -> DFA | NFA:
    dead_states = find_dead_states(auto)

    return auto.remove_states(dead_states - {auto.q0})
