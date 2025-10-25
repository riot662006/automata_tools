import argparse

from automata.dfa import DFA
from automata.graph import build_graph
from automata.operations import convert_dfa_to_nfa, convert_nfa_to_dfa
from automata.parser import parse_automaton
from automata.nfa import NFA


def main():
    ap = argparse.ArgumentParser(
        description="Convert between automaton formats (DFA ⇄ NFA)"
    )
    ap.add_argument(
        "input", help="Path to the automaton file (.dfauto or .nfauto)")
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
        help="Optional output base, NO EXTENSION (default: results/converted)",
        default="results/converted"
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

    out_base_path = args.out

    if '.' in out_base_path.split('/')[-1]:
        raise ValueError("Output base should not have an extension.")

    out_path = converted.save(out_base_path)
    
    g = build_graph(converted)
    g.render(out_base_path, format='png', cleanup=True)  # type: ignore
    
    print(f"✅ Converted to NFA and written to {out_path} and rendered image to {out_base_path}.png")


if __name__ == "__main__":
    main()
