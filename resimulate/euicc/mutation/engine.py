from resimulate.euicc.transport.apdu import APDUPacket
from resimulate.euicc.mutation.types import MutationType


class MutationEngine:
    def __init__(self, mutation_rate: float = 0.01):
        self.mutation_rate = mutation_rate

    def bitflip(self, data: bytearray):
        length = len(data)
        num_flips = max(1, int(length * self.mutation_rate))

        for i in range(num_flips):
            index = (i * 31) % length
            bit = 1 << ((i * 7) % 8)
            data[index] ^= bit

        return bytes(data)

    def random_byte(self, data: bytearray):
        length = len(data)
        num_mutations = max(1, int(length * self.mutation_rate))

        for i in range(num_mutations):
            index = (i * 29) % length
            data[index] = (index * 13) % 256

        return bytes(data)

    def zero_block(self, data: bytearray):
        length = len(data)
        start = (length // 4) % max(1, length - 20)
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

        # Deterministic block reordering based on index rotation
        blocks = sorted(blocks, key=lambda b: sum(b) % 256)
        data = b"".join(blocks)
        return bytes(data)

    def truncate(self, data: bytearray):
        truncate_point = (len(data) * 3) // 4  # Fixed truncation at 75%
        data = data[:truncate_point]
        return bytes(data)

    def mutate(
        self,
        apdu: APDUPacket,
        mutation_type: MutationType,
    ) -> APDUPacket:
        data = bytearray(apdu.data)
        mutated_apdu = apdu

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
