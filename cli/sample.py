import argparse

from automata.parser import parse_automaton
from automata.sampler import Sampler
from automata.utils import cprint


def main():
    ap = argparse.ArgumentParser(
        description="Sample strings from a DFA or NFA given an automaton file"
    )
    ap.add_argument(
        "input",
        help="Path to the automaton file (.dfauto or .nfauto)"
    )
    ap.add_argument(
        "--out", "-o",
        help="Optional path to save results into a file"
    )
    ap.add_argument(
        "--max-samples",
        type=int,
        default=10,
        help="Maximum number of samples to generate (default: 10)"
    )
    ap.add_argument(
        "--max-length",
        type=int,
        default=10,
        help="Maximum length (depth) of sampled strings (default: 10)"
    )

    args = ap.parse_args()

    # Auto-detect DFA or NFA
    auto = parse_automaton(args.input)

    # Use the generic sampler (assumed to support both DFA and NFA)
    sampler = Sampler(auto)
    samples = sampler.sample(
        max_samples=args.max_samples,
        max_depth=args.max_length
    )

    auto_type = getattr(auto, "get_automaton_type", lambda: "Automaton")()
    msg = f"Sampled {len(samples)} strings from the {auto_type}"

    if len(samples) == args.max_samples:
        cprint(msg, "green")
    elif len(samples) == 0:
        cprint(msg, "red")
    else:
        cprint(msg, "yellow")

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write("\n".join(repr(s) for s in samples) + "\n")
        cprint(f"Saved samples to {args.out}", "blue")
    else:
        print(" ".join(repr(s) for s in samples))


if __name__ == "__main__":
    main()
