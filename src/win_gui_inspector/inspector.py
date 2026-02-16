"""Full recursive UI element inspector for Windows applications.

Generalized from ms2auto/cli/inspector.py — no broker-specific dependencies.
Uses pywinauto Desktop(backend="uia") to connect to any Windows application.
"""

from __future__ import annotations

import io
import sys
from datetime import datetime
from pathlib import Path

import yaml
from pywinauto import Desktop


def _ensure_utf8_output() -> None:
    """Force UTF-8 output for non-ASCII text on Windows."""
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "buffer"):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


class UIInspector:
    """Interactive UI element inspector for any Windows application."""

    def __init__(
        self,
        window_title: str | None = None,
        window_class: str | None = None,
        max_depth: int = 4,
        backend: str = "uia",
    ) -> None:
        self.window_title = window_title
        self.window_class = window_class
        self.max_depth = max_depth
        self.backend = backend
        self.elements: dict[str, dict] = {}
        self.window = None

    def connect(self, window_pattern: str | None = None) -> bool:
        """Connect to a window by title pattern.

        Args:
            window_pattern: Regex pattern to match window title.
                Overrides self.window_title if provided.

        Returns:
            True if connection successful.
        """
        _ensure_utf8_output()

        pattern = window_pattern or self.window_title

        print("\n" + "=" * 70)
        print("Windows GUI Inspector")
        print("=" * 70)

        desktop = Desktop(backend=self.backend)

        if pattern:
            try:
                self.window = desktop.window(title_re=pattern)
                title = self.window.window_text()
                print(f"\n[OK] Found window: {title}")
                print(f"     Handle: {self.window.handle}")
                return True
            except Exception as e:
                print(f"\n[ERROR] Window not found matching: {pattern} ({e})")
                return False
        else:
            # List available windows
            windows = desktop.windows()
            if windows:
                print(f"\nAvailable windows ({len(windows)}):")
                for w in windows[:20]:
                    try:
                        print(f"  - {w.window_text()}")
                    except Exception:
                        pass
                print("\nSpecify --title to connect to a window.")
            return False

    def scan_element(self, element: object, depth: int = 0, parent_path: str = "") -> dict:
        """Recursively scan an element and its children."""
        if depth > self.max_depth:
            return {}

        try:
            info = element.element_info  # type: ignore[attr-defined]
            name = info.name or ""
            control_type = info.control_type or ""
            automation_id = info.automation_id or ""
            class_name = info.class_name or ""

            path_segment = automation_id or name or control_type
            current_path = f"{parent_path}/{path_segment}" if parent_path else path_segment

            try:
                rect = element.rectangle()  # type: ignore[attr-defined]
                rect_info = {
                    "left": rect.left,
                    "top": rect.top,
                    "width": rect.width(),
                    "height": rect.height(),
                }
            except Exception:
                rect_info = None

            result: dict = {
                "name": name,
                "control_type": control_type,
                "automation_id": automation_id,
                "class_name": class_name,
                "path": current_path,
                "depth": depth,
                "rectangle": rect_info,
                "children": [],
            }

            try:
                for child in element.children():  # type: ignore[attr-defined]
                    child_info = self.scan_element(child, depth + 1, current_path)
                    if child_info:
                        result["children"].append(child_info)
            except Exception:
                pass

            return result

        except Exception as e:
            return {"error": str(e), "depth": depth}

    def scan_current_screen(self, screen_name: str = "main") -> dict:
        """Scan all elements on the current screen."""
        print(f"\n[Scanning] {screen_name} (depth={self.max_depth})...")
        print("           This may take a moment...")

        result = self.scan_element(self.window)
        result["screen_name"] = screen_name
        result["scanned_at"] = datetime.now().isoformat()

        self.elements[screen_name] = result
        return result

    def print_element_tree(self, element: dict, indent: int = 0, max_print_depth: int = 3) -> None:
        """Print element tree in a readable format."""
        if indent > max_print_depth * 2:
            return

        prefix = "  " * indent
        name = element.get("name", "")
        ctrl_type = element.get("control_type", "")
        auto_id = element.get("automation_id", "")

        if (
            name
            or auto_id
            or ctrl_type in ["Button", "Edit", "MenuItem", "TabItem", "ComboBox"]
        ):
            line = f"{prefix}[{ctrl_type}]"
            if name:
                line += f" '{name}'"
            if auto_id:
                line += f" (ID: {auto_id})"
            print(line)

        for child in element.get("children", []):
            self.print_element_tree(child, indent + 1, max_print_depth)

    def find_elements_by_type(
        self, element: dict, control_type: str, results: list[dict] | None = None
    ) -> list[dict]:
        """Find all elements of a specific control type."""
        if results is None:
            results = []

        if element.get("control_type") == control_type:
            results.append(
                {
                    "name": element.get("name", ""),
                    "automation_id": element.get("automation_id", ""),
                    "path": element.get("path", ""),
                    "rectangle": element.get("rectangle"),
                }
            )

        for child in element.get("children", []):
            self.find_elements_by_type(child, control_type, results)

        return results

    def print_summary(self, screen_data: dict) -> None:
        """Print a summary of discovered elements."""
        print("\n" + "-" * 70)
        print("ELEMENT SUMMARY")
        print("-" * 70)

        type_counts: dict[str, int] = {}

        def count_types(elem: dict) -> None:
            ctrl_type = elem.get("control_type", "Unknown")
            type_counts[ctrl_type] = type_counts.get(ctrl_type, 0) + 1
            for child in elem.get("children", []):
                count_types(child)

        count_types(screen_data)

        for ctrl_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            if count > 0:
                print(f"  {ctrl_type}: {count}")

        print("\n" + "-" * 70)
        print("KEY ELEMENTS")
        print("-" * 70)

        for ctrl_type in ["Button", "Edit", "MenuItem", "TabItem", "ComboBox"]:
            elements = self.find_elements_by_type(screen_data, ctrl_type)
            if elements:
                print(f"\n[{ctrl_type}] ({len(elements)} found)")
                for elem in elements[:10]:
                    name = elem["name"] or "(no name)"
                    auto_id = elem["automation_id"] or "(no id)"
                    print(f"  - Name: '{name}' | ID: {auto_id}")

    def export_to_yaml(self, output_path: str | Path | None = None) -> Path:
        """Export discovered elements to YAML file."""
        if output_path is None:
            output_path = Path("inspector_export.yaml")

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        export_data: dict = {
            "version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "screens": {},
        }

        for screen_name, screen_data in self.elements.items():
            export_data["screens"][screen_name] = {
                "scanned_at": screen_data.get("scanned_at"),
                "elements": {
                    "buttons": self.find_elements_by_type(screen_data, "Button"),
                    "text_fields": self.find_elements_by_type(screen_data, "Edit"),
                    "menu_items": self.find_elements_by_type(screen_data, "MenuItem"),
                    "tabs": self.find_elements_by_type(screen_data, "TabItem"),
                    "combo_boxes": self.find_elements_by_type(screen_data, "ComboBox"),
                },
            }

        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(export_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

        print(f"\n[OK] Exported to: {output_path}")
        return output_path

    def interactive_mode(self) -> None:
        """Run interactive discovery session."""
        print("\n" + "=" * 70)
        print("INTERACTIVE MODE")
        print("=" * 70)
        print("\nCommands:")
        print("  scan [name]  - Scan current screen (default: 'main')")
        print("  tree         - Print element tree of last scan")
        print("  summary      - Print element summary of last scan")
        print("  export       - Export all scans to YAML")
        print(f"  depth N      - Set scan depth (current: {self.max_depth})")
        print("  quit         - Exit")

        last_scan: dict | None = None

        while True:
            try:
                cmd = input("\n> ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                break

            if not cmd:
                continue

            parts = cmd.split()
            action = parts[0]

            if action in ("quit", "q"):
                break
            elif action == "scan":
                screen_name = parts[1] if len(parts) > 1 else "main"
                last_scan = self.scan_current_screen(screen_name)
                print(f"\n[OK] Scanned '{screen_name}'")
                self.print_summary(last_scan)
            elif action == "tree":
                if last_scan:
                    print("\n" + "-" * 70)
                    print("ELEMENT TREE (first 3 levels)")
                    print("-" * 70)
                    self.print_element_tree(last_scan)
                else:
                    print("[!] No scan data. Run 'scan' first.")
            elif action == "summary":
                if last_scan:
                    self.print_summary(last_scan)
                else:
                    print("[!] No scan data. Run 'scan' first.")
            elif action == "export":
                if self.elements:
                    self.export_to_yaml()
                else:
                    print("[!] No scan data. Run 'scan' first.")
            elif action == "depth":
                if len(parts) > 1:
                    try:
                        self.max_depth = int(parts[1])
                        print(f"[OK] Scan depth set to {self.max_depth}")
                    except ValueError:
                        print("[!] Invalid depth value")
                else:
                    print(f"[INFO] Current depth: {self.max_depth}")
            else:
                print(f"[!] Unknown command: {action}")
