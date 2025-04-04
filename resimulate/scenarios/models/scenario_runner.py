import logging

from resimulate.euicc.card import Card
from resimulate.euicc.recorder.recorder import OperationRecorder
from resimulate.euicc.transport.pcsc_link import PcscLink
from resimulate.scenarios.models.scenario import Scenario


class ScenarioRunner:
    def __init__(self, scenarios: list[type[Scenario]]):
        self.scenarios = scenarios

    def run_scenarios(self):
        recorder = OperationRecorder()
        with PcscLink(recorder=recorder) as link:
            card = Card(link)
            for scenario in self.scenarios:
                logging.debug(f"Running scenario: {scenario}")
                scenario_instance = scenario(link)
                try:
                    scenario_instance.run(card)
                except Exception as e:
                    logging.error(f"Error running scenario {scenario}: {e}")
                    logging.exception(e)
                    continue
                finally:
                    link.reset_card()

    def record_card(self, name: str):
        recorder = OperationRecorder()
        with PcscLink(recorder=recorder) as link:
            card = Card(link)
            for scenario_cls in self.scenarios:
                scenario_cls(link).run(card)
                recorder.save_file(f"{name}_{str(scenario_cls)}")
                recorder.clear()
                link.reset_card()
