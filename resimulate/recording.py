import importlib.metadata
import pickle
from os.path import exists, isfile

from pySim.apdu import Apdu

from resimulate.util.enums import ISDR_AID
from resimulate.util.logger import log


class Recording:
    apdus: list[Apdu]
    src_isd_r_aid: ISDR_AID
    version = importlib.metadata.version("resimulate")

    def __init__(self, src_isd_r: ISDR_AID):
        self.src_isd_r_aid = src_isd_r
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
        if recording.src_isd_r_aid != ISDR_AID._DEFAULT:
            log.debug(
                "Recording used ISD-R AID: %s (%s)",
                recording.src_isd_r_aid.value,
                recording.src_isd_r_aid.name,
            )

        if recording.version != importlib.metadata.version("resimulate"):
            log.warning(
                "File %s was created with a different version of ReSIMulate. "
                "Please ensure compatibility.",
                file_path,
            )

        return recording

    def save_file(self, file_path: str) -> None:
        if len(self.apdus) == 0:
            log.info("No APDUs captured, not saving to file.")
            return

        log.info("Saving %s captured APDU commands to %s", len(self.apdus), file_path)
        with open(file_path, "wb") as f:
            pickle.dump(self, f)
