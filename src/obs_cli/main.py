"""OBS CLI - Main entry point for BACnet network discovery."""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
import time
from importlib.metadata import version
from pathlib import Path
from typing import TYPE_CHECKING

import obs

if TYPE_CHECKING:
    from argparse import Namespace

log = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for CLI output."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[logging.StreamHandler(sys.stderr)],
    )


def format_duration(seconds: float) -> str:
    """Format duration in human-readable form."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes}m {secs:.1f}s"


def detect_output_format(output: str) -> str:
    """Detect output format from file extension."""
    path = Path(output)
    if path.suffix.lower() == ".json":
        return "json"
    return "yaml"


def write_output(data: object, output: str, fmt: str) -> None:
    """Write data to file in specified format."""
    if fmt == "json":
        obs.dump_json(data, output)
    else:
        obs.dump_yaml(data, output)


async def cmd_scan(args: Namespace) -> int:
    """Execute network scan command."""
    setup_logging(args.verbose)
    start_time = time.time()

    log.info("Scanning network: %s", args.network or "auto-detect")
    log.info("")

    try:
        result = await obs.scan_network(
            network=args.network,
        )
    except asyncio.CancelledError:
        log.info("\nCancelled.")
        return 130
    except Exception as e:
        log.error("Error: %s", e)
        return 1

    elapsed = time.time() - start_time
    device_count = len(result.data) if result.data else 0

    log.info("Discovered %d device(s) in %s", device_count, format_duration(elapsed))

    if not result.success:
        for error in result.errors:
            log.warning("Warning: %s", error)

    graph = obs.network_scan_result_to_graph(result)
    fmt = args.format or detect_output_format(args.output)
    write_output(graph, args.output, fmt)

    log.info("Output written to: %s", args.output)
    return 0


async def cmd_discover(args: Namespace) -> int:
    """Execute full discovery command."""
    setup_logging(args.verbose)
    start_time = time.time()

    log.info("Starting full discovery on: %s", args.network or "auto-detect")
    log.info("Max concurrent: %s", args.max_concurrent)
    log.info("")
    log.info("Phase 1: Network scan...")

    try:
        result = await obs.full_scan(
            network=args.network,
            max_concurrent=args.max_concurrent,
        )
    except asyncio.CancelledError:
        log.info("\nCancelled.")
        return 130
    except Exception as e:
        log.error("Error: %s", e)
        return 1

    elapsed = time.time() - start_time

    device_count = 0
    point_count = 0
    if result.data and result.data.devices:
        device_count = len(result.data.devices)
        for device in result.data.devices:
            if device.points:
                point_count += len(device.points)

    log.info("")
    log.info("Discovery complete in %s", format_duration(elapsed))
    log.info("  Devices: %d", device_count)
    log.info("  Points: %d", point_count)

    if not result.success:
        for error in result.errors:
            log.warning("Warning: %s", error)

    graph = obs.full_scan_result_to_graph(result)
    fmt = args.format or detect_output_format(args.output)
    write_output(graph, args.output, fmt)

    log.info("Output written to: %s", args.output)
    return 0


async def cmd_classify(args: Namespace) -> int:
    """Execute classification command."""
    setup_logging(args.verbose)
    start_time = time.time()

    log.info("Loading graph from: %s", args.input)

    input_path = Path(args.input)
    if not input_path.exists():
        log.error("Error: Input file not found: %s", args.input)
        return 1

    try:
        import json

        import yaml

        with open(input_path, encoding="utf-8") as f:
            if input_path.suffix.lower() == ".json":
                data = json.load(f)
            else:
                data = yaml.safe_load(f)

        graph = obs.Graph(**data)
    except Exception as e:
        log.error("Error loading input: %s", e)
        return 1

    log.info("Classifying against: %s", args.topology_url)

    try:
        topology = obs.TopologyInput(url=args.topology_url)
        result = await obs.classify_graph(graph, topology)
    except asyncio.CancelledError:
        log.info("\nCancelled.")
        return 130
    except Exception as e:
        log.error("Error: %s", e)
        return 1

    elapsed = time.time() - start_time

    log.info("Classification complete in %s", format_duration(elapsed))

    if not result.success:
        for error in result.errors:
            log.warning("Warning: %s", error)

    fmt = args.format or detect_output_format(args.output)
    write_output(result.graph, args.output, fmt)

    log.info("Output written to: %s", args.output)
    return 0


def add_common_args(parser: argparse.ArgumentParser) -> None:
    """Add common arguments to a parser."""
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="obs",
        description="OBS CLI - BACnet network discovery tool",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {version('obs-cli')}",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Scan command
    scan_parser = subparsers.add_parser(
        "scan",
        help="Scan network for BACnet devices (quick census)",
    )
    scan_parser.add_argument(
        "--network",
        "-n",
        help="Network CIDR to scan (auto-detected if not specified)",
    )
    scan_parser.add_argument(
        "--output",
        "-o",
        required=True,
        help="Output file path (YAML or JSON based on extension)",
    )
    scan_parser.add_argument(
        "--format",
        "-f",
        choices=["yaml", "json"],
        help="Output format (default: auto-detect from extension)",
    )
    add_common_args(scan_parser)
    scan_parser.set_defaults(func=cmd_scan)

    # Discover command
    discover_parser = subparsers.add_parser(
        "discover",
        help="Full discovery: scan network and read all device objects",
    )
    discover_parser.add_argument(
        "--network",
        "-n",
        help="Network CIDR to scan (auto-detected if not specified)",
    )
    discover_parser.add_argument(
        "--max-concurrent",
        "-c",
        type=int,
        default=10,
        help="Max concurrent device reads (default: 10)",
    )
    discover_parser.add_argument(
        "--output",
        "-o",
        required=True,
        help="Output file path (YAML or JSON based on extension)",
    )
    discover_parser.add_argument(
        "--format",
        "-f",
        choices=["yaml", "json"],
        help="Output format (default: auto-detect from extension)",
    )
    add_common_args(discover_parser)
    discover_parser.set_defaults(func=cmd_discover)

    # Classify command
    classify_parser = subparsers.add_parser(
        "classify",
        help="Classify discovered graph against Brick ontology",
    )
    classify_parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="Input graph file (YAML or JSON)",
    )
    classify_parser.add_argument(
        "--topology-url",
        default="https://brickschema.org/schema/Brick.ttl",
        help="Brick ontology URL (default: brickschema.org)",
    )
    classify_parser.add_argument(
        "--output",
        "-o",
        required=True,
        help="Output file path (YAML or JSON based on extension)",
    )
    classify_parser.add_argument(
        "--format",
        "-f",
        choices=["yaml", "json"],
        help="Output format (default: auto-detect from extension)",
    )
    add_common_args(classify_parser)
    classify_parser.set_defaults(func=cmd_classify)

    return parser


def main() -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    try:
        return asyncio.run(args.func(args))
    except KeyboardInterrupt:
        log.info("\nInterrupted.")
        return 130


if __name__ == "__main__":
    sys.exit(main())
