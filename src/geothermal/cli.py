"""Standalone CLI — run the whole analysis from a small TOML input file, no key needed.

    geo-datathon template --out inputs.toml      # write a starting-point input file
    geo-datathon report --input inputs.toml      # run the pipeline → technical report
    geo-datathon workflow                         # run the agent → decision log

Driven entirely by the typed config, so judges can reproduce everything offline.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pydantic import ValidationError

from geothermal.agent import narrate_deterministic, run_workflow
from geothermal.assumptions import DEFAULT_ASSUMPTIONS, Assumptions
from geothermal.economics.search import search_designs
from geothermal.inputs import InputSpec, default_template, parse_input_file
from geothermal.report import build_report


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns a process exit code."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except (ValidationError, ValueError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="geo-datathon", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    template = sub.add_parser("template", help="write a starting-point TOML input file")
    template.add_argument("--out", default="inputs.toml")
    template.set_defaults(handler=_cmd_template)

    report = sub.add_parser("report", help="run the pipeline and produce the technical report")
    report.add_argument(
        "--input", default=None, help="TOML input file (defaults applied if omitted)"
    )
    report.add_argument("--out", default=None, help="output Markdown path (stdout if omitted)")
    report.add_argument("--mc-samples", type=int, default=2000)
    report.set_defaults(handler=_cmd_report)

    workflow = sub.add_parser(
        "workflow", help="run the agentic workflow and print the decision log"
    )
    workflow.add_argument("--input", default=None)
    workflow.add_argument("--mc-samples", type=int, default=2000)
    workflow.set_defaults(handler=_cmd_workflow)

    return parser


def _cmd_template(args: argparse.Namespace) -> int:
    Path(args.out).write_text(default_template(), encoding="utf-8")
    print(f"wrote starting-point input file to {args.out}")
    return 0


def _cmd_report(args: argparse.Namespace) -> int:
    assumptions = _resolve_assumptions(args.input)
    markdown = build_report(assumptions=assumptions, mc_samples=args.mc_samples)
    if args.out:
        Path(args.out).write_text(markdown, encoding="utf-8")
        print(f"wrote report to {args.out}")
    else:
        print(markdown)
    return 0


def _cmd_workflow(args: argparse.Namespace) -> int:
    assumptions = _resolve_assumptions(args.input)
    result = run_workflow(assumptions=assumptions, mc_samples=args.mc_samples)
    print(narrate_deterministic(result))
    return 0


def _resolve_assumptions(input_path: str | None) -> Assumptions:
    """Resolve the run config from a file; if it requests a search, optimise and use the winner."""
    if input_path is None:
        return DEFAULT_ASSUMPTIONS
    spec: InputSpec = parse_input_file(input_path)
    if not spec.search.ranges:
        return spec.assumptions
    result = search_designs(
        base=spec.assumptions,
        ranges=spec.search.ranges,
        constraints=spec.search.constraints,
        objective=spec.search.objective,
    )
    if result.best is None:
        raise ValueError("no design satisfies the given constraints")
    return result.best.assumptions


if __name__ == "__main__":
    raise SystemExit(main())
