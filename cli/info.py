import argparse

from graphviz import Digraph # type: ignore
from automata.dfa import DFA
from automata.parser import parse_dfa_file

from automata.parser import parse_dfa_file

def print_transition_table(dfa: DFA):
    Q_sorted = sorted(dfa.Q)
    Σ_sorted = sorted(dfa.Σ)

    header = ["state"] + Σ_sorted
    widths = [max(len(h), 5) for h in header]

    for s in Q_sorted:
        widths[0] = max(widths[0], len(s))
        for i, sym in enumerate(Σ_sorted, start=1):
            dst = dfa.δ.get((s, sym), "-")
            widths[i] = max(widths[i], len(dst))

    def fmt_row(row: list[str]) -> str:
        return " | ".join(f"{cell:>{widths[i]}}" for i, cell in enumerate(row))
    
    print("\nTransition Table δ:")
    print(fmt_row(header))
    print("-+-".join("-" * w for w in widths))

    for s in Q_sorted:
        row = [s]
        for sym in Σ_sorted:
            dst = dfa.δ.get((s, sym), "-")
            row.append(dst)
        print(fmt_row(row))

def main():
    ap = argparse.ArgumentParser(description="Show DFA tuples and counts from a .dfauto file")
    ap.add_argument("input", help="Path to .dfauto file")
    args = ap.parse_args()

    dfa = parse_dfa_file(args.input)
    Q, Σ, δ, q0, F = dfa.get_tuples()

    print("DFA 5-tuple:")
    print(f"  Q  = {Q}")
    print(f"  Σ  = {Σ}")
    print(f"  δ  = {δ}")
    print(f"  q0 = {q0}")
    print(f"  F  = {F}")
    print()

    print("Counts:")
    print(f"  |Q| = {len(Q)}")
    print(f"  |Σ| = {len(Σ)}")
    print(f"  |δ| = {len(δ)}")
    print(f"  |F| = {len(F)}")

    print_transition_table(dfa)


if __name__ == "__main__":
    main()