from typing import Mapping, Tuple
from automata.automaton import Epsilon, Symbol
from automata.dfa import DFA
from automata.nfa import NFA
from automata.utils import parse_counted_list, Q_LABEL_RE, SIGMA_LABEL_RE


def parse_dfa_file(path: str) -> DFA:
    """Parse a DFA from a .dfauto file."""
    if not path.endswith(".dfauto"):
        raise ValueError(f"Expected .dfauto file, got {path}.")

    with open(path, 'r') as f:
        lines = f.readlines()

    Q_num, _Q = parse_counted_list(lines[0], Q_LABEL_RE)
    Q = [f"q_{i}" for i in range(1, Q_num + 1)] if not _Q else _Q

    Σ_num, Σ = parse_counted_list(lines[1], SIGMA_LABEL_RE)
    if not Σ:
        Σ = [chr(ord('a') + i) for i in range(Σ_num)]

    δ: Mapping[Tuple[str, str], str] = {}
    if len(lines) < 4 + Q_num:
        raise ValueError(
            f"Expected at least {4 + Q_num} lines, got {len(lines)}.")

    for src, line in enumerate(lines[2:2 + Q_num], start=0):
        parts = [x.strip() for x in line.split(',')]
        if len(parts) != Σ_num:
            raise ValueError(
                f"Transition line {src+3} has {len(parts)} items, expected {Σ_num}."
            )
        for sym, dst_raw in enumerate(parts, start=0):
            dst = int(dst_raw)
            δ[(Q[src], Σ[sym])] = Q[dst]

    q0_raw = int(lines[2 + Q_num].strip())
    if not (0 <= q0_raw < Q_num):
        raise ValueError(
            f"Start state index {q0_raw} out of range 0..{Q_num-1}.")
    q0 = Q[q0_raw]

    F = {Q[int(x)] for x in lines[3 + Q_num].split(',') if x.strip()}
    if not F:
        raise ValueError("At least one accept state must be specified.")

    return DFA(frozenset(Q), frozenset(Σ), δ, q0, frozenset(F))


def parse_nfa_file(path: str) -> NFA:
    """Parse an NFA from a .nfauto file."""
    if not path.endswith(".nfauto"):
        raise ValueError(f"Expected .nfauto file, got {path}.")

    with open(path, 'r') as f:
        lines = f.readlines()

    Q_num, _Q = parse_counted_list(lines[0], Q_LABEL_RE)
    Q = [f"q_{i}" for i in range(1, Q_num + 1)] if not _Q else _Q

    Σ_num, Σ = parse_counted_list(lines[1], SIGMA_LABEL_RE)
    # epsilon cant be in Σ if user defined
    if Σ and 'ε' in Σ:
        raise ValueError("ε is a reserved symbol and can't be in Σ")
    if not Σ:
        Σ = [chr(ord('a') + i) for i in range(Σ_num)]

        try:
            epsilon_index = Σ.index('ε')
        except ValueError:
            pass
        else:
            Σ = Σ[:epsilon_index] + Σ[epsilon_index + 1:] + \
                [chr(ord('a') + len(Σ))]

    δ: Mapping[Tuple[str, Symbol], frozenset[str]] = {}
    if len(lines) < 4 + Q_num:
        raise ValueError(
            f"Expected at least {4 + Q_num} lines, got {len(lines)}.")

    for src, line in enumerate(lines[2:2 + Q_num], start=0):
        parts = [x.strip() for x in line.split(',')]
        if len(parts) != Σ_num + 1:
            raise ValueError(
                f"Transition line {src+3} has {len(parts)} items, expected {Σ_num} for letters and the last for ε."
            )
        for sym, dst_raw in enumerate(parts[:-1], start=0):
            # space seperated states
            dsts = [Q[int(x.strip())] for x in dst_raw.split(' ') if x.strip()]
            δ[(Q[src], Σ[sym])] = frozenset(dsts)

        # Add ε transitions
        for dst_raw in parts[-1].split(','):
            dsts = [Q[int(x.strip())] for x in dst_raw.split(' ') if x.strip()]
            δ[(Q[src], Epsilon)] = frozenset(dsts)

    q0_raw = int(lines[2 + Q_num].strip())
    if not (0 <= q0_raw < Q_num):
        raise ValueError(
            f"Start state index {q0_raw} out of range 0..{Q_num-1}.")
    q0 = Q[q0_raw]

    F = {Q[int(x)] for x in lines[3 + Q_num].split(',') if x.strip()}
    if not F:
        raise ValueError("At least one accept state must be specified.")

    return NFA(frozenset(Q), frozenset(Σ), δ, q0, frozenset(F))
