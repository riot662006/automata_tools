import argparse

from automata.parser import parse_automaton
from automata.utils import print_table


def main():
    ap = argparse.ArgumentParser(
        description="Show DFA or NFA tuples and counts from an automaton file")
    ap.add_argument(
        "input", help="Path to the automaton file (.dfauto or .nfauto)")
    args = ap.parse_args()

    auto = parse_automaton(args.input)
    Q, Σ, δ, q0, F = auto.get_tuples()

    print(f"{auto.get_automaton_type()} 5-tuple:")
    print(f"  Q  = {set(Q)}")
    print(f"  Σ  = {set(Σ)}")

    print()
    print("Transition Table δ:")
    print_table(auto.get_transition_table())
    print()

    print(f"  q0 = {q0}")
    print(f"  F  = {set(F)}")
    print()

    print("Counts:")
    print(f"  |Q| = {len(Q)}")
    print(f"  |Σ| = {len(Σ)}")
    print(f"  |δ| = {len(δ)}")
    print(f"  |F| = {len(F)}")

if __name__ == "__main__":
    main()
