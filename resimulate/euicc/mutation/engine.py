from abc import ABC, abstractmethod

from resimulate.euicc.transport.apdu import APDUPacket


class MutationEngine(ABC):
    def __init__(
        self,
        mutation_rate: float = 0.01,
    ):
        self.mutation_rate = mutation_rate

    @abstractmethod
    def mutate(
        self,
        apdu: APDUPacket,
    ) -> APDUPacket:
        raise NotImplementedError("This method should be overridden in subclasses.")
