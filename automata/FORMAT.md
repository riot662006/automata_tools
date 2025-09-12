# `.dfauto` File Format

A `.dfauto` file describes a **Deterministic Finite Automaton (DFA)**.  
It is a plain text file with **five sections** in this order:

---

## 1. States (Q)

```
<N> [q1, q2, ..., qN]
```

- `<N>` = number of states (must be ≥ 1).  
- Optional bracketed list:
  - If present → must contain exactly `N` state names.  
  - If absent → default names are generated: `q_1, q_2, …, qN`.

**Examples**

```
3 [q0, q1, q2]
4
```

---

## 2. Alphabet (Σ)

```
<M> [a, b, ..., m]
```

- `<M>` = number of symbols (must be ≥ 1).  
- Optional bracketed list:
  - If present → must contain exactly `M` valid symbols.  
    - Symbols are **single characters** (letter, digit, or underscore).  
  - If absent → default names are `a, b, …`.

**Examples**

```
2 [a, b]
3
```

---

## 3. Transition Table (δ)

- Next **N lines** (one per state, in the order listed).  
- Each line has **M integers**, separated by commas.  
- Each integer = index of the destination state (0-based).  
- Line *i* corresponds to state `q_i`.  
- Column *j* corresponds to symbol `Σ[j]`.

**Example**

For `N = 3`, `M = 2`:

```
1,0
2,1
2,0
```

This means:

- δ(q0, a) = q1, δ(q0, b) = q0  
- δ(q1, a) = q2, δ(q1, b) = q1  
- δ(q2, a) = q2, δ(q2, b) = q0  

---

## 4. Start State (q₀)

```
<index>
```

- A single integer (0-based index into the state list).  

**Example**

```
0
```

= start state is `q0`.

---

## 5. Accept States (F)

```
<index1>, <index2>, ...
```

- Comma-separated list of state indices (0-based).  
- Must contain at least one index.  
- Duplicates are ignored.

**Examples**

```
1
1, 2
```

---

# Full Example

```
3 [q0, q1, q2]
2 [a, b]
1,0
2,1
2,0
0
1,2
```

### Interpretation

- States: {q0, q1, q2}  
- Alphabet: {a, b}  
- Transition function:
  - δ(q0,a)=q1, δ(q0,b)=q0  
  - δ(q1,a)=q2, δ(q1,b)=q1  
  - δ(q2,a)=q2, δ(q2,b)=q0  
- Start state: q0  
- Accept states: {q1, q2}  

---

✅ This format is strict: counts must match actual list lengths, indices must be within range, and at least one accept state must be defined.  
