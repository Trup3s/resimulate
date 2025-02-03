from pySim.transport import ProactiveHandler as Proact
from pySim.transport import ProactiveCommand

from resimulate.util.logger import log


class ProactiveHandler(Proact):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def receive_fetch(self, cmd: ProactiveCommand):
        log.debug("Handling proactive command:", cmd)
