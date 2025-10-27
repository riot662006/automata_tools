from typing import Generator
from abc import ABC, abstractmethod


class RegExpr(ABC):
    def __init__(self, pattern: str):
        self.pattern = pattern
    
    @abstractmethod
    def read(self, string: str) -> Generator[str, None, None]:
        pass
    
    @abstractmethod
    def sample(self) -> str:
        pass
        