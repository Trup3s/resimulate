from abc import ABC, abstractmethod

from resimulate.legacy_pcsc_link import PcscLink


class Scenario(ABC):
    def __init__(self, link: PcscLink):
        self.link = link

    @abstractmethod
    def run(self):
        raise NotImplementedError("Scenario must implement the run method.")


SCENARIOS = [cls for cls in Scenario.__subclasses__()]
