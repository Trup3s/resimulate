import logging
import pickle

from resimulate.euicc.recorder.operation import Operation
from resimulate.util.name_generator import generate_name


class OperationRecorder:
    def __init__(self):
        self.recordings: list[Operation] = []
        self.atr = None
        self.name = None

    def record(self, operation: Operation):
        self.recordings.append(operation)
        logging.debug(
            f"Recorded operation: {operation.func_name} with {len(operation.mutation_recordings)} mutations"
        )

    def clear(self):
        self.recordings.clear()

    def save_file(self, file_path: str):
        logging.debug(f"Saving recording to {file_path}")
        with open(file_path, "wb") as f:
            pickle.dump(self, f)

    def compare(
        self,
        compare_recorder: "OperationRecorder",
    ):
        main_name = self.name or generate_name(self.atr)
        compare_name = compare_recorder.name or generate_name(compare_recorder.atr)
        differences = {}

        logging.debug(f"Comparing {main_name} with {compare_name}")

        for main_operation in self.recordings:
            operations_by_func_name = {
                operation.func_name: operation
                for operation in compare_recorder.recordings
            }
            compare_operation = operations_by_func_name.get(main_operation.func_name)

            if not compare_operation:
                continue

            compare_difference = main_operation.compare(compare_operation)

            if compare_difference:
                differences[main_operation.func_name] = compare_difference
                logging.debug(
                    f"Found differences in {main_operation.func_name}: {compare_difference}"
                )

        return {"main": main_name, "compare": compare_name, "differences": differences}

    @staticmethod
    def compare_multiple(
        main_recording: "OperationRecorder",
        compare_recordings: list["OperationRecorder"],
    ):
        differences = []
        for compare_recording in compare_recordings:
            diff = main_recording.compare(compare_recording)

            if diff["differences"]:
                differences.append(diff)

        return differences

    @staticmethod
    def compare_files(main_recording_path: str, compare_recording_paths: list[str]):
        with open(main_recording_path, "rb") as f:
            main_recorder: "OperationRecorder" = pickle.load(f)
            main_recorder.name = main_recording_path

        compare_recordings = []
        for compare_recording_path in compare_recording_paths:
            with open(compare_recording_path, "rb") as f:
                compare_recorder: "OperationRecorder" = pickle.load(f)
                compare_recorder.name = compare_recording_path

                compare_recordings.append(compare_recorder)
                logging.debug(
                    f"Loaded compare recording: {compare_recording_path} with {len(compare_recorder.recordings)} mutations"
                )

        return OperationRecorder.compare_multiple(
            main_recorder,
            compare_recordings,
        )
