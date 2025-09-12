from automata.dfa import DFA
from automata.utils import parse_counted_list, Q_LABEL_RE, SIGMA_LABEL_RE


def parse_dfa_file(path: str) -> DFA:
    with open(path, 'r') as f:
        lines = f.readlines()

    Q_num, Q = parse_counted_list(lines[0], Q_LABEL_RE)
    if not Q:
        Q = [f"q_{i}" for i in range(1, Q_num + 1)]

    Σ_num, Σ = parse_counted_list(lines[1], SIGMA_LABEL_RE)
    if not Σ:
        Σ = [chr(ord('a') + i) for i in range(Σ_num)]

    δ = {}
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

    return DFA(Q, Σ, δ, q0, F)
