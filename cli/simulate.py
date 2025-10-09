import argparse
from pathlib import Path

from automata.parser import parse_automaton
from automata.utils import cprint


def main():
    ap = argparse.ArgumentParser(
        description="Simulate DFA or NFA on input strings from an automaton file"
    )
    ap.add_argument(
        "input",
        help="Path to the automaton file (.dfauto or .nfauto)"
    )
    ap.add_argument(
        "strings",
        nargs="*",
        help="Input strings to simulate on the automaton"
    )
    ap.add_argument(
        "--in",
        dest="infile",
        help="File containing input strings (space and/or newline separated)"
    )
    ap.add_argument(
        "--out", "-o",
        help="Optional path to save results into a file"
    )
    args = ap.parse_args()

    # Auto-detect DFA or NFA
    auto = parse_automaton(args.input)

    # Load words from args and optional file
    words = list(args.strings)
    if args.infile:
        file_words = Path(args.infile).read_text(encoding="utf-8").split()
        words.extend(word.strip() for word in file_words if word.strip())

    if not words:
        ap.error("No input strings provided (either as arguments or via --in file).")

    output_lines: list[str] = []

    # Simulate on all words
    for word in words:
        msg = f"{word!r} -> "
        try:
            accepted = auto.accepts(word)
            if accepted:
                msg += "Accepted"
                cprint(msg, color="green")
            else:
                msg += "Rejected"
                cprint(msg, color="red")
        except ValueError as e:
            msg += f"Error: {e}"
            cprint(msg, color="yellow")

        output_lines.append(msg)

    # Save results if requested
    if args.out:
        path = Path(args.out)
        path.write_text("\n".join(output_lines) + "\n", encoding="utf-8")
        cprint(f"Results written to {args.out}", color="blue")


if __name__ == "__main__":
    main()
