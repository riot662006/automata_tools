
from typing import Any, Dict, FrozenSet, Set, Tuple, overload
from automata.automaton import Epsilon, Symbol
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


@overload
def minimize(auto: "DFA") -> "DFA": ...
@overload
def minimize(auto: "NFA") -> "NFA": ...

def minimize(auto: DFA | NFA) -> DFA | NFA:
    dead_states = find_dead_states(auto)

    auto_no_dead = auto.remove_states(dead_states - {auto.q0})

    groups = group_indistinguishable_states(auto_no_dead)

    new_Q: set[str] = set()
    state_map: Dict[str, str] = {}

    for g in groups:
        if auto_no_dead.q0 in g:
            retained_state = auto_no_dead.q0
        else:
            retained_state = sorted(g)[0]

        for s in g:
            state_map[s] = retained_state

        new_Q.add(retained_state)

    if isinstance(auto_no_dead, NFA):
        new_δ_nfa: Dict[Tuple[str, Symbol], frozenset[str]] = {}

        for (src, sym), dsts in auto_no_dead.δ.items():
            if state_map[src] not in new_Q:
                continue

            new_dsts = frozenset(state_map[d]
                                 for d in dsts if state_map[d] in new_Q)
            if new_dsts:
                new_δ_nfa[(state_map[src], sym)] = new_dsts

        return NFA(
            Q=frozenset(new_Q),
            Σ=auto_no_dead.Σ,
            δ=new_δ_nfa,
            q0=auto_no_dead.q0,
            F=frozenset(state_map[s]
                        for s in auto_no_dead.F if state_map[s] in new_Q)
        )
    else:
        new_δ_dfa: Dict[Tuple[str, str], str] = {}

        for (src, sym), dst in auto_no_dead.δ.items():
            if state_map[src] not in new_Q:
                continue
            
            new_δ_dfa[(state_map[src], sym)] = state_map[dst]

        return DFA(
            Q=frozenset(new_Q),
            Σ=auto_no_dead.Σ,
            δ=new_δ_dfa,
            q0=auto_no_dead.q0,
            F=frozenset(state_map[s]
                        for s in auto_no_dead.F if state_map[s] in new_Q)
        )

    raise RuntimeError("Unreachable")
