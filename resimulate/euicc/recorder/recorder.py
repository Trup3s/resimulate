import logging
import pickle
from typing import TYPE_CHECKING

from resimulate.euicc.recorder.operation import Operation

if TYPE_CHECKING:
    from resimulate.euicc.card import Card


class OperationRecorder:
    def __init__(self):
        self.recordings: list[Operation] = []

    def record(self, operation: Operation):
        self.recordings.append(operation)
        logging.debug(
            f"Recorded operation: {operation.func_name} with mutation {operation.mutation_type}"
        )

    def clear(self):
        self.recordings.clear()

    def save_file(self, file_path: str):
        with open(file_path, "wb") as f:
            pickle.dump(self, f)

    def replay(self, file_path: str, card: "Card"):
        with open(file_path, "rb") as f:
            recorder: "OperationRecorder" = pickle.load(f)

        for operation in recorder.recordings:
            logging.debug(
                f"Replaying operation: {operation.func_name} with mutation {operation.mutation_type}"
            )
            applications_by_name = {
                app.name: app for app in card.supported_applications.values()
            }
            application = applications_by_name.get(operation.application_name)
            if not application:
                raise Exception(f"Application {operation.application_name} not found")

            card.commands.select_adf(application.aid)
            application.__getattribute__(operation.func_name)(
                *operation.original_args, **operation.kwargs
            )

    def compare(self, main_recording: str, compare_recordings: list[str]):
        """Compare recordings to find differences in their sw bytes for the same APDU.

        Args:
            main_recording (str): recording to compare against
            compare_recordings (list[str]): recordings to compare with the main recording
        """
        with open(main_recording, "rb") as f:
            main_recorder: "OperationRecorder" = pickle.load(f)

        for compare_recording in compare_recordings:
            with open(compare_recording, "rb") as f:
                compare_recorder: "OperationRecorder" = pickle.load(f)

            for main_operation in main_recorder.recordings:
                for compare_operation in compare_recorder.recordings:
                    if (
                        main_operation.func_name != compare_operation.func_name
                        or main_operation.mutation_type
                        != compare_operation.mutation_type
                    ):
                        continue

                    if main_operation.response_sw != compare_operation.response_sw:
                        logging.debug(
                            f"Difference found in {main_operation.func_name}: {main_operation.response_sw} vs {compare_operation.response_sw}"
                        )
