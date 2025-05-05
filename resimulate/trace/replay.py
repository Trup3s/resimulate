import logging

from osmocom.utils import b2h, h2b
from pySim.apdu import Apdu
from pySim.ts_102_221 import CardProfileUICC
from pySim.utils import ResTuple
from rich.align import Align
from rich.console import Group
from rich.live import Live
from rich.progress import BarColumn, Progress, TextColumn, TimeElapsedColumn
from rich.text import Text

from resimulate.euicc.transport.pcsc_link import PcscLink
from resimulate.trace.models.recording import Recording
from resimulate.trace.legacy_card import Card
from resimulate.util.enums import ISDR_AID


class Replayer:
    def __init__(self, device: int, target_isd_r: str, mutate: bool = False):
        self.device = device
        self.target_isd_r_aid = ISDR_AID.get_aid(target_isd_r)
        self.mutate = mutate

    def __send_apdu(self, link: PcscLink, apdu: Apdu) -> ResTuple:
        if (self.recording.src_isd_r_aid and self.target_isd_r_aid) and (
            self.recording.src_isd_r_aid != self.target_isd_r_aid
        ):
            cmd_data = b2h(apdu.cmd_data)
            if self.recording.src_isd_r_aid.value in cmd_data:
                cmd_data = cmd_data.replace(
                    self.recording.src_isd_r_aid.value, self.target_isd_r_aid.value
                )
                apdu.cmd_data = h2b(cmd_data)

        data, resp = link.send_apdu_checksw(b2h(apdu.cmd), sw="????")
        logging.debug("Received Data: %s, SW: %s", data, resp)
        return data, resp

    def replay(self, input_path: str):
        progress = Progress(
            TimeElapsedColumn(), BarColumn(), TextColumn("{task.description}")
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
            self.recording = Recording.load_file(input_path)
            progress.update(
                progress_id, description="[bold green]Initializing PC/SC link..."
            )

            try:
                pcsc_link = PcscLink(device_index=self.device)
                logging.debug("PC/SC link initialized: %s", pcsc_link)
                card = Card(pcsc_link)
                initialized_card = card.init_card(target_isd_r=self.target_isd_r_aid)
                logging.debug("Initialized card of type: %s", initialized_card.name)
                logging.debug("Card eUICC Info: %s", card.euicc_info_2)
            except Exception as e:
                logging.error("Failed to initialize card: %s", e)
                logging.exception(e)
                progress.update(
                    progress_id, description=":x: [bold red]Failed to initialize card."
                )
                return

            successful_replays = 0
            try:
                with pcsc_link as link:
                    logging.debug("Replaying APDUs...")
                    for idx, recorded_apdu in enumerate(self.recording.apdus, start=1):
                        logging.info("Replaying %s", recorded_apdu.__rich__())
                        data, resp = self.__send_apdu(link, recorded_apdu.apdu)

                        if resp == b2h(recorded_apdu.apdu.sw):
                            progress.update(
                                progress_id,
                                total=len(self.recording.apdus),
                                completed=idx,
                                description=f"Replaying APDU {idx} / {len(self.recording.apdus)}",
                            )
                            successful_replays += 1
                            continue

                        logging.debug(
                            "Unexpected SW: %s (expected: %s)",
                            resp,
                            b2h(recorded_apdu.apdu.sw),
                        )

                        error, description = CardProfileUICC().interpret_sw(resp)
                        if error:
                            logging.error("%s: %s", error, description)
                        else:
                            logging.error(
                                "Unexpected response: %s != %s",
                                resp,
                                b2h(recorded_apdu.apdu.sw),
                            )

            except KeyboardInterrupt:
                logging.debug("Replay interrupted.")
                progress.update(
                    progress_id, description=":x: [bold red]Replay interrupted."
                )
            except Exception as e:
                logging.exception(e)
                progress.update(
                    progress_id, description=":x: [bold red]Error during replay."
                )
            else:
                logging.debug("Replay finished.")

                if not progress.finished:
                    progress.update(
                        progress_id,
                        description=f":police_car_light: [bold yellow]Failed to replay all APDUs ({successful_replays}/{len(self.recording.apdus)}).",
                    )

                else:
                    progress.update(
                        progress_id,
                        description=":white_check_mark: [bold green]Replay finished.",
                    )
