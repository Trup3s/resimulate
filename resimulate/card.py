from pySim.transport import LinkBase
from pySim.commands import SimCardCommands
from pySim.filesystem import CardModel, CardApplication
from pySim.cards import SimCardBase, UiccCardBase
from pySim.runtime import RuntimeState
from pySim.profile import CardProfile
from pySim.ts_102_221 import CardProfileUICC
from pySim.utils import all_subclasses
from pySim.exceptions import SwMatchError
from pySim.euicc import CardApplicationISDR, EuiccInfo2

from resimulate.models.euicc_info_2 import EuiccInfo2Data
from resimulate.util.enums import ISDR_AID
from resimulate.util.logger import log


# Card initialization taken from pySim card_init function and modified for ReSIMulate
class Card:
    card: SimCardBase | None
    profile: CardProfile | None
    generic_card: bool = False

    def __init__(self, sim_link: LinkBase):
        self.sim_link = sim_link
        self.sim_card_commands = SimCardCommands(transport=sim_link)

    def init_card(self, target_isd_r: ISDR_AID, timeout: int = 3) -> SimCardBase:
        self.sim_link.wait_for_card(timeout=timeout)

        self.card = UiccCardBase(self.sim_card_commands)
        if not self.card.probe():
            log.warning("Could not detect card type! Assuming a generic card type...")
            self.card = SimCardBase(self.sim_card_commands)
            self.generic_card = True

        self.profile = CardProfile.pick(self.sim_card_commands)
        if self.profile is None:
            log.warning("Unsupported card type!")
            return self.card

        if self.generic_card and isinstance(self.profile, CardProfileUICC):
            self.card._adm_chv_num = 0x0A

        log.debug("Profile of type %s detected." % self.profile)

        if isinstance(self.profile, CardProfileUICC):
            for app_cls in all_subclasses(CardApplication):
                # skip any intermediary sub-classes such as CardApplicationSD
                if hasattr(app_cls, "_" + app_cls.__name__ + "__intermediate"):
                    continue
                self.profile.add_application(app_cls())
            # We have chosen SimCard() above, but we now know it actually is an UICC
            # so it's safe to assume it supports USIM application (which we're adding above).
            # IF we don't do this, we will have a SimCard but try USIM specific commands like
            # the update_ust method (see https://osmocom.org/issues/6055)
            if self.generic_card:
                self.card = UiccCardBase(self.sim_card_commands)

        self.runtime_state = RuntimeState(self.card, self.profile)

        CardModel.apply_matching_models(self.sim_card_commands, self.runtime_state)

        # inform the transport that we can do context-specific SW interpretation
        self.sim_link.set_sw_interpreter(self.runtime_state)

        # try to obtain the EID, if any
        isd_r = self.runtime_state.mf.applications.get(target_isd_r.value.lower(), None)
        if isd_r:
            self.runtime_state.lchan[0].select_file(isd_r)
            try:
                self.runtime_state.identity["EID"] = CardApplicationISDR.get_eid(
                    self.sim_card_commands
                )

                euicc_info_2 = CardApplicationISDR.store_data_tlv(
                    self.sim_card_commands, EuiccInfo2(), EuiccInfo2
                )
                self.euicc_info_2 = EuiccInfo2Data.from_list(
                    euicc_info_2.to_dict()["euicc_info2"]
                )
            except SwMatchError:
                # has ISD-R but not a SGP.22/SGP.32 eUICC - maybe SGP.02?
                pass
            finally:
                self.runtime_state.reset()
        else:
            log.warning("No ISD-R application found on card.")

        return self.card
