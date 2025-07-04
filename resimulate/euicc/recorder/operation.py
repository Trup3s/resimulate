from __future__ import annotations

import random
from dataclasses import dataclass, field

from resimulate.euicc.mutation.types import MutationType
from resimulate.euicc.transport.apdu import APDUPacket
from resimulate.util.color import Colors


@dataclass
class MutationRecording:
    original_apdu: APDUPacket
    mutated_apdu: APDUPacket
    response_sw: str
    response_data: str | None = None

    def is_different(self, other: MutationRecording) -> bool:
        return self.response_sw != other.response_sw


@dataclass
class MutationTreeNode:
    func_name: str
    mutation_type: MutationType
    failure_reason: str | None = None
    leaf: bool = False
    parent: MutationTreeNode | None = None
    recording: MutationRecording | None = None
    children: list["MutationTreeNode"] = field(default_factory=list)
    trace: list[MutationRecording] = field(default_factory=list)

    def add_child(self, child: MutationTreeNode) -> None:
        self.children.append(child)
        child.parent = self

    def get_not_tried_mutations(self) -> list[MutationType]:
        tried_mutations = [node.mutation_type for node in self.children]
        not_tried_mutations = list(set(MutationType).difference(tried_mutations))

        # if (
        #     self.func_name == "get_euicc_info_1"
        #     and MutationType.TRUNCATE in not_tried_mutations
        # ):
        #     not_tried_mutations.remove(MutationType.TRUNCATE)
        #     not_tried_mutations.append(MutationType.TRUNCATE)
        #     return not_tried_mutations

        # if (
        #     self.func_name not in ["get_euicc_info_1", "get_euicc_challenge"]
        #     and MutationType.NONE in not_tried_mutations
        # ):
        #     return sorted(not_tried_mutations, reverse=True)

        if self.has_parent_with(
            func_name="authenticate_server", mutation_type=MutationType.TRUNCATE
        ) or (
            self.func_name == "authenticate_server"
            and self.mutation_type == MutationType.TRUNCATE
        ):
            return sorted(not_tried_mutations, reverse=True)

        random.shuffle(not_tried_mutations)
        return not_tried_mutations

    def has_parent_with(
        self, func_name: str | None = None, mutation_type: MutationType | None = None
    ) -> bool:
        if not self.parent:
            return False

        if (func_name is None or self.parent.func_name == func_name) and (
            mutation_type is None or self.parent.mutation_type == mutation_type
        ):
            return True

        return self.parent.has_parent_with(func_name, mutation_type)

    def has_not_tried_mutations(self) -> bool:
        if self.failure_reason or self.leaf:
            return False

        if self.get_not_tried_mutations():
            return True

        for child in self.children:
            if child.has_not_tried_mutations():
                return True

        return False

    def is_different(self, other: MutationTreeNode) -> bool:
        if self.mutation_type != other.mutation_type:
            return True

        if self.failure_reason != other.failure_reason:
            return True

        if self.recording and other.recording:
            return self.recording.is_different(other.recording)

        return False

    def is_successful_branch(self) -> bool:
        if self.leaf and self.failure_reason is None:
            return True

        for child in self.children:
            if child.is_successful_branch():
                return True

        return False

    def compare(self, other: MutationTreeNode | None) -> dict[str, dict[str, str]]:
        if not other:
            return {
                "main": (self.recording.response_sw, self.failure_reason),
                "compare": None,
            }

        if self.func_name != other.func_name:
            raise ValueError(
                f"Cannot compare nodes with different function names: "
                f"{self.func_name} vs {other.func_name}"
            )

        differences = {}
        child_diff = {}

        if self.is_different(other):
            differences = {
                "main": (self.recording.response_sw, self.failure_reason),
                "compare": (other.recording.response_sw, other.failure_reason),
            }

        for child in self.children:
            key = (child.func_name, child.mutation_type.name)
            other_child = next(
                (c for c in other.children if c.mutation_type == child.mutation_type),
                None,
            )
            if not other_child:
                continue

            children_diff = child.compare(other_child)
            if children_diff:
                child_diff[key] = children_diff

        if child_diff:
            differences["children"] = child_diff

        return differences

    def print_tree(self, last: bool = True, header: str = "", warning: bool = False):
        elbow = "└──"
        tee = "├──"
        pipe = "│  "
        blank = "   "

        if self.parent is None:
            prefix = ""
        else:
            prefix = elbow if last else tee

        status = [
            self.mutation_type,
            self.failure_reason if self.failure_reason else "success",
        ]
        postfix = f"({', '.join(status)})" if self.parent else ""

        branch_message = f"{self.func_name} {postfix}"
        mark_branch = (
            self.mutation_type != MutationType.NONE or warning
        ) and self.is_successful_branch()
        mark_node = (
            self.mutation_type != MutationType.NONE or warning
        ) and self.children != []
        if mark_branch or mark_node:
            print(f"{header}{prefix} {Colors.WARNING}{branch_message}{Colors.ENDC}")
        else:
            print(f"{header}{prefix} {Colors.OKGREEN}{branch_message}{Colors.ENDC}")

        for i, child in enumerate(self.children):
            is_last = i == len(self.children) - 1
            child_header = header + (blank if last else pipe)
            child.print_tree(last=is_last, header=child_header, warning=mark_branch)
