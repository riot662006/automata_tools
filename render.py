import argparse
from pathlib import Path
import re

from graphviz import Digraph
from custom_types import DFA
from parser import parse_dfa_file

def html_label(name: str) -> str:
    """Render labels like q_12 as q<sub>12</sub> for Graphviz HTML-like labels."""
    if "_" in name:
        head, tail = name.split("_", 1)
        tail_html = tail  # keep underscores in subscript
        return f"<{head}<sub>{tail_html}</sub>>"
    return name

def build_graph(dfa: DFA, *, engine="dot", rankdir="LR", node_fill="lightgray"):
    g = Digraph('G', format='png', engine='dot')
    g.attr(rankdir='LR')
    g.attr('node', shape='circle', style='filled',
        fillcolor="lightgray", color='black')
    
    for n in dfa.Q:
        shape = "doublecircle" if n in dfa.F else "circle"
        g.node(n, label=html_label(n), shape=shape)

    # Invisible start arrow
    g.node('start', shape='point', width='0.01')
    g.edge('start', dfa.q0)
    g.body.append("{ rank=source start }")

    # Group multiple symbols on same edge
    grouped = {}
    for (src, sym), dst in dfa.δ.items():
        grouped.setdefault((src, dst), []).append(sym)
    for (src, dst), syms in grouped.items():
        g.edge(src, dst, label=", ".join(syms))

    return g
    

def main():
    ap = argparse.ArgumentParser(description="Render a .dfauto DFA file to an image using Graphviz.")

    ap.add_argument("input", help="Path to .dfauto file")
    ap.add_argument("-o", "--out", help="Output filepath (defaults to results/<stem>.<fmt>)")
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
    g = build_graph(dfa, engine=args.engine, rankdir=args.rankdir, node_fill=args.node_fill)

    out_path = Path(args.out) if args.out else Path("results") / (Path(args.input).stem + f".{args.fmt}")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    render_stem = out_path.with_suffix('').as_posix()
    g.render(render_stem, format=args.fmt, cleanup=True)
    print(f"Rendered DFA to {out_path}")

if __name__ == "__main__":
    main()
