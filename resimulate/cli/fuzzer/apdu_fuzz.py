import argparse

from rich_argparse import RichHelpFormatter

from resimulate.euicc.mutation.deterministic_engine import DeterministicMutationEngine
from resimulate.euicc.mutation.random_engine import RandomMutationEngine
from resimulate.fuzzing.apdu_fuzzing import SCENARIOS
from resimulate.fuzzing.apdu_fuzzing.models.scenario_runner import ScenarioRunner


def add_subparser(
    parent_parser: argparse._SubParsersAction,
) -> None:
    parser: argparse.ArgumentParser = parent_parser.add_parser(
        "apdu_fuzz",
        formatter_class=RichHelpFormatter,
        help="Fuzz an esim card by mutating the APDUs.",
        description="Coverage guided fuzzing of an esim card. By mutating the APDUs sent to the card, we can explore the card's behavior and find potential vulnerabilities.",
    )
    parser.add_argument(
        "card_name",
        type=str,
        help="Card name (e.g. 'eSIM-1')",
    )
    parser.add_argument(
        "-e",
        "--engine",
        type=str,
        default="deterministic",
        choices=["deterministic", "random"],
        required=False,
        help="Fuzzing engine to use (default: %(default)s)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output path (e.g. 'resimulate/recordings/'). If not provided, the current directory will be used.",
    )
    parser.add_argument(
        "-s",
        "--scenario",
        type=str,
        choices=[scenario.__qualname__ for scenario in SCENARIOS],
        required=False,
        help="Scenario to run (default: all scenarios)",
    )
    parser.add_argument(
        "--max-apdu-size",
        type=int,
        default=255,
        required=False,
        help="Max APDU size (default: %(default)s)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite existing output files (default: %(default)s)",
    )


def run(args: argparse.Namespace) -> None:
    engine_map = {
        "deterministic": DeterministicMutationEngine,
        "random": RandomMutationEngine,
    }
    mutation_engine_cls = engine_map[args.engine]

    if args.scenario:
        scenarios = [
            scenario for scenario in SCENARIOS if scenario.__qualname__ == args.scenario
        ]
    else:
        scenarios = SCENARIOS

    runner = ScenarioRunner(scenarios=scenarios)
    runner.record_card(
        card_name=args.card_name,
        mutation_engine=mutation_engine_cls(),
        path=args.output,
        overwrite=args.overwrite,
        apdu_data_size=args.max_apdu_size,
    )
