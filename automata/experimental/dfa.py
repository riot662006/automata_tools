from automata.experimental.reg_auto import RegAuto


class DFA(RegAuto):
    # --- validation / execution ---
    def is_valid_dfa(self) -> bool:
        if not any(not s.is_dead() for s in self.states):
            return False
        if not any(not a.is_dead() for a in self.alphabet):
            return False
        for sid, s in enumerate(self.states):
            if s.is_dead():
                continue
            for aid, a in enumerate(self.alphabet):
                if a.is_dead():
                    continue
                live_dsts = {d for d in self._tx.delta.get(
                    (sid, aid), set()) if not self.states[d].is_dead()}
                if len(live_dsts) != 1:
                    return False
        return True

    def validate_edit(self):
        if not self.is_valid_dfa():
            raise ValueError(
                "Invalid DFA after edit() — each (state, symbol) must have exactly one destination."
            )
