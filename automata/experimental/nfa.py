# automata/experimental/reg_auto.py
from typing import Iterable
import weakref

from automata.experimental.reg_auto import RegAuto


class NFA(RegAuto):
    """
    NFA over live letters in Σ *excluding* ε.
    ε is a reserved live letter present in the index/δ view but not in Σ.
    """

    _EPSILON_CHAR = "ε"  # you can choose another symbol if you like

    def __init__(
        self,
        Q: set[str],
        Σ: set[str],
        δ: dict[tuple[str, str], Iterable[str] | str],
        q0: str,
        F: set[str],
    ):
        self.states: list[RegAuto.State] = []
        self.name_to_sid: dict[str, int] = {}

        #  Create epsilon as a reserved letter that callers can't touch.
        self.alphabet: list[RegAuto.Letter] = [RegAuto.Letter(
            self._EPSILON_CHAR, _owner=weakref.ref(self))]
        self.char_to_aid: dict[str, int] = {self._EPSILON_CHAR: 0}

        # Mark ε as reserved so public mutators can enforce uneditable/unremovable
        self._epsilon_aid = 0
        self._reserved_aids = {self._epsilon_aid}

        # Cache for ε-closure computation.
        self._eps_closure_cache: dict[int, set[int]] = {}

        self._tx = RegAuto._Index()
        self._editing = False

        with self.edit():
            self.add_states(Q)

            # If user tried to include ε in Σ, ignore—NFA controls it.
            if self._EPSILON_CHAR in Σ:
                Σ = {ch for ch in Σ if ch != self._EPSILON_CHAR}
            self.add_letters(Σ)

            self.add_transitions(δ)

        self.start_sid = self._sid_of(q0)
        self.final_sids: set[int] = {self._sid_of(f) for f in F}

    # ---------------- cache helpers ----------------
    def _invalidate_eps_cache(self) -> None:
        self._eps_closure_cache.clear()

    def _eps_closure_single(self, sid: int) -> set[int]:
        """Compute ε-closure({sid}) with lazy memoization (live states only)."""
        if sid in self._eps_closure_cache:
            return self._eps_closure_cache[sid]

        if self.states[sid].is_dead():
            res: set[int] = set()
            self._eps_closure_cache[sid] = res
            return res

        eps = self._epsilon_aid
        seen: set[int] = set()
        stack = [sid]
        while stack:
            u = stack.pop()
            if u in seen or self.states[u].is_dead():
                continue
            seen.add(u)
            for v in self._tx.delta.get((u, eps), set()):
                if not self.states[v].is_dead() and v not in seen:
                    stack.append(v)

        self._eps_closure_cache[sid] = seen
        return seen

    def _eps_closure(self, sids: Iterable[int]) -> set[int]:
        """Union of memoized singleton closures."""
        out: set[int] = set()
        for sid in sids:
            out |= self._eps_closure_single(sid)
        return out

    # -------------- Overrides to protect ε --------------

    def rename_letter(self, old: str, new: str) -> None:
        if old == self._EPSILON_CHAR:
            raise RuntimeError("Cannot rename the reserved epsilon letter.")
        if new == self._EPSILON_CHAR:
            raise RuntimeError("Cannot rename any letter to epsilon.")
        return super().rename_letter(old, new)

    def remove_letters(self, letters: Iterable[str]) -> None:
        # Throw if user tries to remove ε
        if self._EPSILON_CHAR in letters:
            raise RuntimeError("Cannot remove the reserved epsilon letter.")

        if not letters:
            return
        return super().remove_letters(letters)

    def add_letters(self, letters: Iterable[str]) -> None:
        # Prevent user from (re)adding ε via public API
        letters = [ch for ch in letters if ch != self._EPSILON_CHAR]
        if not letters:
            return
        return super().add_letters(letters)

    # -------------- Properties --------------

    @property
    def Σ(self) -> set[str]:
        """Live letters excluding epsilon."""
        return {
            a.char for i, a in enumerate(self.alphabet)
            if not a.is_dead() and i not in self._reserved_aids
        }

    @property
    def δ(self) -> dict[tuple[str, str], set[str]]:
        """
        Transition table (names) including epsilon rows.
        Matches your requirement: ε shows up in transition table and index,
        but Σ excludes it.
        """
        out: dict[tuple[str, str], set[str]] = {}
        for (sid, aid), dsts in self._tx.delta.items():
            s = self.states[sid]
            a = self.alphabet[aid]
            if s.is_dead():
                continue
            # NOTE: we do NOT skip epsilon here; it appears in δ.
            live = {
                self.states[d].name for d in dsts if not self.states[d].is_dead()
            }
            if not a.is_dead():
                out[(s.name, a.char)] = live
            else:
                # If a letter is dead (never epsilon), still skip it in δ.
                continue
        return out

    # -------------- NFA semantics --------------

    def transition(self, s_id: int, a_id: int, throw_on_dead: bool = True) -> set[int]:
        """
        NFA move on a single non-epsilon symbol from the ε-closure of s_id.
        (You can still call with ε aid directly; it will behave like RegAuto.transition.)
        """
        # make sure not editing at the same time
        if self._editing:
            raise RuntimeError("Cannot call NFA transition while editing.")

        # If caller passes ε, keep base behavior:
        if a_id in self._reserved_aids:
            return super().transition(s_id, a_id, throw_on_dead=throw_on_dead)

        # Move from ε-closure(s_id) on symbol a_id, then take ε-closure of the union.
        start = self._eps_closure([s_id])
        dst_union: set[int] = set()
        for sid in start:
            dst_union |= super().transition(sid, a_id, throw_on_dead=throw_on_dead)
        return self._eps_closure(dst_union)

    def accepts(self, word: str) -> bool:
        """Standard ε-NFA simulation."""
        # Start from ε-closure of q0
        states = self._eps_closure([self.start_sid])

        for ch in word:
            if ch not in self.Σ:
                raise ValueError(f"Symbol {ch!r} not in alphabet Σ = {self.Σ}")
            aid = self._aid_of(ch)
            new_states: set[int] = set()
            for sid in states:
                new_states |= super().transition(sid, aid, throw_on_dead=True)
            # ε-closure of the union
            states = self._eps_closure(new_states)
            if not states:
                return False

        return any(sid in self.final_sids for sid in states)

    # -------------- Validation --------------

    def validate_edit(self):
        """
        NFAs don’t require totality or determinism.
        We only require:
          - at least one live state and one live letter (ε counts for letters here),
          - reserved epsilon letter stays live.
        """
        if not any(not s.is_dead() for s in self.states):
            raise ValueError("Invalid NFA: no live states.")
        # ensure epsilon remains live
        if self.alphabet[self._epsilon_aid].is_dead():
            raise ValueError("Invalid NFA: epsilon must remain live.")

        self._invalidate_eps_cache()
