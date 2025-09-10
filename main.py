from graphviz import Digraph

g = Digraph('G', format='png', engine='dot')
g.attr(rankdir='LR')
g.attr('node', shape='circle', style='filled', fillcolor="lightgray", color='black')

for n in ['A', 'B', 'C']:
    g.node(n)

g.edge('A', 'B', label='a, b')
g.edge('B', 'C', label='c, d')
g.edge('C', 'C', label='e')

g.render('results/example_graph', cleanup=True)