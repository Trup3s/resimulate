import random
from copy import deepcopy

from resimulate.euicc.mutation.engine import MutationEngine
from resimulate.euicc.mutation.types import MutationType
from resimulate.euicc.transport.apdu import APDUPacket


class RandomMutationEngine(MutationEngine):
    def __init__(
        self,
        mutation_rate: float = 0.01,
        seed: int | float | str | bytes | bytearray | None = None,
    ):
        self.mutation_rate = mutation_rate
        self.random = random.Random(seed)

    def bitflip(self, data: bytearray):
        length = len(data)
        num_flips = max(1, int(length * self.mutation_rate))

        for _ in range(num_flips):
            index = self.random.randint(0, length - 1)
            bit = 1 << self.random.randint(0, 7)
            data[index] ^= bit

        return bytes(data)

    def random_byte(self, data: bytearray):
        length = len(data)
        num_mutations = max(1, int(length * self.mutation_rate))

        for _ in range(num_mutations):
            index = self.random.randint(0, length - 1)
            data[index] = self.random.randint(0, 255)

        return bytes(data)

    def zero_block(self, data: bytearray):
        length = len(data)
        max_start = max(1, length - 10)
        start = self.random.randint(0, max_start)
        end = min(length, start + 10)

        for i in range(start, end):
            data[i] = 0x00

        return bytes(data)

    def shuffle_blocks(self, data: bytearray):
        block_size = 16
        num_blocks = len(data) // block_size
        blocks = [
            data[i * block_size : (i + 1) * block_size] for i in range(num_blocks)
        ]

        self.random.shuffle(blocks)
        data = b"".join(blocks) + data[num_blocks * block_size :]
        return bytes(data)

    def truncate(self, data: bytearray):
        truncate_point = self.random.randint(1, len(data))
        data = data[:truncate_point]
        return bytes(data)

    def mutate(
        self,
        apdu: APDUPacket,
        mutation_type: MutationType,
    ) -> APDUPacket:
        data = bytearray(apdu.data)
        mutated_apdu = deepcopy(apdu)

        match mutation_type:
            case MutationType.BITFLIP:
                mutated_apdu.data = self.bitflip(data)

            case MutationType.RANDOM_BYTE:
                mutated_apdu.data = self.random_byte(data)

            case MutationType.ZERO_BLOCK:
                mutated_apdu.data = self.zero_block(data)

            case MutationType.SHUFFLE_BLOCKS:
                mutated_apdu.data = self.shuffle_blocks(data)

            case MutationType.TRUNCATE:
                mutated_apdu.data = self.truncate(data)

        return mutated_apdu
