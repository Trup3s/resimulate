import itertools
import logging
from typing import Type

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
from resimulate.util.name_generator import generate_name


class Card:
    selected_application: Application | None = None

    def __init__(self, link: PcscLink, name: str | None = None) -> None:
        self.link = link
        applications: list[Application] = [USIM, ISDR, ECASD, ISDP, ESTK_FWUPD]
        self.commands = SimCardCommands(self.link)
        self.executed_commands = []
        self.supported_applications: dict[type[Application], Application] = {}
        self.atr = self.commands.get_atr()
        self.name = name or generate_name(self.atr)

        for application in applications:
            aids = [application.aid] + application.alternative_aids
            for aid, cla_byte in itertools.product(aids, [0x01, 0x00]):
                try:
                    self.select_adf(aid, cla_byte)
                    instance = application(link=self.link, aid=aid)
                    self.supported_applications[application] = instance
                    self.selected_application = instance
                    logging.debug("Found %s via ADF %s", application.name, aid)
                    break
                except Exception as exception:
                    logging.debug(
                        "Error selecting ADF %s! Failed with %s", aid, str(exception)
                    )

    def select_adf(self, adf: str, cla_byte: int = 0x00) -> None:
        apdu = APDUPacket(
            cla=cla_byte, ins=0xA4, p1=0x04, p2=0x0C, data=bytes.fromhex(adf)
        )
        self.link.send_apdu_checksw(apdu.to_hex(), "9000")
        logging.debug("Selected ADF %s", adf)

    def select_application(self, application_cls: Type[Application]) -> Application:
        application = self.supported_applications.get(application_cls)
        if not application:
            raise Exception(f"{application_cls.name} application not supported")

        if self.selected_application != application:
            logging.debug("Selecting application %s", application.name)
            self.select_adf(application.aid)
            self.selected_application = application

        return application

    @property
    def isd_r(self) -> ISDR:
        return self.select_application(ISDR)

    @property
    def estk_dfu(self) -> ESTK_FWUPD:
        return self.select_application(ESTK_FWUPD)
