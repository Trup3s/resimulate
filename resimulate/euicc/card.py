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
            for aid in aids:
                try:
                    self.select_adf(aid)
                    self.supported_applications[application] = application(
                        link=self.link, aid=aid
                    )
                    logging.debug("Found %s via ADF %s", application.name, aid)
                    break
                except Exception as exception:
                    logging.debug(
                        "Error selecting ADF %s! Failed with %s", aid, str(exception)
                    )
                    pass

        self.link.reset_card()

    def select_adf(self, adf: str) -> None:
        apdu = APDUPacket(cla=0x00, ins=0xA4, p1=0x04, p2=0x04, data=bytes.fromhex(adf))
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
