import itertools
import logging
from osmocom.utils import i2h, h2b

from pySim.commands import SimCardCommands

from resimulate.euicc.applications import (
    ECASD,
    ESTK_FWUPD,
    ISDP,
    ISDR,
    USIM,
    Application,
)
from resimulate.euicc.transport.apdu import APDUPacket
from resimulate.euicc.transport.pcsc_link import PcscLink


class Card:
    def __init__(self, link: PcscLink):
        self.link = link
        applications: list[Application] = [USIM, ISDR, ECASD, ISDP, ESTK_FWUPD]
        cla_bytes = [0x00, 0x01, 0x80, 0x81]
        self.commands = SimCardCommands(self.link)
        self.executed_commands = []
        self.supported_applications: dict[type[Application], Application] = {}
        self.atr = self.commands.get_atr()

        for application in applications:
            aids = [application.aid] + application.alternative_aids
            for aid, cla_byte in itertools.product(aids, cla_bytes):
                try:
                    self.select_adf(aid, cla_byte)
                    self.supported_applications[application] = application(
                        link=self.link, aid=aid, cla_byte=cla_byte
                    )
                    logging.debug(
                        "Found %s via ADF %s with CLA byte %s",
                        application.name,
                        aid,
                        i2h([cla_byte]),
                    )
                    break
                except Exception as exception:
                    logging.debug(
                        "Error selecting ADF %s! Failed with %s", aid, str(exception)
                    )
                    pass

        self.link.reset_card()

    def select_adf(self, adf: str, cla_byte: int) -> None:
        apdu = APDUPacket(cla=cla_byte, ins=0xA4, p1=0x04, p2=0x04, data=h2b(adf))
        self.link.send_apdu_checksw(apdu.to_hex(), "9000")
        logging.debug("Selected ADF %s", adf)

    @property
    def isd_r(self) -> ISDR:
        isd_r = self.supported_applications.get(ISDR)
        if not isd_r:
            raise Exception("ISDR application not supported")

        logging.debug("Selecting ISD-R application")
        self.select_adf(isd_r.aid, isd_r.cla_byte)
        return isd_r

    @property
    def estk_dfu(self) -> ESTK_FWUPD:
        estk_dfu = self.supported_applications.get(ESTK_FWUPD)
        if not estk_dfu:
            raise Exception("ESTK_DFU application not supported")

        self.select_adf(estk_dfu.aid, estk_dfu.cla_byte)
        return estk_dfu
