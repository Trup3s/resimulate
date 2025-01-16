import pickle

from osmocom.utils import b2h
from pySim.apdu import Apdu
from pySim.app import init_card
from pySim.card_handler import CardHandler
from rich.align import Align
from rich.console import Group
from rich.live import Live
from rich.progress import BarColumn, Progress, TextColumn, TimeElapsedColumn
from rich.text import Text
from util.logger import log
from util.pcsc_link import PcscLink


class Replayer:
    def __init__(self, device: int):
        self.pcsc_link = PcscLink(device=device)
        self.card_handler = CardHandler(self.pcsc_link)
        self.runtime_state, self.card = init_card(self.card_handler)

    def replay(self, input_path: str):
        progress = Progress(
            TimeElapsedColumn(),
            BarColumn(),
            TextColumn("{task.description}"),
        )

        main_group = Group(
            progress,
            Align.left(
                Text.assemble(
                    "Press ", ("Ctrl+C", "bold red"), " to stop replaying APDUs."
                ),
                vertical="bottom",
            ),
        )

        progress_id = progress.add_task(
            f"[bold red]Loading APDUs from {input_path}...", start=True, total=None
        )

        with Live(main_group):
            with open(input_path, "rb") as f:
                apdus: list[Apdu] = pickle.load(f)

            with self.pcsc_link as link:
                for id, apdu in enumerate(apdus):
                    progress.update(
                        progress_id, description=f"Replaying APDU {id} / {len(apdus)}"
                    )
                    data, sw = link.send_tpdu(b2h(apdu))
                    log.debug("APDU: %s, SW: %s", b2h(apdu), sw)
