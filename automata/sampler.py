from collections import defaultdict, deque
from typing import Dict, List, Optional
from automata.dfa import DFA

StatePath = List[str]


class Sampler:
    class SampleNode:
        def __init__(self, state: str, parent: Optional["Sampler.SampleNode"] = None):
            self.state = state
            self.prev = parent
            self.depth = parent.depth + 1 if parent else 1
            
        def get_possible_words(self, dfa: DFA) -> set[str]:
            cur_node = self
            rev_path = []
            
            while cur_node:
                rev_path.append(cur_node.state)
                cur_node = cur_node.prev
                
            return dfa.words_for_path(rev_path[::-1])
            
    def __init__(self, dfa: DFA):
        self._dfa = dfa
        
        self._queue = deque()
        self._queue.append(Sampler.SampleNode(dfa.q0))
        
        self._samples = set()
            
    def sample(self, *, max_samples = 10, max_depth = 10) -> List[str]:
        while self._queue:
            node = self._queue.popleft()
            
            if node.state in self._dfa.F:
                self._samples |= node.get_possible_words(self._dfa)
                
            if len(self._samples) >= max_samples:
                break
            
            if node.depth < max_depth:
                for sym in self._dfa.Σ:
                    next_state = self._dfa.transition(node.state, sym)
                    self._queue.append(Sampler.SampleNode(next_state, node))
                    
        return list(sorted(self._samples, key=lambda s: (len(s), s))[:max_samples])