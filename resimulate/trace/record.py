import logging
import signal
from queue import Empty, Queue, ShutDown
from threading import Thread

from pySim.apdu import Apdu, ApduCommand
from pySim.apdu_source.gsmtap import ApduSource
from rich.align import Align
from rich.console import Group
from rich.live import Live
from rich.progress import BarColumn, Progress, TextColumn, TimeElapsedColumn
from rich.text import Text

from resimulate.trace.models.recorded_apdu import RecordedApdu
from resimulate.trace.models.recording import Recording
from resimulate.trace.tracer import Tracer
from resimulate.util.enums import ISDR_AID


class Recorder:
    def __init__(self, source: ApduSource, src_isd_r: ISDR_AID):
        self.tracer = Tracer(source, isd_r_aid=src_isd_r.aid)
        self.src_isd_r_aid = src_isd_r

        self.package_queue: Queue[tuple[Apdu, ApduCommand]] = Queue()
        self.tracer_thread = Thread(
            target=self.tracer.main, args=(self.package_queue,), daemon=True
        )
        self.recording = Recording(src_isd_r=src_isd_r.aid)
        signal.signal(signal.SIGINT, self.__signal_handler)

    def __signal_handler(self, sig, frame):
        logging.debug("Received signal %s, shutting down capture.", sig)
        self.package_queue.shutdown(immediate=True)

    def record(self, output_path: str, timeout: int):
        overall_progress = Progress(
            TimeElapsedColumn(),
            BarColumn(),
            TextColumn("{task.description}"),
        )

        main_group = Group(
            # Panel(capture_progress, title="APDU Packets captured", expand=False),
            overall_progress,
            Align.left(
                Text.assemble(
                    "Press ",
                    ("Ctrl+C", "bold green"),
                    " to stop capturing and save recorded commands.",
                ),
                vertical="bottom",
            ),
        )

        overall_task_id = overall_progress.add_task(
            f"[bold red]{len(self.recording.apdus)} packets captured!",
            start=True,
            total=None,
        )

        with Live(main_group):
            self.tracer_thread.start()

            while self.tracer_thread.is_alive():
                try:
                    apdu, apdu_command = self.package_queue.get(timeout=timeout)

                    if apdu is None:
                        logging.debug("No more APDU packets to capture.")
                        break

                    logging.info(
                        "Captured %s %s %s",
                        apdu_command._name,
                        apdu_command.path_str,
                        apdu,
                    )
                    self.recording.apdus.append(RecordedApdu(apdu, apdu_command))
                except TimeoutError:
                    logging.debug("Timeout reached, stopping capture.")
                    break
                except Empty:
                    logging.debug("No more APDU packets to capture.")
                    break
                except ShutDown:
                    logging.debug("Shutting down capture.")
                    break
                except UnboundLocalError as e:
                    logging.debug("Error capturing APDU packets: %s", e)
                    break

                overall_progress.update(
                    overall_task_id,
                    description=f"[bold green]{len(self.recording.apdus)} packet(s) captured!",
                )

            overall_progress.update(
                overall_task_id,
                description="[bold yellow]Saving captured APDU commands...",
            )

            self.recording.save_file(output_path)

            overall_progress.update(
                overall_task_id,
                description="[bold green]Captured %s APDU packets!"
                % len(self.recording.apdus),
            )
