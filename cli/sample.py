import argparse
import heapq
import random
from pathlib import Path
from collections import defaultdict
from typing import Any, Dict, Hashable, List, Optional

from automata.dfa import DFA
from automata.parser import parse_dfa_file
from automata.utils import cprint


def find_simple_path(dfa: DFA, state: str, seq: list[str], end_states: set[str]=None):
    results = []
    if state in (end_states or dfa.F):
        results.append(seq + [state])

    for (dst, _) in dfa.edges[state].items():
        if dst in seq or dst == state:
            continue
        results.extend(find_simple_path(dfa, dst, seq + [state], end_states))

    return results


def find_state_loops(dfa, state):
    next_state = set([dfa.transition(state, sym) for sym in dfa.Σ])

    results = []
    for ns in next_state:
        results.extend(find_simple_path(dfa, ns, [], set([state])))

    return results

class SamplePQ:
    def __init__(self):
        self.samples_by_length: Dict[int, List[Any]] = defaultdict(list)
        self._min_heap: List[int] = []
        self._nonempty: set[int] = set()

    def __len__(self):
        return sum(len(v) for v in self.samples_by_length.values())
    
    def __repr__(self) -> str:
        parts = []
        for k in sorted(self.samples_by_length.keys()):
            samples = self.samples_by_length[k]
            if samples:
                parts.append(f"{k}: {samples}")
        return f"<SamplePQ total={len(self)} samples={{" + ", ".join(parts) + "}}>"

    
    def _ensure_key(self, k: int) -> None:
        if k not in self._nonempty:
            heapq.heappush(self._min_heap, k)
            self._nonempty.add(k)

    def _gc_heap(self) -> None:
        while self._min_heap and self._min_heap[0] not in self._nonempty:
            k = heapq.heappop(self._min_heap)
            self._nonempty.discard(k)

    def push(self, sample: Any) -> None:
        k = len(sample)
        self.samples_by_length[k].append(sample)
        self._ensure_key(k)

    def push_many(self, samples: List[Any]) -> None:
        for sample in samples:
            self.push(sample)

    def peek(self) -> Optional[int]:
        self._gc_heap()
        return self._min_heap[0] if self._min_heap else None
    
    def pop_random(self) -> Any:
        self._gc_heap()
        if not self._min_heap:
            raise IndexError("pop from empty SamplePQ")
        
        k = self._min_heap[0]
        samples = self.samples_by_length[k]

        idx = random.randrange(len(samples))
        sample = samples[idx]

        samples[idx] = samples[-1]
        samples.pop()

        if not samples:
            self._nonempty.discard(k)
            heapq.heappop(self._min_heap)

        return sample
    

def main():
    ap = argparse.ArgumentParser(
        description="Simulate DFA on input strings from a .dfauto file")
    ap.add_argument("input", help="Path to .dfauto file")
    args = ap.parse_args()

    dfa = parse_dfa_file(args.input)

    limit, max_len = 5, 5
    simple_accepted_paths = find_simple_path(dfa, dfa.q0, [])  
    # print("Accepted", simple_accepted_paths)

    # for state_seq in simple_accepted_paths:
    #     print(dfa.words_for_path(state_seq))

    state_loops = {}
    for state in dfa.Q:
        state_loops[state] = find_state_loops(dfa, state)

        # print(state, loops)

    pq = SamplePQ()
    pq.push_many(simple_accepted_paths)
    print(pq)

    for i in range(3):
        if len(pq) == 0:
            break
        path = pq.pop_random()
        new_paths = []

        print("path", path, "pq", pq)
        
        for state_idx in range(len(path)):
            state = path[state_idx]
            
            for loop in state_loops[state]:
                new_path = path[:state_idx+1] + loop + path[state_idx+1:]
                print("  loop", loop, "->", new_path)
                new_paths.append(new_path)

        pq.push_many(new_paths)
        print(pq)
        


if __name__ == "__main__":
    main()
