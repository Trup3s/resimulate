import logging

from pySim.commands import SimCardCommands

from resimulate.euicc.applications import Application
from resimulate.euicc.applications.ecasd import ECASD
from resimulate.euicc.applications.isd_p import ISDP
from resimulate.euicc.applications.isd_r import ISDR
from resimulate.euicc.applications.usim import USIM
from resimulate.euicc.transport.pcsc_link import PcscLink


class Card:
    supported_applications: dict[type[Application], Application] = {}

    def __init__(self, link: PcscLink):
        self.link = link
        applications: list[Application] = [USIM, ISDR, ECASD, ISDP]
        self.commands = SimCardCommands(self.link)
        self.commands.cla_byte = "00"
        self.executed_commands = []
        self.atr = self.commands.get_atr()

        for application in applications:
            for aid in [application.aid] + application.alternative_aids:
                try:
                    self.commands.select_adf(aid)
                    self.supported_applications[application] = application(
                        self.link, aid
                    )
                    break
                except Exception as exception:
                    logging.debug(
                        "Error selecting ADF %s! Failed with %s", aid, str(exception)
                    )
                    pass

    @property
    def isd_r(self) -> ISDR:
        isd_r = self.supported_applications.get(ISDR)
        if not isd_r:
            raise Exception("ISDR application not supported")

        self.commands.select_adf(ISDR.aid)
        return isd_r
