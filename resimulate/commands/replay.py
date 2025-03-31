from osmocom.utils import b2h, h2b, h2i, i2h
from pySim.apdu import Apdu
from pySim.transport.pcsc import PcscSimLink
from pySim.ts_102_221 import CardProfileUICC
from pySim.utils import ResTuple
from rich.align import Align
from rich.console import Group
from rich.live import Live
from rich.progress import BarColumn, Progress, TextColumn, TimeElapsedColumn
from rich.text import Text

from resimulate.legacy_card import Card
from resimulate.models.recording import Recording
from resimulate.legacy_pcsc_link import PcscLink
from resimulate.util.enums import ISDR_AID
from resimulate.util.logger import log


class Replayer:
    def __init__(self, device: int, target_isd_r: str, mutate: bool = False):
        self.device = device
        self.target_isd_r_aid = ISDR_AID.get_aid(target_isd_r)
        self.mutate = mutate

    def __get_remaining_bytes(
        self, link: PcscLink, bytes_to_receive: int, cla: int
    ) -> ResTuple:
        log.debug("Retrieving remaining bytes: %d", bytes_to_receive)
        apdu = Apdu(i2h([cla]) + "C00000" + i2h([bytes_to_receive]))
        return self.__send_apdu(link, apdu)

    def __resend_with_modified_le(
        self, link: PcscLink, apdu: Apdu, le: int
    ) -> ResTuple:
        log.debug("Resending APDU with modified Le: %d", le)
        modified_apdu = Apdu(b2h(apdu.cmd)[:-2] + i2h([le]))
        return self.__send_apdu(link, modified_apdu)

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

        data, resp = link.send_tpdu(b2h(apdu.cmd))
        log.debug("Received Data: %s, SW: %s", data, resp)
        return data, resp

    def __handle_resend(self, link: PcscLink, apdu: Apdu, resp: str) -> bool:
        while resp[:2] in {"61", "6c"}:
            if resp.startswith("61"):
                remaining_bytes = h2i(resp[2:])[0]
                log.debug(
                    "Normal processing, %s bytes still available", remaining_bytes
                )
                _, resp = self.__get_remaining_bytes(link, remaining_bytes, apdu.cla)
            elif resp.startswith("6c"):
                le = h2i(resp[2:])[0]
                log.debug("Wrong length, resending with modified Le %s", le)
                _, resp = self.__resend_with_modified_le(link, apdu, le)

        return resp == "9000"

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
                card = Card(pcsc_link)
                initialized_card = card.init_card(target_isd_r=self.target_isd_r_aid)
                log.debug("Initialized card of type: %s", initialized_card.name)
                log.debug("Card eUICC Info: %s", card.euicc_info_2)
            except Exception as e:
                log.error("Failed to initialize card: %s", e)
                log.exception(e)
                progress.update(
                    progress_id, description=":x: [bold red]Failed to initialize card."
                )
                return

            successful_replays = 0
            try:
                with pcsc_link as link:
                    log.debug("Replaying APDUs...")
                    for idx, recorded_apdu in enumerate(self.recording.apdus, start=1):
                        log.info("Replaying %s", recorded_apdu.__rich__())
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

                        log.debug(
                            "Unexpected SW: %s (expected: %s)",
                            resp,
                            b2h(recorded_apdu.apdu.sw),
                        )

                        if self.__handle_resend(link, recorded_apdu.apdu, resp):
                            progress.update(
                                progress_id,
                                total=len(self.recording.apdus),
                                completed=idx,
                                description=f"Replaying APDU {idx} / {len(self.recording.apdus)}",
                            )
                            successful_replays += 1
                            continue

                        error, description = CardProfileUICC().interpret_sw(resp)
                        if error:
                            log.error("%s: %s", error, description)
                        else:
                            log.error(
                                "Unexpected response: %s != %s",
                                resp,
                                b2h(recorded_apdu.apdu.sw),
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
