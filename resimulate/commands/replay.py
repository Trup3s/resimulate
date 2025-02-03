from osmocom.utils import b2h, h2b, h2i, i2h
from pySim.apdu import Apdu
from pySim.transport.pcsc import PcscSimLink
from pySim.ts_102_221 import CardProfileUICC
from rich.align import Align
from rich.console import Group
from rich.live import Live
from rich.progress import BarColumn, Progress, TextColumn, TimeElapsedColumn
from rich.text import Text

from resimulate.card import Card
from resimulate.recording import Recording
from resimulate.util.enums import ISDR_AID
from resimulate.util.logger import log


class Replayer:
    def __init__(self, device: int, target_isd_r: str):
        self.device = device
        self.target_isd_r_aid = ISDR_AID.get_aid(target_isd_r)

    def __get_remaining_bytes(self, link: PcscSimLink, bytes_to_receive: int, cla: int):
        log.debug("Retrieving remaining bytes: %d", bytes_to_receive)
        apdu = Apdu(i2h([cla]) + "C00000" + i2h([bytes_to_receive]))
        return self.__send_apdu(link, apdu)

    def __resend_with_modified_le(self, link: PcscSimLink, apdu: Apdu, le: int):
        log.debug("Resending APDU with modified Le: %d", le)
        modified_apdu = Apdu(b2h(apdu.cmd)[:-2] + i2h([le]))
        return self.__send_apdu(link, modified_apdu)

    def __send_apdu(self, link: PcscSimLink, apdu: Apdu):
        if self.recording.src_isd_r_aid and self.target_isd_r_aid:
            if b2h(apdu.cmd_data) == self.recording.src_isd_r_aid.value:
                apdu.cmd_data = h2b(self.target_isd_r_aid.value)

        log.debug(
            "Sending APDU(%s) where CLA(%s), INS(%s), P1(%s), P2(%s), Lc(%s), DATA(%s), P3/Le(%s)",
            b2h(apdu.cmd),
            i2h([apdu.cla]),
            i2h([apdu.ins]),
            i2h([apdu.p1]),
            i2h([apdu.p2]),
            i2h([apdu.lc]),
            b2h(apdu.cmd_data),
            i2h([apdu.p3]),
        )
        data, resp = link.send_tpdu(b2h(apdu.cmd))
        log.debug("Received Data: %s, SW: %s", data, resp)
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
                pcsc_link = PcscSimLink()  # PcscLink(device_index=self.device)
                log.debug("PC/SC link initialized: %s", pcsc_link)
                card = Card(pcsc_link).init_card(target_ids_r=self.target_isd_r_aid)
                log.debug("Initialized card of type: %s", card.name)
            except Exception as e:
                log.error("Failed to initialize card: %s", e)
                log.exception(e)
                progress.update(
                    progress_id, description=":x: [bold red]Failed to initialize card."
                )
                return

            try:
                with pcsc_link as link:
                    log.debug("Replaying APDUs...")
                    for idx, apdu in enumerate(self.recording.apdus, start=1):
                        progress.update(
                            progress_id,
                            total=len(self.recording.apdus),
                            completed=idx,
                            description=f"Replaying APDU {idx} / {len(self.recording.apdus)}",
                        )

                        data, resp = self.__send_apdu(link, apdu)

                        if resp == b2h(apdu.sw):
                            continue

                        log.debug(
                            "Unexpected SW: %s (expected: %s)", resp, b2h(apdu.sw)
                        )

                        if resp.startswith("61"):
                            remaining_bytes = h2i(resp[2:])[0]
                            log.debug(
                                "Normal processing, %s bytes still available",
                                remaining_bytes,
                            )
                            self.__get_remaining_bytes(link, remaining_bytes, apdu.cla)
                            continue
                        elif resp.startswith("6c"):
                            le = h2i(resp[2:])[0]
                            log.warning(
                                "Wrong length, resending with modified Le %s", le
                            )
                            self.__resend_with_modified_le(link, apdu, le)
                            continue

                        error, description = CardProfileUICC().interpret_sw(resp)
                        if error:
                            log.error("%s: %s", error, description)
                        else:
                            log.error(
                                "Unexpected response: %s != %s", resp, b2h(apdu.sw)
                            )

            except KeyboardInterrupt:
                log.debug("Replay interrupted.")
                progress.update(
                    progress_id, description=":x: [bold red]Replay interrupted."
                )
            except Exception as e:
                log.exception(e)
                progress.update(
                    progress_id, description=":x: [bold red]Error during replay."
                )
            else:
                log.debug("Replay finished.")
                progress.update(
                    progress_id,
                    description=":white_check_mark: [bold green]Replay finished.",
                )
