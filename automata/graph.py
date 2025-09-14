from graphviz import Digraph

from automata.dfa import DFA


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
    for (src, dst_syms) in dfa.edges.items():
        for dst, syms in dst_syms.items():
            g.edge(src, dst, label=", ".join(syms))

    return g
