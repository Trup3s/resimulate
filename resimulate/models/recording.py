import pickle
from os.path import exists, isfile

from resimulate.models.recorded_apdu import RecordedApdu
from resimulate.util import get_version
from resimulate.util.enums import ISDR_AID
from resimulate.util.logger import log


class Recording:
    apdus: list[RecordedApdu]
    src_isd_r_aid: ISDR_AID
    version = get_version()

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
        if recording.src_isd_r_aid != ISDR_AID.DEFAULT:
            log.debug(
                "Recording used ISD-R AID: %s (%s)",
                recording.src_isd_r_aid.value,
                recording.src_isd_r_aid.name,
            )

        if recording.version != get_version():
            log.warning(
                "File %s was created with a different version of ReSIMulate. Please ensure compatibility.",
                file_path,
            )

        if recording.__has_open_channel():
            log.warning(
                "No MANAGE CHANNEL APDU found in recording. This may lead to issues during replay."
            )

        return recording

    def __has_open_channel(self) -> bool:
        return any("MANAGE CHANNEL" in apdu.name for apdu in self.apdus)

    def save_file(self, file_path: str) -> None:
        if len(self.apdus) == 0:
            log.info("No APDUs captured, not saving to file.")
            return

        if self.__has_open_channel():
            log.warning(
                "No MANAGE CHANNEL APDU found in recording. This may lead to issues during replay."
            )

        log.info("Saving %s captured APDU commands to %s", len(self.apdus), file_path)
        with open(file_path, "wb") as f:
            pickle.dump(self, f)
