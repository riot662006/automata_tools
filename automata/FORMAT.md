# 🗂️ Automata File Formats

Automata Tools supports two plain-text formats:

- **`.dfauto`** → Deterministic Finite Automata (DFA)  
- **`.nfauto`** → Nondeterministic Finite Automata (NFA)

Both share similar structures but differ in how transitions are represented.

---

## ⚙️ `.dfauto` Format — *Deterministic Finite Automaton*

A `.dfauto` file defines a **DFA** with a fixed number of states and one unique transition per `(state, symbol)` pair.

It contains **five ordered sections**:

---

### 1. States (Q)

```
<N> [q0, q1, ..., qN-1]
```

- `<N>` = number of states (≥1).  
- Optional `[ ... ]` list:
  - If provided → must contain **exactly N** names.
  - If omitted → defaults to `q_1, q_2, …, qN`.

**Examples**

```
3 [q0, q1, q2]
4
```

---

### 2. Alphabet (Σ)

```
<M> [a, b, ..., m]
```

- `<M>` = number of symbols (≥1).  
- Optional list:
  - If present → must have **exactly M** symbols.
  - If absent → defaults to `a, b, c, ...`.
- Symbols must be **single printable characters**.
- `ε` (epsilon) is **not allowed** in a DFA alphabet.

**Examples**

```
2 [a, b]
3
```

---

### 3. Transition Table (δ)

Each of the next `N` lines corresponds to one state’s transitions in order.

- Each line has exactly `M` comma-separated integers.  
- Each integer is the **0-based index** of the destination state.  
- Line `i` corresponds to `Q[i]`.  
- Column `j` corresponds to symbol `Σ[j]`.

**Example**

For `N = 3`, `M = 2`:

```
1,0
2,1
2,0
```

Meaning:
```
δ(q0, a) = q1, δ(q0, b) = q0
δ(q1, a) = q2, δ(q1, b) = q1
δ(q2, a) = q2, δ(q2, b) = q0
```

---

### 4. Start State (q₀)

A single integer (0-based) selecting the start state.

```
0
```

→ `q0` is the start state.

---

### 5. Accept States (F)

Comma-separated 0-based indices of accepting states.

```
1
1, 2
```

Must contain at least one valid index.

---

### ✅ Example

```
3 [q0, q1, q2]
2 [a, b]
1,0
2,1
2,0
0
1,2
```

Interpretation:
```
Q  = {q0, q1, q2}
Σ  = {a, b}
δ  = { (q0,a)=q1, (q0,b)=q0, (q1,a)=q2, (q1,b)=q1, (q2,a)=q2, (q2,b)=q0 }
q₀ = q0
F  = {q1, q2}
```

---

## ⚙️ `.nfauto` Format — *Nondeterministic Finite Automaton (with ε)*

A `.nfauto` file describes an **NFA**, where:
- Transitions may go to **multiple destinations**.
- Transitions may include **ε (epsilon)** (empty string) moves.

It contains **five ordered sections** similar to `.dfauto`.

---

### 1. States (Q)

```
<N> [q0, q1, ..., qN-1]
```

Same as in DFA.

---

### 2. Alphabet (Σ)

```
<M> [a, b, ..., m]
```

- `<M>` = number of non-ε symbols (≥1).  
- Optional list:
  - If omitted → defaults to `a, b, ...`.
- `ε` is **reserved** and automatically handled by the parser.  
  It **cannot** appear in the explicit Σ list.

---

### 3. Transition Table (δ)

Each of the next `N` lines corresponds to transitions for one state, in order.

Each line has **M + 1** comma-separated entries:
- First **M columns** correspond to the `Σ` symbols.
- The **last column** corresponds to **ε transitions**.

Each column may contain:
- A **space-separated** list of destination indices.
- Empty if no transition.

**Example**

```
2 [a, b]
1  ,  , 1
 ,  , 
```

This means:
```
δ(q0, a) = {}
δ(q0, b) = {}
δ(q0, ε) = {q1}
δ(q1, a) = {}
δ(q1, b) = {}
δ(q1, ε) = {}
```

---

### 4. Start State (q₀)

A single integer selecting the start state.

```
0
```

→ start = `q0`

---

### 5. Accept States (F)

Comma-separated indices of accept states.

```
1
```

→ `F = {q1}`

---

### ✅ Example

```
2 [q0, q1]
2 [a, b]
 , , 1
 , ,
0
1
```

Interpretation:
```
Q  = {q0, q1}
Σ  = {a, b}
δ  = {
  (q0, ε) = {q1},
  (q0, a) = ∅, (q0, b) = ∅,
  (q1, ε) = ∅, (q1, a) = ∅, (q1, b) = ∅
}
q₀ = q0
F  = {q1}
```

---

## 🧠 Notes

- All indices are **0-based**.
- Counts in the header lines must match actual list lengths.
- Empty entries represent **no transitions**.
- Epsilon transitions (`ε`) are handled automatically — the NFA engine will compute:
  ```
  ε-closure(move(ε-closure(state), symbol))
  ```
  for each symbol.
- `.nfauto` files are validated on load; malformed tables or mismatched counts raise `ValueError`.
