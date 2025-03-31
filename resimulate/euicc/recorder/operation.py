from dataclasses import dataclass

from resimulate.euicc.transport.apdu import APDUPacket
from resimulate.euicc.mutation.types import MutationType


@dataclass
class Operation:
    application_name: str
    func_name: str
    original_apdu: APDUPacket
    mutated_apdu: APDUPacket
    mutation_type: MutationType
    response_sw: str
