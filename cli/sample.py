import argparse

from automata.parser import parse_dfa_file
from automata.sampler import Sampler
from automata.utils import cprint

def main():
    ap = argparse.ArgumentParser(
        description="Simulate DFA on input strings from a .dfauto file")
    ap.add_argument("input", help="Path to .dfauto file")
    ap.add_argument("--out", "-o", help="Optional path to save results into a file")
    ap.add_argument("--max-samples", type=int, default=10, help="Maximum number of samples to generate (default: 10)")
    ap.add_argument("--max-length", type=int, default=10, help="Maximum length of sampled strings (default: 10)")
    
    args = ap.parse_args()

    dfa = parse_dfa_file(args.input)
    
    sampler = Sampler(dfa)
    samples = sampler.sample(max_samples=args.max_samples, max_depth=args.max_length)
    
    msg = f"Sampled {len(samples)} strings from the DFA"
    
    if len(samples) == args.max_samples:
        cprint(msg, "green")
    elif len(samples) == 0:
        cprint(msg, "red")
    else:
        cprint(msg, "yellow")
        
    if args.out: 
        with open(args.out, "w") as f:
            f.write("\n".join(repr(s) for s in samples))
        print("Saved samples to", args.out)
    else:
        print(" ".join(repr(s) for s in samples))


if __name__ == "__main__":
    main()
