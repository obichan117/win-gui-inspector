"""CLI entry point for win-gui-inspector.

Usage:
    win-gui-inspector inspect --title "MarketSpeed" --depth 4
    win-gui-inspector inspect --title "MarketSpeed" --export elements.yaml
    win-gui-inspector map --title "MarketSpeed"
    win-gui-inspector map --title "MarketSpeed" --export elements.json
"""

from __future__ import annotations

import argparse
import sys


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog="win-gui-inspector",
        description="Windows GUI element inspector and mapper",
    )

    parser.add_argument("--version", action="store_true", help="Show version and exit")

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Inspect command
    inspect_parser = subparsers.add_parser(
        "inspect",
        help="Interactively inspect UI elements",
    )
    inspect_parser.add_argument(
        "--title", type=str, default=None, help="Window title pattern (regex)"
    )
    inspect_parser.add_argument(
        "--class-name", type=str, default=None, help="Window class name"
    )
    inspect_parser.add_argument(
        "--depth", type=int, default=4, help="Max scan depth (default: 4)"
    )
    inspect_parser.add_argument(
        "--export", action="store_true", help="Scan and export to YAML immediately"
    )
    inspect_parser.add_argument(
        "--screen", type=str, default="main", help="Screen name label for export"
    )
    inspect_parser.add_argument(
        "--output", type=str, default=None, help="Output path for YAML export"
    )
    inspect_parser.add_argument(
        "--backend", type=str, default="uia", help="pywinauto backend (default: uia)"
    )

    # Map command
    map_parser = subparsers.add_parser(
        "map",
        help="Map all windows and elements",
    )
    map_parser.add_argument(
        "--title", type=str, default=None, help="Window title pattern (regex)"
    )
    map_parser.add_argument(
        "--export", type=str, default=None, help="Export element map to JSON file"
    )
    map_parser.add_argument(
        "--depth", type=int, default=5, help="Max scan depth (default: 5)"
    )
    map_parser.add_argument(
        "--backend", type=str, default="uia", help="pywinauto backend (default: uia)"
    )

    return parser.parse_args()


def cmd_inspect(args: argparse.Namespace) -> int:
    """Run the inspect command."""
    from win_gui_inspector.inspector import UIInspector

    inspector = UIInspector(
        window_title=args.title,
        max_depth=args.depth,
        backend=args.backend,
    )

    if not inspector.connect():
        return 1

    if args.export:
        inspector.scan_current_screen(args.screen)
        inspector.export_to_yaml(args.output)
    else:
        inspector.interactive_mode()

    return 0


def cmd_map(args: argparse.Namespace) -> int:
    """Run the map command."""
    from win_gui_inspector.mapper import WindowMapper

    mapper = WindowMapper(
        title_pattern=args.title,
        max_depth=args.depth,
        backend=args.backend,
    )

    mapper.run(export_path=args.export)
    return 0


def main() -> int:
    """Main entry point."""
    args = parse_args()

    if args.version:
        from win_gui_inspector import __version__

        print(f"win-gui-inspector version {__version__}")
        return 0

    if args.command == "inspect":
        return cmd_inspect(args)

    if args.command == "map":
        return cmd_map(args)

    # No command — show help
    parse_args()  # Will show usage if no args
    return 0


if __name__ == "__main__":
    sys.exit(main())
