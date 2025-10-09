from collections import deque
from typing import List, Optional
from automata.dfa import DFA
from automata.nfa import NFA
from automata.utils import words_for_path

StatePath = List[str]


class Sampler:
    class SampleNode:
        def __init__(self, state: str, parent: Optional["Sampler.SampleNode"] = None):
            self.state = state
            self.prev = parent
            self.depth = parent.depth + 1 if parent else 1

        def get_possible_words(self, auto: DFA | NFA) -> set[str]:
            if not self.prev:
                return {""}

            cur_node = self
            rev_path: list[str] = []

            while cur_node:
                rev_path.append(cur_node.state)
                cur_node = cur_node.prev

            return words_for_path(rev_path[::-1], auto.edges if isinstance(auto, DFA) else auto.closed_edges)

    def __init__(self, auto: DFA | NFA):
        self._auto = auto

        self._queue: deque[Sampler.SampleNode] = deque()
        if isinstance(auto, DFA):
            self._queue.append(Sampler.SampleNode(auto.q0))
        else:
            self._queue.extend(Sampler.SampleNode(s)
                               for s in auto.epsilon_closure(auto.q0))

        self._samples: set[str] = set()

    def path_between_exists(self, state: str, end_states: set[str] | frozenset[str]) -> bool:
        def rec(state: str, visited: set[str]) -> bool:
            if state in visited:
                return False

            for ns in self._auto.edges[state]:
                if ns in end_states:
                    return True
                if rec(ns, visited | {state}):
                    return True

            return False

        return rec(state, set())

    def sample(self, *, max_samples: int = 10, max_depth: int = 10) -> List[str]:
        dead_end_states: set[str] = set()

        for state in self._auto.Q:
            # checks if state can lead to accepting state
            if not self.path_between_exists(state, self._auto.F):
                dead_end_states.add(state)

        while self._queue:
            node = self._queue.popleft()

            if node.state in self._auto.F:
                self._samples |= node.get_possible_words(self._auto)

            if len(self._samples) >= max_samples:
                break

            if node.state in dead_end_states:
                continue

            if node.depth < max_depth:
                for sym in self._auto.Σ:
                    if isinstance(self._auto, DFA):
                        next_states = {self._auto.transition(node.state, sym)}
                    else:
                        next_states = self._auto.transition(node.state, sym)

                    self._queue.extend(Sampler.SampleNode(
                        next_state, node) for next_state in next_states)

        return list(sorted(self._samples, key=lambda s: (len(s), s))[:max_samples])
