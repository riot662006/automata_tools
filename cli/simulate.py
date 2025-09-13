import argparse

from automata.parser import parse_dfa_file
from automata.utils import cprint

def main():
    ap  = argparse.ArgumentParser(description="Simulate DFA on input strings from a .dfauto file")
    ap.add_argument("input", help="Path to .dfauto file")
    ap.add_argument("strings", nargs="+", help="Input strings to simulate on the DFA")
    args = ap.parse_args()

    dfa = parse_dfa_file(args.input)
    
    for word in args.strings:
        try:
            accepted = dfa.accepts(word)
            
            if accepted:
                cprint(f"Input: {word!r} -> Accepted", color="green")
            else:
                cprint(f"Input: {word!r} -> Rejected", color="red")
        except ValueError as e:
            cprint(f"Input: {word!r} -> Error: {e}", color="yellow")

if __name__ == "__main__":
    main()