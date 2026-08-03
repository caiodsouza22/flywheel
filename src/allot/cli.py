"""CLI for inspecting allot configuration, allocating, simulating, and reporting."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from typing import Sequence

from allot import AllocationEngine, AllocationRequest, FrozenClock, __version__
from allot.config import dump_config_dict, load_config_file
from allot.migration import default_pipeline, detect_version
from allot.report import build_system_report, render_simulation_report, render_text_report
from allot.serialization import decision_to_dict, dumps
from allot.simulation import ConstantRatePattern, LoadSimulator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="allot",
        description="Multi-tenant quota and budget allocation utilities",
    )
    parser.add_argument("--version", action="version", version=f"allot {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    show = sub.add_parser("show-config", help="Load and print a config document")
    show.add_argument("config", help="Path to JSON config file")

    allocate = sub.add_parser("allocate", help="Dry-run an allocation against a config")
    allocate.add_argument("config", help="Path to JSON config file")
    allocate.add_argument("--tenant", required=True)
    allocate.add_argument("--resource", required=True)
    allocate.add_argument("--amount", required=True, type=float)
    allocate.add_argument("--allow-partial", action="store_true")

    simulate = sub.add_parser("simulate", help="Run a constant-rate load simulation")
    simulate.add_argument("config", help="Path to JSON config file")
    simulate.add_argument("--tenant", required=True)
    simulate.add_argument("--resource", required=True)
    simulate.add_argument("--amount", required=True, type=float)
    simulate.add_argument("--count", type=int, default=10)
    simulate.add_argument("--every-seconds", type=float, default=1.0)

    report = sub.add_parser("report", help="Allocate once per tenant and print a report")
    report.add_argument("config", help="Path to JSON config file")
    report.add_argument("--resource", required=True)
    report.add_argument("--amount", type=float, default=1.0)

    migrate = sub.add_parser("migrate-config", help="Migrate a legacy config document to v1")
    migrate.add_argument("config", help="Path to JSON config file")
    migrate.add_argument("--in-place", action="store_true")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.command == "show-config":
        store = load_config_file(args.config)
        print(json.dumps(dump_config_dict(store), indent=2, sort_keys=True))
        return 0

    if args.command == "allocate":
        store = load_config_file(args.config)
        engine = AllocationEngine(store)
        decision = engine.allocate(
            AllocationRequest(
                tenant_id=args.tenant,
                resource=args.resource,
                amount=args.amount,
                allow_partial=args.allow_partial,
            )
        )
        print(dumps(decision_to_dict(decision), indent=2))
        return 0 if decision.granted > 0 else 2

    if args.command == "simulate":
        store = load_config_file(args.config)
        clock = FrozenClock(datetime(2024, 1, 1, tzinfo=timezone.utc))
        engine = AllocationEngine(store, clock=clock)
        simulator = LoadSimulator(
            engine=engine,
            clock=clock,
            start=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        pattern = ConstantRatePattern(
            tenant_id=args.tenant,
            resource=args.resource,
            amount=args.amount,
            every_seconds=args.every_seconds,
            count=args.count,
        )
        result = simulator.run(pattern)
        print(render_simulation_report(result))
        return 0

    if args.command == "report":
        store = load_config_file(args.config)
        engine = AllocationEngine(store)
        decisions = []
        for tenant in store.list_tenants():
            decisions.append(
                engine.allocate(
                    AllocationRequest(
                        tenant_id=tenant.id,
                        resource=args.resource,
                        amount=args.amount,
                    )
                )
            )
        system = build_system_report(store, decisions)
        print(render_text_report(system))
        return 0

    if args.command == "migrate-config":
        raw = json.loads(open(args.config, encoding="utf-8").read())
        version = detect_version(raw)
        migrated = default_pipeline().run(raw)
        text = json.dumps(migrated, indent=2, sort_keys=True)
        if args.in_place:
            with open(args.config, "w", encoding="utf-8") as handle:
                handle.write(text + "\n")
        else:
            print(text)
        print(f"# migrated from version {version} to {migrated.get('version')}", file=sys.stderr)
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
