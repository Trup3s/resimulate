import pickle
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
from util.logger import log
from util.tracer import Tracer


class Recorder:
    def __init__(self, source: ApduSource):
        self.tracer = Tracer(source)

        self.captured_apdus = []

        self.package_queue: Queue[tuple[Apdu, ApduCommand]] = Queue()
        self.tracer_thread = Thread(
            target=self.tracer.main, args=(self.package_queue,), daemon=True
        )
        signal.signal(signal.SIGINT, self.__signal_handler)

    def __signal_handler(self, sig, frame):
        self.package_queue.shutdown(immediate=True)

    def record(self, output_path: str, timeout: int):
        capture_progress = Progress(
            TimeElapsedColumn(),
            TextColumn("{task.completed}"),
            TextColumn("[bold blue]{task.fields[packet_type]}"),
            TextColumn("[bold green]{task.fields[packet_description]}"),
            TextColumn("{task.fields[packet_code]}"),
        )

        overall_progress = Progress(
            TimeElapsedColumn(),
            BarColumn(),
            TextColumn("{task.description}"),
        )

        main_group = Group(
            # Panel(capture_progress, title="APDU Packets captured", expand=False),
            overall_progress,
            Align.left(
                Text.assemble("Press ", ("Ctrl+C", "bold red"), " to stop capturing."),
                vertical="bottom",
            ),
        )

        overall_task_id = overall_progress.add_task(
            f"[bold red]{len(self.captured_apdus)} packets captured!",
            start=True,
            total=None,
        )

        with Live(main_group) as live:
            self.tracer_thread.start()

            while self.tracer_thread.is_alive():

                try:
                    apdu, apdu_command = self.package_queue.get(timeout=timeout)

                    if apdu is None:
                        log.debug("No more APDU packets to capture.")
                        break

                    log.info("Captured %s %s", apdu_command._name, apdu)

                    """ capture_task_id = capture_progress.add_task(
                        "",
                        completed=len(self.captured_apdus),
                        packet_type=str(apdu_command._name) or "",
                        packet_description=str(apdu_command.path_str),
                        packet_code=str(apdu_command.col_sw),
                    ) """

                    self.captured_apdus.append(apdu)

                    """ capture_progress.stop_task(capture_task_id) """
                except TimeoutError:
                    log.debug("Timeout reached, stopping capture.")
                    break
                except Empty:
                    log.debug("No more APDU packets to capture.")
                    break
                except ShutDown:
                    log.debug("Shutting down capture.")
                    break
                except UnboundLocalError as e:
                    log.debug("Error capturing APDU packets: %s", e)
                    break

                overall_progress.update(
                    overall_task_id,
                    description=f"[bold green]{len(self.captured_apdus)} packet(s) captured!",
                )

            overall_progress.update(
                overall_task_id,
                description="[bold yellow]Saving captured APDU commands...",
            )

            log.debug("Saving captured APDU commands to %s", output_path)

            with open(output_path, "wb") as f:
                pickle.dump(self.captured_apdus, f)

            overall_progress.update(
                overall_task_id,
                description="[bold green]Captured %s APDU packets!"
                % len(self.captured_apdus),
            )
