from graphviz import Digraph

g = Digraph('G', format='png', engine='dot')
g.attr(rankdir='LR')
g.attr('node', shape='circle', style='filled',
       fillcolor="lightgray", color='black')

Q = {'q_1', 'q_2', 'q_3', 'q_E'}  # states
Σ = {'0', '1'}  # alphabet
δ = {
    ('q_1', '0'): 'q_2',
    ('q_1', '1'): 'q_E',
    ('q_2', '0'): 'q_E',
    ('q_2', '1'): 'q_3',
    ('q_3', '0'): 'q_E',
    ('q_3', '1'): 'q_E',
    ('q_E', '0'): 'q_E',
    ('q_E', '1'): 'q_E'
}  # transition function
q_0 = 'q_1'  # start state
F = {'q_2', 'q_3'}  # accept states

for n in Q:
    g.node(n, shape='doublecircle' if n in F else 'circle')

# Invisible start arrow
g.node('start', shape='point', width='0.01')
g.edge('start', q_0)

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
