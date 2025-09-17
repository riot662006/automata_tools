import argparse

from automata.parser import parse_dfa_file
from automata.sampler import Sampler

def main():
    ap = argparse.ArgumentParser(
        description="Simulate DFA on input strings from a .dfauto file")
    ap.add_argument("input", help="Path to .dfauto file")
    args = ap.parse_args()

    dfa = parse_dfa_file(args.input)
    
    sampler = Sampler(dfa)
    samples = sampler.sample(max_samples=100, max_depth=10)

    print(f"Sampled {len(samples)} strings from the DFA")
    print(" ".join(samples))


if __name__ == "__main__":
    main()
