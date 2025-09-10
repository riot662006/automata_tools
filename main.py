import re

from graphviz import Digraph
from parser import parse_dfa_file

g = Digraph('G', format='png', engine='dot')
g.attr(rankdir='LR')
g.attr('node', shape='circle', style='filled',
       fillcolor="lightgray", color='black')

INPUT = 'example.dfauto'

Q, Σ, δ, q0, F = parse_dfa_file(INPUT)

for n in Q:
    subscript_split = n.split('_', 1)
    node_label = f"<{subscript_split[0]}<sub>{"_".join(subscript_split[1:])}</sub>>" if '_' in n else n

    g.node(n, label=node_label, shape='doublecircle' if n in F else 'circle')

# Invisible start arrow
g.node('start', shape='point', width='0.01')
g.edge('start', q0)

edges = {}
for (src, sym), dst in δ.items():
    if (src, dst) in edges:
        edges[(src, dst)].append(sym)
    else:
        edges[(src, dst)] = [sym]

for (src, dst), syms in edges.items():
    g.edge(src, dst, label=', '.join(syms))

g.body.append("{ rank=source start }")
g.render('results/example_graph', cleanup=True)
