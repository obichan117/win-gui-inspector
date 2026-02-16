"""Map all windows and their UI elements for a target application.

Generalized from ms2auto/cli/mapper.py — no broker-specific dependencies.
Uses pywinauto Desktop(backend="uia") to discover windows by title pattern.
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
from datetime import datetime
from pathlib import Path

from pywinauto import Application, Desktop


def _ensure_utf8_output() -> None:
    """Force UTF-8 output for non-ASCII text on Windows."""
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "buffer"):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


class WindowMapper:
    """Maps all windows and UI elements for a target application."""

    def __init__(
        self,
        title_pattern: str | None = None,
        class_name: str | None = None,
        max_depth: int = 5,
        backend: str = "uia",
    ) -> None:
        self.title_pattern = title_pattern
        self.class_name = class_name
        self.max_depth = max_depth
        self.backend = backend

    def find_windows(self) -> list[dict]:
        """Find all matching windows.

        Returns:
            List of dicts with 'title', 'handle', 'width', 'height' keys.
        """
        desktop = Desktop(backend=self.backend)
        windows_info: list[dict] = []

        try:
            if self.title_pattern:
                all_windows = desktop.windows(title_re=self.title_pattern)
            else:
                all_windows = desktop.windows()
        except Exception:
            all_windows = desktop.windows()

        for win in all_windows:
            try:
                title = win.window_text()
                if not title:
                    continue

                rect = win.rectangle()
                width = rect.width()
                height = rect.height()

                # Skip tiny windows (likely hidden or system artifacts)
                if width > 100 and height > 100:
                    windows_info.append(
                        {
                            "title": title,
                            "handle": win.handle,
                            "width": width,
                            "height": height,
                        }
                    )
            except Exception:
                continue

        return windows_info

    def map_window_elements(self, window: object) -> list[dict]:
        """Map all UI elements in a window recursively.

        Args:
            window: A pywinauto WindowSpecification object.

        Returns:
            List of element info dicts.
        """
        elements: list[dict] = []

        useful_types = {
            "Button", "Edit", "CheckBox", "ComboBox", "List", "ListItem",
            "DataGrid", "DataItem", "Tab", "TabItem", "RadioButton",
            "Text", "Table", "TreeItem", "MenuItem",
        }

        def scan_element(elem: object, depth: int = 0) -> None:
            if depth > self.max_depth:
                return

            try:
                info = elem.element_info  # type: ignore[attr-defined]
                name = info.name or ""
                ctrl_type = info.control_type or ""
                auto_id = info.automation_id or ""
                class_name = info.class_name or ""

                value = ""
                if ctrl_type == "Edit":
                    with contextlib.suppress(Exception):
                        value = elem.legacy_properties().get("Value", "")  # type: ignore[attr-defined]

                checked = None
                if ctrl_type == "CheckBox":
                    with contextlib.suppress(Exception):
                        checked = elem.get_toggle_state()  # type: ignore[attr-defined]

                element_info: dict = {
                    "depth": depth,
                    "type": ctrl_type,
                    "id": auto_id,
                    "name": name,
                    "class": class_name,
                }

                if value:
                    element_info["value"] = value
                if checked is not None:
                    element_info["checked"] = checked

                if ctrl_type in useful_types and (auto_id or name):
                    elements.append(element_info)

                for child in elem.children():  # type: ignore[attr-defined]
                    scan_element(child, depth + 1)

            except Exception:
                pass

        scan_element(window)
        return elements

    def run(self, export_path: str | Path | None = None) -> dict[str, dict]:
        """Run the full mapping process.

        Args:
            export_path: Optional JSON file path for export.

        Returns:
            Dict of window_title -> mapping data.
        """
        _ensure_utf8_output()

        print("\n" + "=" * 70)
        print("FINDING WINDOWS")
        print("=" * 70)

        windows = self.find_windows()

        print(f"\nFound {len(windows)} windows:")
        for i, win in enumerate(windows):
            print(f"  {i + 1}. [{win['title']}] {win['width']}x{win['height']}")

        if not windows:
            print("\n[WARNING] No matching windows found.")
            return {}

        all_mappings: dict[str, dict] = {}

        for win in windows:
            title = win["title"]
            print("\n" + "=" * 70)
            print(f"MAPPING: {title}")
            print("=" * 70)

            try:
                app = Application(backend=self.backend).connect(handle=win["handle"])
                window = app.window(handle=win["handle"])

                elements = self.map_window_elements(window)

                # Group by control type
                by_type: dict[str, list[dict]] = {}
                for elem in elements:
                    t = elem["type"]
                    if t not in by_type:
                        by_type[t] = []
                    by_type[t].append(elem)

                print(f"\nFound {len(elements)} elements:")

                for ctrl_type in sorted(by_type.keys()):
                    items = by_type[ctrl_type]
                    print(f"\n  === {ctrl_type} ({len(items)}) ===")

                    seen: set[tuple[str, str]] = set()
                    for elem in items:
                        key = (elem.get("id", ""), elem.get("name", ""))
                        if key in seen:
                            continue
                        seen.add(key)

                        id_str = elem.get("id") or "-"
                        name_str = elem.get("name") or "(no name)"
                        value_str = f" value=[{elem['value']}]" if elem.get("value") else ""
                        checked_str = (
                            f" checked={elem['checked']}"
                            if elem.get("checked") is not None
                            else ""
                        )

                        print(f"    [{id_str:>5}] {name_str[:50]}{value_str}{checked_str}")

                all_mappings[title] = {
                    "size": f"{win['width']}x{win['height']}",
                    "elements": elements,
                    "mapped_at": datetime.now().isoformat(),
                }

            except Exception as e:
                print(f"  Error: {e}")

        # Export to JSON if requested
        if export_path:
            export_path = Path(export_path)
            try:
                with open(export_path, "w", encoding="utf-8") as f:
                    json.dump(all_mappings, f, ensure_ascii=False, indent=2)
                print(f"\n\nSaved element map to: {export_path}")
            except Exception as e:
                print(f"\nError saving: {e}")

        print("\n" + "=" * 70)
        print("MAPPING COMPLETE")
        print("=" * 70)

        return all_mappings
