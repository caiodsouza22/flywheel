"""Minimal CLI for inspecting allot configuration and dry-run allocations."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from allot import AllocationEngine, AllocationRequest, __version__
from allot.config import dump_config_dict, load_config_file
from allot.serialization import decision_to_dict, dumps


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

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
