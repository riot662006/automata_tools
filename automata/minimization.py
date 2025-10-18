
from typing import Any, Dict, FrozenSet, Set, Tuple, overload
from automata.automaton import Epsilon, Symbol
from automata.dfa import DFA
from automata.nfa import NFA


class _MinimizationView:
    def __init__(self, auto: DFA | NFA, live: frozenset[str]):
        self.Q = frozenset(live)
        self.Σ = auto.Σ
        self.q0 = auto.q0
        self.F = frozenset(s for s in auto.F if s in live)
        self.δ = {k: v for k, v in auto.δ.items() if k[0] in live}


def _fresh_sink_name(existing_states: Set[str]) -> str:
    i = 0
    while True:
        candidate = f"q_sink_{i}"
        if candidate not in existing_states:
            return candidate
        i += 1


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


def group_indistinguishable_states(auto: DFA | NFA | _MinimizationView) -> Set[FrozenSet[str]]:
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
    dead = find_dead_states(auto)
    live = (auto.Q - dead) | {auto.q0}

    view = _MinimizationView(auto, live)
    groups = group_indistinguishable_states(view)

    new_Q: set[str] = set()
    state_map: Dict[str, str] = {}
    rep_of: Dict[str, str] = {}

    for g in groups:
        kept = view.q0 if view.q0 in g else sorted(g)[0]
        for s in g:
            state_map[s] = kept
        new_Q.add(kept)
        rep_of[kept] = next(iter(g))

    if isinstance(auto, NFA):
        new_δ_nfa: Dict[Tuple[str, Symbol], frozenset[str]] = {}

        for (src, sym), dsts in view.δ.items():
            if src not in live:
                continue

            kept_src = state_map.get(src)
            if kept_src not in new_Q:
                continue

            mapped = frozenset(
                state_map[d] for d in dsts
                if d in live and state_map[d] in new_Q
            )
            if mapped:
                new_δ_nfa[(kept_src, sym)] = mapped

        return NFA(
            Q=frozenset(new_Q),
            Σ=view.Σ,
            δ=new_δ_nfa,
            q0=view.q0,
            F=frozenset(state_map[s] for s in view.F if state_map[s] in new_Q),
        )

    new_δ_dfa: Dict[Tuple[str, str], str] = {}

    # cover every (kept_src, sym) from a representative in the original δ
    for kept_src in new_Q:
        rep_src = rep_of[kept_src]
        for sym in view.Σ:
            orig_dst = auto.δ.get((rep_src, sym))
            if orig_dst is None:
                continue  # will fix via sink below
            # If destination is not live, it was pruned; fix via sink
            if orig_dst not in live:
                continue
            kept_dst = state_map[orig_dst]
            new_δ_dfa[(kept_src, sym)] = kept_dst

    if view.Σ:
        missing = [(q, a)
                   for q in new_Q for a in view.Σ if (q, a) not in new_δ_dfa]
        if missing:
            sink = _fresh_sink_name(new_Q)
            new_Q.add(sink)
            for a in view.Σ:
                new_δ_dfa[(sink, a)] = sink
            for q, a in missing:
                new_δ_dfa[(q, a)] = sink

    return DFA(
        Q=frozenset(new_Q),
        Σ=view.Σ,
        δ=new_δ_dfa,
        q0=view.q0,
        F=frozenset(state_map[s] for s in view.F if state_map[s] in new_Q),
    )
