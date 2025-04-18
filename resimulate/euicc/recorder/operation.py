from dataclasses import dataclass, field

from resimulate.euicc.transport.apdu import APDUPacket
from resimulate.euicc.mutation.types import MutationType


@dataclass
class MutationRecording:
    mutation_type: MutationType
    original_apdu: APDUPacket
    mutated_apdu: APDUPacket
    response_sw: str

    def is_different(self, other: "MutationRecording") -> bool:
        return (
            self.original_apdu == other.original_apdu
            and self.mutation_type == other.mutation_type
            and self.response_sw != other.response_sw
        )


@dataclass
class Operation:
    application_name: str
    func_name: str
    mutation_recordings: list[MutationRecording] = field(default_factory=list)

    def compare(self, other: "Operation") -> bool:
        if (
            self.application_name != other.application_name
            or self.func_name != other.func_name
        ):
            raise ValueError(
                f"Cannot compare operations with different application names or function names: "
                f"{self.application_name} vs {other.application_name}, "
                f"{self.func_name} vs {other.func_name}"
            )

        recording_by_mutation_type = {
            recording.mutation_type: recording for recording in self.mutation_recordings
        }

        differences = {}

        for recording in self.mutation_recordings:
            other_recording = recording_by_mutation_type.get(recording.mutation_type)

            if not recording.is_different(other_recording):
                continue

            differences[recording.mutation_type] = {
                "main": recording.response_sw,
                "compare": other_recording.response_sw,
            }

        return differences if differences else None
