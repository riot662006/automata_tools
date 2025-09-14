import argparse
from pathlib import Path

from automata.dfa import DFA
from automata.parser import parse_dfa_file
from automata.utils import cprint


def find_simple_path(dfa: DFA, state: str, seq: list[str], end_states: set[str]=None):
    results = []
    if state in (end_states or dfa.F):
        results.append(seq + [state])

    for (dst, _) in dfa.edges[state].items():
        if dst in seq or dst == state:
            continue
        results.extend(find_simple_path(dfa, dst, seq + [state], end_states))

    return results


def find_state_loops(dfa, state):
    next_state = set([dfa.transition(state, sym) for sym in dfa.Σ])

    results = []
    for ns in next_state:
        results.extend(find_simple_path(dfa, ns, [], set([state])))

    return results


def main():
    ap = argparse.ArgumentParser(
        description="Simulate DFA on input strings from a .dfauto file")
    ap.add_argument("input", help="Path to .dfauto file")
    args = ap.parse_args()

    dfa = parse_dfa_file(args.input)

    limit, max_len = 5, 5
    accepted = find_simple_path(dfa, dfa.q0, [])
    print("Accepted", accepted)

    for state_seq in accepted:
        print(dfa.get_words_from_path(state_seq))

    for state in dfa.Q:
        loops = find_state_loops(dfa, state)
        print(state, loops)
        


if __name__ == "__main__":
    main()
