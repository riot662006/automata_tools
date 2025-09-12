# Automata Tools
A small toolkit for working with [Automata theory](https://en.wikipedia.org/wiki/Automata_theory), built to support my Theory of Computation class.

Instead of drawing automata by hand each time, I wanted to save time creating and rendering automata from a simple text format and test my understanding of each concept by creating a tool as I learn it. This way, I can focus more on concepts and less on the mechanics of drawing arrows and circles.

## Project Structure
```
automata/   # Core library
  dfa.py    # DFA dataclass (Q, Σ, δ, q0, F)
  parser.py # Parse .dfauto files into DFA 
  FORMAT.md # Spec for .dfauto format

cli/        # Command-line tools
  render.py # Render DFA diagram as image file
  info.py   # Show tuples for describing an automaton
  ...       # (future tools)

examples/   # Example automata
  example.dfauto

results/    # Output images (ignored in git)
```

## Usage
### Render DFA to image
```bash
python -m cli.render_dfauto examples/example.dfauto 

# Output format (png/svg/pdf)
python -m cli.render_dfauto examples/example.dfauto --fmt svg

# Custom output filename 
python -m cli.render_dfauto examples/example.dfauto -o results/mydfa.png # default {name}.png e.g. example.png
```

### Inspect DFA 
```bash
python -m cli.info examples/example.dfauto
```
Output:
```bash
DFA 5-tuple:
  Q  = ['q_1', 'q_2', 'q_3', 'q_4']
  Σ  = ['0', '1']
  δ  = {('q_1', '0'): 'q_2', ('q_1', '1'): 'q_4', ('q_2', '0'): 'q_4', ('q_2', '1'): 'q_3', ('q_3', '0'): 'q_4', ('q_3', '1'): 'q_4', ('q_4', '0'): 'q_4', ('q_4', '1'): 'q_1'}
  q0 = q_1
  F  = {'q_3', 'q_2'}

Counts:
  |Q| = 4
  |Σ| = 2
  |δ| = 8
  |F| = 2

Transition Table δ:
state |     0 |     1
------+-------+------
  q_1 |   q_2 |   q_4
  q_2 |   q_4 |   q_3
  q_3 |   q_4 |   q_4
  q_4 |   q_4 |   q_1
```

### Installation
Clone this repo and install dependencies
```bash
pip install =r requirements.txt
```
Dependencies
- `graphviz` (system binary + Python package. Download [here](https://graphviz.org/download) and make sure you add to PATH) 
- Python >= 3.10

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.