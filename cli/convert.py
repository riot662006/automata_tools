import argparse
from pathlib import Path

from automata.dfa import DFA
from automata.operations import convert_dfa_to_nfa, convert_nfa_to_dfa
from automata.parser import parse_automaton
from automata.nfa import NFA
from automata.automaton import Epsilon


def main():
    ap = argparse.ArgumentParser(
        description="Convert between automaton formats (DFA ⇄ NFA)"
    )
    ap.add_argument("input", help="Path to the automaton file (.dfauto or .nfauto)")
    ap.add_argument(
        "--to",
        "-t",
        choices=["dfa", "nfa"],
        required=True,
        help="Target automaton type"
    )
    ap.add_argument(
        "--out",
        "-o",
        help="Optional output file path (default: results/converted.<type>)"
    )
    args = ap.parse_args()

    auto = parse_automaton(args.input)

    if args.to == auto.__class__.__name__.lower():
        print(f"Already a {args.to.upper()} — no conversion performed.")
        return

    converted = None

    match args.to:
        case "dfa":
            if isinstance(auto, NFA):
                converted = convert_nfa_to_dfa(auto)
        case "nfa":
            if isinstance(auto, DFA):
                converted = convert_dfa_to_nfa(auto)
        case _:
            raise ValueError(f"Unknown target automaton type: {args.to}")
        
    if converted is None:
        print("Conversion failed.")
        return

    out_path = converted.save("results/converted")
    print(f"✅ Converted to NFA and written to {out_path}")


if __name__ == "__main__":
    main()
