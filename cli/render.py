import argparse
from pathlib import Path

from automata.graph import build_graph
from automata.parser import parse_dfa_file


def main():
    ap = argparse.ArgumentParser(
        description="Render a .dfauto DFA file to an image using Graphviz.")

    ap.add_argument("input", help="Path to .dfauto file")
    ap.add_argument(
        "-o", "--out", help="Output filepath (defaults to results/<stem>.<fmt>)")
    ap.add_argument("--fmt", default="png", choices=["png", "svg", "pdf"],
                    help="Output format (default: png)")
    ap.add_argument("--engine", default="dot",
                    choices=["dot", "neato", "fdp", "sfdp", "twopi", "circo"],
                    help="Graphviz layout engine (default: dot)")
    ap.add_argument("--rankdir", default="LR", choices=["LR", "TB", "RL", "BT"],
                    help="Layout direction (default: LR)")
    ap.add_argument("--node-fill", default="lightgray", help="Node fill color")

    args = ap.parse_args()

    dfa = parse_dfa_file(args.input)
    g = build_graph(dfa, engine=args.engine,
                    rankdir=args.rankdir, node_fill=args.node_fill)

    out_path = Path(args.out) if args.out else Path(
        "results") / (Path(args.input).stem + f".{args.fmt}")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    render_stem = out_path.with_suffix('').as_posix()
    g.render(render_stem, format=args.fmt, cleanup=True)  # type: ignore
    print(f"Rendered DFA to {out_path}")


if __name__ == "__main__":
    main()
