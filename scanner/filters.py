from abc import abstractmethod

from models.program import Program


class Filter:
    @abstractmethod
    def check(self, program: Program) -> bool:
        pass
