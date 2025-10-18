from typing import Any
import cv2
import numpy as np
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


def show_graph_opencv(auto: Automaton[Any, Any], *, window_name: str = "Automaton",
                      engine: str = "dot", rankdir: str = "LR",
                      node_fill: str = "lightgray",
                      wait_ms: int = 0,
                      max_width: int | None = None):
    """
    Render the automaton graph to an in-memory PNG and preview it via OpenCV.

    Args:
        auto: your DFA/NFA object (must work with build_graph).
        window_name: OpenCV window title.
        engine: Graphviz engine (e.g., "dot", "neato").
        rankdir: "LR" or "TB".
        node_fill: node fill color.
        wait_ms: milliseconds to wait in cv2.waitKey (0 = until keypress).
        max_width: if set, image is scaled down to this width (keeps aspect).
    Returns:
        The displayed image as a NumPy BGR array (useful for further UI).
    """
    # Build the Graphviz Digraph
    g = build_graph(auto, engine=engine, rankdir=rankdir, node_fill=node_fill)

    # Render to PNG bytes in memory (no file I/O)
    png_bytes = g.pipe(format="png")  # requires Graphviz installed

    # Decode PNG bytes to OpenCV image (BGR)
    img = cv2.imdecode(np.frombuffer(
        png_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise RuntimeError(
            "Failed to decode graph image. Is Graphviz installed and on PATH?")

    # Optional resize to fit screen
    if max_width is not None and img.shape[1] > max_width:
        scale = max_width / img.shape[1]
        new_size = (int(img.shape[1] * scale), int(img.shape[0] * scale))
        img = cv2.resize(img, new_size, interpolation=cv2.INTER_AREA)

    # Show in a window
    cv2.imshow(window_name, img)
    cv2.waitKey(wait_ms)
    
