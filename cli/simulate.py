import argparse

from automata.parser import parse_dfa_file

def main():
    ap  = argparse.ArgumentParser(description="Simulate DFA on input strings from a .dfauto file")
    ap.add_argument("input", help="Path to .dfauto file")
    ap.add_argument("strings", nargs="+", help="Input strings to simulate on the DFA")
    args = ap.parse_args()

    dfa = parse_dfa_file(args.input)
    
    for word in args.strings:
        try:
            is_accepted = dfa.accepts(word)
            
            print(f"Input: {word!r} -> {'Accepted' if is_accepted else 'Rejected'}")
        except ValueError as e:
            print(f"Input: {word!r} -> Error: {e}")

if __name__ == "__main__":
    main()