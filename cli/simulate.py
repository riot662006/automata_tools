import argparse
from pathlib import Path

from automata.parser import parse_dfa_file
from automata.utils import cprint


def main():
    ap = argparse.ArgumentParser(
        description="Simulate DFA on input strings from a .dfauto file")
    ap.add_argument("input", help="Path to .dfauto file")
    ap.add_argument("strings", nargs="*",
                    help="Input strings to simulate on the DFA")
    ap.add_argument("--in", dest="infile",
                    help="File containing input strings (space and/or newline separated)")
    ap.add_argument(
        "--out", "-o", help="Optional path to save results into a file")
    args = ap.parse_args()

    dfa = parse_dfa_file(args.input)

    words = list(args.strings)
    if args.infile:
        file_words = Path(args.infile).read_text(encoding="utf-8").split()
        words.extend([word for word in file_words if word.strip()])

    if not words:
        ap.error(
            "No input strings provided (either as arguments or via --strings-file).")

    output_lines: list[str] = []

    for word in words:
        msg = f"{word!r} -> "

        try:
            accepted = dfa.accepts(word)

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
    if args.out:
        path = Path(args.out)
        path.write_text("\n".join(output_lines) + "\n", encoding="utf-8")

        cprint(f"Results written to {args.out}")


if __name__ == "__main__":
    main()
