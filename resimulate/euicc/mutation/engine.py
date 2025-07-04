import random
from abc import ABC, abstractmethod

from resimulate.euicc.transport.apdu import APDUPacket


class MutationEngine(ABC):
    def __init__(
        self,
        mutation_rate: float = 0.01,
        seed: int | float | str | bytes | bytearray | None = None,
    ):
        self.mutation_rate = mutation_rate
        random.seed(seed)

    @abstractmethod
    def mutate(
        self,
        apdu: APDUPacket,
    ) -> APDUPacket:
        raise NotImplementedError("This method should be overridden in subclasses.")
