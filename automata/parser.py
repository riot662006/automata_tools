from typing import Any, Callable, Mapping, Tuple, Type
from automata.automaton import Automaton, Epsilon, Symbol
from automata.dfa import DFA
from automata.nfa import NFA
from automata.utils import parse_counted_list, Q_LABEL_RE, SIGMA_LABEL_RE


def infer_automaton_class(path: str) -> type[Automaton[Any, Any]]:
    for ext, (cls, _) in AUTOMATON_PARSERS.items():
        if path.endswith(ext):
            return cls
    raise ValueError(f"Expected one of {list(AUTOMATON_PARSERS)}, got {path}.")


def parse_automaton(path: str) -> Automaton[Any, Any]:
    for ext, (_, parser) in AUTOMATON_PARSERS.items():
        if path.endswith(ext):
            return parser(path)
    raise ValueError(f"Unknown automaton type for {path}.")


def _parse_automaton_data(lines: list[str]) -> Tuple[list[str], int, list[str] | None, list[str], str, set[str]]:
    """Parses common components for both DFA and NFA from lines."""
    if len(lines) < 4:
        raise ValueError("File is too short to be a valid automaton.")

    Q_num, _Q = parse_counted_list(lines[0], Q_LABEL_RE)
    Q = [f"q_{i}" for i in range(Q_num)] if not _Q else _Q

    if len(Q) != Q_num:
        raise ValueError(
            "State count does not match the number of states provided.")

    Σ_num, Σ_raw = parse_counted_list(lines[1], SIGMA_LABEL_RE)
    if Σ_raw and len(Σ_raw) != Σ_num:
        raise ValueError(
            "Alphabet count does not match the number of symbols provided.")

    if len(lines) < 4 + Q_num:
        raise ValueError(
            f"Expected at least {4 + Q_num} lines, got {len(lines)}.")

    δ_raw = lines[2:2 + Q_num]

    q0_raw = int(lines[2 + Q_num].strip())
    if not (0 <= q0_raw < Q_num):
        raise ValueError(
            f"Start state index {q0_raw} out of range 0..{Q_num-1}.")
    q0 = Q[q0_raw]

    F = {Q[int(x)] for x in lines[3 + Q_num].split(',') if x.strip()}
    if not F:
        raise ValueError("At least one accept state must be specified.")

    return Q, Σ_num, Σ_raw, δ_raw, q0, F


def parse_dfa_file(path: str) -> DFA:
    """Parse a DFA from a .dfauto file."""
    if not path.endswith(".dfauto"):
        raise ValueError(f"Expected .dfauto file, got {path}.")

    with open(path, 'r') as f:
        lines = f.readlines()

    Q, Σ_num, Σ, _δ, q0, F = _parse_automaton_data(lines)
    if not Σ:
        Σ = [chr(ord('a') + i) for i in range(Σ_num)]

    δ: Mapping[Tuple[str, str], str] = {}

    for src, line in enumerate(_δ, start=0):
        parts = [x.strip() for x in line.split(',')]
        if len(parts) != Σ_num:
            raise ValueError(
                f"Transition line {src+3} has {len(parts)} items, expected {Σ_num}."
            )
        for sym, dst_raw in enumerate(parts, start=0):
            dst = int(dst_raw)
            δ[(Q[src], Σ[sym])] = Q[dst]

    return DFA(frozenset(Q), frozenset(Σ), δ, q0, frozenset(F))


def parse_nfa_file(path: str) -> NFA:
    """Parse an NFA from a .nfauto file."""
    if not path.endswith(".nfauto"):
        raise ValueError(f"Expected .nfauto file, got {path}.")

    with open(path, 'r') as f:
        lines = f.readlines()

    Q, Σ_num, Σ, _δ, q0, F = _parse_automaton_data(lines)

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
    for src, line in enumerate(_δ, start=0):
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

    return NFA(frozenset(Q), frozenset(Σ), δ, q0, frozenset(F))


AUTOMATON_PARSERS: dict[str, tuple[Type[Automaton[Any, Any]], Callable[[str], Automaton[Any, Any]]]] = {
    ".dfauto": (DFA, parse_dfa_file),
    ".nfauto": (NFA, parse_nfa_file),
}
