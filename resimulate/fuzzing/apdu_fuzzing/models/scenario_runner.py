import logging
import os

from asn1tools.codecs.ber import DecodeTagError

from resimulate.euicc.card import Card
from resimulate.euicc.exceptions import EuiccException, NothingToDeleteError
from resimulate.euicc.models.reset_option import ResetOption
from resimulate.euicc.mutation.engine import MutationEngine
from resimulate.euicc.recorder.recorder import OperationRecorder
from resimulate.euicc.transport.pcsc_link import PcscLink
from resimulate.fuzzing.apdu_fuzzing.models.exceptions import ScenarioException
from resimulate.fuzzing.apdu_fuzzing.models.scenario import Scenario
from resimulate.smdp.exceptions import SmdpException


class ScenarioRunner:
    def __init__(self, scenarios: list[type[Scenario]]):
        self.scenarios = scenarios

    def run_scenarios(self):
        with PcscLink() as link:
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
                    link._reset_card()

    def __clear_card(self, card: Card):
        notifications = card.isd_r.retrieve_notification_list()
        if notifications:
            card.isd_r.process_notifications(notifications)

        try:
            card.isd_r.reset_euicc_memory(reset_options=ResetOption.all())
        except NothingToDeleteError:
            pass

    def record_card(
        self,
        card_name: str,
        mutation_engine: MutationEngine,
        path: str | None = None,
        overwrite: bool = False,
        apdu_data_size: int = 255,
    ):
        recorder = OperationRecorder()
        with PcscLink(recorder=recorder, apdu_data_size=apdu_data_size) as link:
            card = Card(link)
            self.__clear_card(card)

            link.mutation_engine = mutation_engine
            for scenario_cls in self.scenarios:
                scenario_name = scenario_cls.__qualname__
                if mutation_engine:
                    scenario_name = (
                        f"{scenario_name}_{type(mutation_engine).__qualname__}"
                    )
                logging.info(f"Recording scenario: {scenario_name}")
                while True:
                    try:
                        scenario_cls(link).run(card)
                        recorder.current_node.leaf = True
                    except (EuiccException, SmdpException, DecodeTagError) as e:
                        logging.debug(
                            f"Scenario {scenario_name} failed on operation {recorder.current_node.func_name}... Resetting and continuing!"
                        )
                        recorder.current_node.failure_reason = e.__class__.__name__
                        continue
                    except ScenarioException as e:
                        logging.debug(
                            f"Scenario {scenario_name} failed with scenario exception: {e}. Stopping..."
                        )
                        break
                    finally:
                        link.mutation_engine = None
                        try:
                            self.__clear_card(card)
                        except Exception:
                            logging.debug(
                                "Failed to clear card after scenario execution"
                            )

                        link.mutation_engine = mutation_engine
                        recorder.reset()

                    if not recorder.root.has_not_tried_mutations():
                        logging.info(
                            f"Scenario {scenario_name} finished with all mutations tried!"
                        )
                        recorder.root.print_tree()
                        break

                    logging.debug(
                        f"Scenario {scenario_name} finished with untried mutations! Continuing..."
                    )

                file_name = f"{card_name}_{scenario_name}.resim"
                if path:
                    file_path = os.path.join(path, file_name)
                else:
                    file_path = file_name

                if os.path.exists(file_path):
                    if not overwrite:
                        logging.debug(f"File {file_path} already exists. Skipping.")
                        continue

                    logging.debug(f"File {file_path} already exists. Overwriting.")

                recorder.save_file(file_path)
                recorder.clear()
                link._reset_card()
