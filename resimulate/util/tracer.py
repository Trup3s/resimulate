from queue import Queue

from pySim.apdu import ApduDecoder, CardReset
from pySim.apdu.global_platform import ApduCommands as GlobalPlatformCommands
from pySim.apdu.ts_31_102 import ApduCommands as UsimApduCommands
from pySim.apdu.ts_102_221 import ApduCommands as UiccApduCommands
from pySim.apdu.ts_102_221 import UiccSelect, UiccStatus
from pySim.apdu.ts_102_222 import ApduCommands as ManageApduCommands
from pySim.apdu_source import ApduSource
from pySim.ara_m import CardApplicationARAM
from pySim.cards import UiccCardBase
from pySim.commands import SimCardCommands
from pySim.euicc import CardApplicationECASD, CardApplicationISDR
from pySim.global_platform import CardApplicationISD
from pySim.runtime import RuntimeState
from pySim.ts_31_102 import CardApplicationUSIM
from pySim.ts_31_103 import CardApplicationISIM
from pySim.ts_102_221 import CardProfileUICC

from resimulate.util.dummy_sim_link import DummySimLink
from resimulate.util.enums import ISDR_AID
from resimulate.util.logger import log

APDU_COMMANDS = (
    UiccApduCommands + UsimApduCommands + ManageApduCommands + GlobalPlatformCommands
)


# Taken from the pySim project and modified for the ReSIMulate project
class Tracer:
    def __init__(self, source: ApduSource, isd_r_aid: ISDR_AID):
        # we assume a generic UICC profile; as all APDUs return 9000 in DummySimLink above,
        # all CardProfileAddon (including SIM) will probe successful.
        profile = CardProfileUICC()
        profile.add_application(CardApplicationUSIM())
        profile.add_application(CardApplicationISIM())
        profile.add_application(CardApplicationISDR(aid=isd_r_aid.value))
        profile.add_application(CardApplicationECASD())
        profile.add_application(CardApplicationARAM())
        profile.add_application(CardApplicationISD())

        scc = SimCardCommands(transport=DummySimLink())
        card = UiccCardBase(scc)
        self.runtime_state = RuntimeState(card, profile)
        self.apdu_decoder = ApduDecoder(APDU_COMMANDS)

        self.suppress_status = False
        self.suppress_select = False
        self.show_raw_apdu = False
        self.source = source

    def main(self, package_queue: Queue):
        """Main loop of tracer: Iterates over all Apdu received from source."""
        apdu_counter = 0
        while True:
            # obtain the next APDU from the source (blocking read)
            try:
                apdu = self.source.read()
                apdu_counter = apdu_counter + 1
            except StopIteration:
                log.debug("%i APDUs parsed, stop iteration." % apdu_counter)
                package_queue.task_done()
                return
            except Exception as e:
                log.error("Error reading APDU (%s): %s", apdu, e)
                continue

            if apdu is None:
                log.debug("Received None APDU")
                continue

            if isinstance(apdu, CardReset):
                log.debug("Resetting runtime state")
                self.runtime_state.reset()
                continue

            # ask ApduDecoder to look-up (INS,CLA) + instantiate an ApduCommand derived
            apdu_command = self.apdu_decoder.input(apdu)
            # process the APDU (may modify the RuntimeState)
            try:
                apdu_command.process(self.runtime_state)
            except ValueError as e:
                log.error("Error reading APDU (%s): %s", apdu, e)
                continue
            except AttributeError as e:
                log.error("Error processing APDU (%s): %s", apdu, e)
                return

            # Avoid cluttering the log with too much verbosity
            if self.suppress_select and isinstance(apdu_command, UiccSelect):
                log.debug("Suppressing UiccSelect")
                continue
            if self.suppress_status and isinstance(apdu_command, UiccStatus):
                log.debug("Suppressing UiccStatus")
                continue

            package_queue.put((apdu, apdu_command))
