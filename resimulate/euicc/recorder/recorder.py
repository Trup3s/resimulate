import logging
import pickle

from resimulate.euicc.mutation.types import MutationType
from resimulate.euicc.recorder.operation import (
    MutationRecording,
    MutationTreeNode,
)
from resimulate.util.name_generator import generate_name


class OperationRecorder:
    answer_to_request = None
    name = None
    root: MutationTreeNode
    current_node: MutationTreeNode

    def __init__(self):
        self.clear()

    def record(self, recording: MutationRecording):
        self.current_node.recording = recording

    def add_new_mutation_node(self, func_name: str, mutation_type: MutationType):
        node = MutationTreeNode(func_name=func_name, mutation_type=mutation_type)
        self.current_node.add_child(node)
        self.current_node = node

    def get_next_mutation(self, func_name: str) -> MutationTreeNode | None:
        not_tried_mutations = self.current_node.get_not_tried_mutations()
        if not_tried_mutations:
            logging.debug("Current node has not tried mutations...")
            mutation_type = not_tried_mutations.pop()
            self.add_new_mutation_node(
                func_name=func_name,
                mutation_type=mutation_type,
            )
            return mutation_type

        none_mutation_node = None
        for child in self.current_node.children:
            if child.failure_reason:
                continue

            not_tried_mutations = child.get_not_tried_mutations()

            if not_tried_mutations:
                self.current_node = child
                logging.debug(
                    f"Found a child with not tried mutations: {child.func_name} -> {child.mutation_type}"
                )
                return child.mutation_type

            if child.mutation_type is MutationType.NONE:
                none_mutation_node = child

        assert none_mutation_node is not None, "No child with NONE mutation node found!"
        logging.debug(
            "Could not find a child with not tried mutations, continuing with NONE mutation node!"
        )
        return none_mutation_node

    def clear(self):
        self.root = MutationTreeNode(func_name="root", mutation_type=MutationType.NONE)
        self.current_node = self.root
        logging.debug("Cleared all recorded operations")

    def reset(self):
        logging.debug("Resetting recorder")
        self.current_node = self.root

    def save_file(self, file_path: str):
        logging.debug(f"Saving recording to {file_path}")
        with open(file_path, "wb") as f:
            pickle.dump(self, f)

    def compare(
        self,
        compare_recorder: "OperationRecorder",
    ):
        return self.root.compare(other=compare_recorder.root)

    @staticmethod
    def compare_multiple(
        main_recording: "OperationRecorder",
        compare_recordings: list["OperationRecorder"],
    ):
        differences = {}
        main_name = main_recording.name or generate_name(
            main_recording.answer_to_request
        )
        for compare_recording in compare_recordings:
            compare_name = compare_recording.name or generate_name(
                compare_recording.answer_to_request
            )

            logging.debug(f"Comparing main {main_name} with {compare_name}")
            diff = main_recording.compare(compare_recording)

            if diff:
                differences[main_name, compare_name] = diff
            else:
                logging.debug(
                    f"No differences found between {main_name} and {compare_name}"
                )

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
                logging.debug(f"Loaded compare recording: {compare_recording_path}")

        return OperationRecorder.compare_multiple(
            main_recorder,
            compare_recordings,
        )
