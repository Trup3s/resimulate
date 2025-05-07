import argparse
import io
import logging
import unittest

from rich.console import Group
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich_argparse import RichHelpFormatter

from resimulate.fuzzing import scenarios
from resimulate.util.logger import init_logger


def add_subparser(
    parent_parser: argparse._SubParsersAction,
) -> None:
    parent_parser.add_parser(
        "fuzz",
        formatter_class=RichHelpFormatter,
        help="Fuzz an esim card by generating arbitrary data.",
        description="Fuzz an esim card by generating APDUs with valid data by constructing the necessary data structures and filling them with arbitrary data.",
    )


def run(args: argparse.Namespace) -> None:
    loader = unittest.TestLoader()
    modules = scenarios.__all__

    # Progress UI
    current_test_suit_progress = Progress(
        TimeElapsedColumn(),
        TextColumn("{task.description}"),
    )
    test_case_progress = Progress(
        TextColumn("  "),
        TimeElapsedColumn(),
        TextColumn("[bold purple]{task.fields[action]}"),
        SpinnerColumn("simpleDots"),
    )
    test_suit_tests_progress = Progress(
        TextColumn(
            "[bold blue]Progress for {task.fields[name]}: {task.percentage:.0f}%"
        ),
        BarColumn(),
        TextColumn("({task.completed} of {task.total} test cases done)"),
    )
    overall_progress = Progress(
        TimeElapsedColumn(), BarColumn(), TextColumn("{task.description}")
    )

    progress_group = Group(
        Panel(
            Group(
                current_test_suit_progress, test_case_progress, test_suit_tests_progress
            )
        ),
        overall_progress,
    )

    overall_task_id = overall_progress.add_task("", total=len(modules))

    def run_test_cases(
        name: str, test_suit: unittest.TestSuite, test_suit_task_id: int
    ) -> None:
        successful_tests = 0
        for test_case in test_suit._tests:
            test_case_task_id = test_case_progress.add_task(
                "", action=test_case._testMethodName, name=name
            )

            dummy_stream = io.StringIO()
            single_suite = unittest.TestSuite([test_case])
            runner = unittest.TextTestRunner(verbosity=0, stream=dummy_stream)
            result = runner.run(single_suite)
            test_case_progress.stop_task(test_case_task_id)

            # Record results
            if result.wasSuccessful():
                test_case_progress.update(test_case_task_id, visible=False)
                successful_tests += 1
            else:
                for _, error in result.errors + result.failures:
                    logging.error(
                        "Fuzzing case %s failed: %s",
                        test_case._testMethodName,
                        error,
                    )

                test_case_progress.update(test_case_task_id, visible=False)

            test_suit_tests_progress.update(test_suit_task_id, advance=1)

        return successful_tests

    with Live(progress_group) as live:
        init_logger(args.verbose, live.console)

        for idx, module in enumerate(modules):
            test_suit = loader.loadTestsFromTestCase(module)
            top_descr = "[bold #AAAAAA](%d out of %d fuzzing groups run)" % (
                idx,
                len(test_suit._tests),
            )
            overall_progress.update(overall_task_id, description=top_descr)

            test_suit_name = module.__name__
            current_task_id = current_test_suit_progress.add_task(
                "Running fuzzing group %s" % test_suit_name
            )
            test_suit_task_id = test_suit_tests_progress.add_task(
                "", total=len(test_suit._tests), name=test_suit_name
            )
            successful_tests = run_test_cases(
                test_suit_name, test_suit, test_suit_task_id
            )

            test_suit_tests_progress.update(test_suit_task_id, visible=False)
            current_test_suit_progress.stop_task(current_task_id)
            if successful_tests == len(test_suit._tests):
                description = "[bold green]Fuzzing Group %s finished! (%d/%d)" % (
                    test_suit_name,
                    successful_tests,
                    len(test_suit._tests),
                )
            else:
                description = "[bold red]Fuzzing Group %s finished! (%d/%d)" % (
                    test_suit_name,
                    successful_tests,
                    len(test_suit._tests),
                )

            current_test_suit_progress.update(
                current_task_id,
                description=description,
            )

            overall_progress.update(overall_task_id, advance=1)

        overall_progress.update(
            overall_task_id,
            description="[bold green]%s fuzzing groups ran, done!" % len(modules),
        )
