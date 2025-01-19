import pickle
from contextlib import redirect_stdout

from osmocom.utils import b2h
from pySim.apdu import Apdu
from pySim.app import init_card
from pySim.card_handler import CardHandler
from pySim.transport.pcsc import PcscSimLink
from rich.align import Align
from rich.console import Group
from rich.live import Live
from rich.progress import BarColumn, Progress, TextColumn, TimeElapsedColumn
from rich.text import Text

from resimulate.util.logger import LoggerWriter, log
from resimulate.util.pcsc_link import PcscLink


class Replayer:
    def __init__(self, device: int, isd_r_aid: str):
        self.device = device
        self.isd_r_aid = isd_r_aid

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
            f"[bold green]Loading APDUs from {input_path}...", start=True, total=None
        )

        with Live(main_group):
            with open(input_path, "rb") as f:
                apdus: list[Apdu] = pickle.load(f)

            progress.update(
                progress_id, description="[bold green]Initializing PC/SC link..."
            )

            try:
                pcsc_link = PcscSimLink()  # PcscLink(device_index=self.device)
                runtime_state, self.card = init_card(pcsc_link)
            except Exception as e:
                log.error("Failed to initialize card: %s", e)
                progress.update(
                    progress_id, description=":x: [bold red]Failed to initialize card."
                )
                return
            try:
                with pcsc_link as link:
                    for id, apdu in enumerate(apdus):
                        progress.update(
                            progress_id,
                            total=len(apdus),
                            completed=id + 1,
                            description=f"Replaying APDU {id + 1} / {len(apdus)}",
                        )
                        cmd, resp = link.send_tpdu(b2h(apdu.cmd))
                        log.debug("APDU: %s, SW: %s", b2h(apdu.cmd), resp)

                        if resp != b2h(apdu.sw):
                            log.info(
                                "Received APDU %s response does not match the expected APDU: %s != %s",
                                b2h(apdu.cmd),
                                resp,
                                b2h(apdu.sw),
                            )
            except KeyboardInterrupt:
                log.debug("Replay interrupted.")
                progress.update(
                    progress_id, description=":x: [bold red]Replay interrupted."
                )
                return
            except Exception as e:
                log.error("Error during replay: %s", e)
                progress.update(
                    progress_id, description=":x: [bold red]Error during replay."
                )
                return

            log.debug("Replay finished.")
            progress.update(
                progress_id,
                description=":white_check_mark: [bold green]Replay finished.",
            )
