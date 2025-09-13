import argparse

def main():
    ap  = argparse.ArgumentParser(description="Simulate DFA on input strings from a .dfauto file")
    ap.add_argument("input", help="Path to .dfauto file")
    ap.add_argument("strings", nargs="+", help="Input strings to simulate on the DFA")
    args = ap.parse_args()

    print(f"Simulating DFA from {args.input} on input strings: {args.strings}")

if __name__ == "__main__":
    main()