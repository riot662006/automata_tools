from typing import Any
from graphviz import Digraph  # type: ignore

from automata.automaton import Automaton


def html_label(name: str) -> str:
    """Render labels like q_12 as q<sub>12</sub> for Graphviz HTML-like labels."""
    if "_" in name:
        head, tail = name.split("_", 1)
        tail_html = tail  # keep underscores in subscript
        return f"<{head}<sub>{tail_html}</sub>>"
    return name


def build_graph(auto: Automaton[Any, Any], *, engine: str = "dot", rankdir: str = "LR", node_fill: str = "lightgray"):
    g = Digraph('G', format='png', engine=engine)
    g.attr(rankdir=rankdir, )  # type: ignore
    g.attr('node', shape='circle', style='filled',  # type: ignore
           fillcolor=node_fill, color='black')

    for n in auto.Q:
        shape = "doublecircle" if n in auto.F else "circle"
        g.node(n, label=html_label(n), shape=shape)  # type: ignore

    # Invisible start arrow
    g.node('start', shape='point', width='0.01')  # type: ignore
    g.edge('start', auto.q0)  # type: ignore
    g.body.append("{ rank=source start }")  # type: ignore

    # Group multiple symbols on same edge
    for (src, dst_syms) in auto.edges.items():
        for dst, syms in dst_syms.items():
            g.edge(src, dst, label=", ".join(  # type: ignore
                [str(s) for s in syms]))

    return g
