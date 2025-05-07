import re
from abc import ABC, abstractmethod

from resimulate.euicc.card import Card
from resimulate.euicc.transport.pcsc_link import PcscLink


class Scenario(ABC):
    """Scenario base class. A scenario represents a sequence of commands to be executed on the card."""

    def __init__(self, link: PcscLink):
        self.link = link

    def __str__(self):
        return re.sub(r"(?<!^)(?=[A-Z])", "_", self.__class__.__name__).lower()

    @abstractmethod
    def run(self, card: Card):
        """Runs a scenario on the card.

        Args:
            card (Card): Card object to run the scenario on.
        """
        raise NotImplementedError("Scenario must implement the run method.")
