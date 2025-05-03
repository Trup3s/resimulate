import logging
import os

from resimulate.euicc.card import Card
from resimulate.euicc.models.reset_option import ResetOption
from resimulate.euicc.mutation.engine import MutationEngine
from resimulate.euicc.recorder.recorder import OperationRecorder
from resimulate.euicc.transport.pcsc_link import PcscLink
from resimulate.scenarios.models.scenario import Scenario
from resimulate.euicc import exceptions


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

    def __clear_card(self, card: Card):
        profiles = card.isd_r.get_profiles()
        for profile in profiles:
            card.isd_r.delete_profile(profile.iccid)

        notifications = card.isd_r.retrieve_notification_list()
        if notifications:
            card.isd_r.process_notifications(notifications)

        try:
            card.isd_r.reset_euicc_memory(reset_options=ResetOption.all())
        except exceptions.NothingToDeleteError:
            pass

    def record_card(
        self,
        card_name: str,
        path: str | None = None,
        overwrite: bool = False,
        mutation_engine: MutationEngine | None = None,
    ):
        recorder = OperationRecorder()
        with PcscLink(recorder=recorder, mutation_engine=mutation_engine) as link:
            card = Card(link)
            self.__clear_card(card)

            for scenario_cls in self.scenarios:
                scenario_name = scenario_cls.__qualname__
                if mutation_engine:
                    scenario_name = (
                        f"{scenario_name}_{type(mutation_engine).__qualname__}"
                    )
                logging.info(f"Recording scenario: {scenario_name}")
                try:
                    scenario_cls(link).run(card)
                except Exception as e:
                    logging.error(f"Error running scenario {scenario_name}: {e}")
                    logging.exception(e)
                finally:
                    try:
                        card.isd_r.reset_euicc_memory(reset_options=ResetOption.all())
                    except exceptions.EuiccException:
                        logging.warning("Card is not in a clean state. Skipping reset.")

                file_name = f"{card_name}_{scenario_name}.resim"
                if path:
                    file_path = os.path.join(path, file_name)
                else:
                    file_path = file_name

                if os.path.exists(file_path):
                    if not overwrite:
                        logging.warning(f"File {file_path} already exists. Skipping.")
                        continue

                    logging.warning(f"File {file_path} already exists. Overwriting.")

                recorder.save_file(file_path)
                recorder.clear()
                link.reset_card()
