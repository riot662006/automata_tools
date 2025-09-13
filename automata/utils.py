import re


def cprint(message: str, color: str = "reset", *, bold: bool = False, end: str = "\n") -> None:
    """
    Print a colored message to the terminal (ANSI escape codes, no extra deps).

    Args:
        message: The text to print.
        color:   One of {"green", "red", "yellow", "blue", "magenta", "cyan", "reset"}.
        bold:    If True, apply bold style.
        end:     Passed to print() (default newline).
    """
    codes = {
        "green": "32",
        "red": "31",
        "yellow": "33",
        "blue": "34",
        "magenta": "35",
        "cyan": "36",
        "reset": "0",
    }

    code = codes.get(color, "0")
    style = "1;" if bold else ""
    start = f"\033[{style}{code}m"
    reset = "\033[0m"

    print(f"{start}{message}{reset}", end=end)


COUNTED_LIST_RE = re.compile(r"""
    ^\s*
    (?P<count>\d+)                    # leading number
    (?:\s*\[\s*(?P<inside>.*?)\s*\]\s*)?   # optional [ ... ]
    \s*$
""", re.VERBOSE)

# Q-labels: identifiers like q_1, fooBar, _x2
Q_LABEL_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

# Σ-labels: exactly one "word" character (letter, digit, or underscore, Unicode-safe).
SIGMA_LABEL_RE = re.compile(r"^\w$", re.UNICODE)


def parse_counted_list(s: str, label_re):
    """
    Parse 'N' or 'N [a, b, c]'.
    Splits items by comma, strips whitespace, and requires each token to FULLY match label_re.
    Raises ValueError on format problems or count mismatch.
    """
    m = COUNTED_LIST_RE.match(s)
    if not m:
        raise ValueError("Expected '<num>' or '<num> [items]'.")

    count = int(m.group("count"))
    inside = m.group("inside")

    # No bracketed list present → return empty items
    if not inside or inside.strip() == "":
        return count, None

    # Split on commas and strip
    raw_items: list[str] = [part.strip() for part in inside.split(",")]

    # Detect empty tokens (e.g., trailing comma, double commas)
    if any(tok == "" for tok in raw_items):
        # pinpoint where the empty token is
        bad_idx = next(i for i, tok in enumerate(raw_items) if tok == "")
        raise ValueError(f"Empty item at position {bad_idx+1} in list.")

    # Validate each token with FULL MATCH against label_re
    for i, tok in enumerate(raw_items, start=1):
        if not label_re.fullmatch(tok):
            raise ValueError(
                f"Invalid token at position {i}: {tok!r} does not match {label_re.pattern!r}"
            )

    # Count check
    if len(raw_items) != count:
        raise ValueError(
            f"Count mismatch: number says {count} but list has {len(raw_items)} items."
        )

    # Unique check
    if len(set(raw_items)) != len(raw_items):
        raise ValueError(
            "Duplicate items found in the list. Items must be unique.")

    return count, raw_items
