import pickle
from os.path import exists, isfile

from pySim.apdu import Apdu

from resimulate.util.enums import ISDR_AID
from resimulate.util.logger import log


class Recording:
    apdus: list[Apdu]
    src_isd_r_aid: ISDR_AID

    def __init__(self, src_isd_r: str = "default"):
        self.src_isd_r_aid = ISDR_AID.get_aid(src_isd_r)
        self.apdus = []

    @staticmethod
    def load_file(file_path: str) -> "Recording":
        if not exists(file_path) or not isfile(file_path):
            raise FileNotFoundError(f"File {file_path} not found.")

        with open(file_path, "rb") as f:
            recording = pickle.load(f)

        if not isinstance(recording, Recording):
            raise TypeError(f"File {file_path} does not contain a Recording object.")

        log.debug("Loaded %d APDUs from %s", len(recording.apdus), file_path)

        return recording

    def save_file(self, file_path: str) -> None:
        log.debug("Saving captured APDU commands to %s", file_path)
        with open(file_path, "wb") as f:
            pickle.dump(self, f)
