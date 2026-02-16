"""Tests for UIInspector."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import yaml

from win_gui_inspector.inspector import UIInspector


class TestScanElement:
    """Test recursive element scanning."""

    def test_scan_returns_element_info(self, mock_window):
        inspector = UIInspector(max_depth=4)
        result = inspector.scan_element(mock_window)

        assert result["name"] == "Test Window"
        assert result["control_type"] == "Window"
        assert result["depth"] == 0
        assert len(result["children"]) == 1  # pane

    def test_scan_respects_depth_limit(self, mock_window):
        inspector = UIInspector(max_depth=0)
        result = inspector.scan_element(mock_window)

        # At depth 0, the root itself is scanned but children are at depth 1
        assert result["children"] == []

    def test_scan_builds_paths(self, mock_window):
        inspector = UIInspector(max_depth=4)
        result = inspector.scan_element(mock_window)

        pane = result["children"][0]
        assert pane["path"] == "Test Window/pane1"

        buy = pane["children"][0]
        assert buy["path"] == "Test Window/pane1/116"

    def test_scan_includes_rectangle(self, mock_window):
        inspector = UIInspector(max_depth=1)
        result = inspector.scan_element(mock_window)

        assert result["rectangle"]["width"] == 800
        assert result["rectangle"]["height"] == 600

    def test_scan_handles_broken_element(self):
        """Elements that raise exceptions are handled gracefully."""
        broken = MagicMock()
        broken.element_info = property(lambda _: (_ for _ in ()).throw(Exception("broken")))
        type(broken).element_info = property(lambda _: (_ for _ in ()).throw(Exception("broken")))

        inspector = UIInspector(max_depth=2)
        result = inspector.scan_element(broken)

        assert "error" in result


class TestFindElementsByType:
    """Test element type filtering."""

    def test_find_buttons(self, mock_window):
        inspector = UIInspector(max_depth=4)
        tree = inspector.scan_element(mock_window)

        buttons = inspector.find_elements_by_type(tree, "Button")
        assert len(buttons) == 2
        names = {b["name"] for b in buttons}
        assert names == {"Buy", "Sell"}

    def test_find_edits(self, mock_window):
        inspector = UIInspector(max_depth=4)
        tree = inspector.scan_element(mock_window)

        edits = inspector.find_elements_by_type(tree, "Edit")
        assert len(edits) == 2

    def test_find_nonexistent_type(self, mock_window):
        inspector = UIInspector(max_depth=4)
        tree = inspector.scan_element(mock_window)

        menus = inspector.find_elements_by_type(tree, "MenuItem")
        assert menus == []


class TestExportToYaml:
    """Test YAML export."""

    def test_export_creates_file(self, mock_window, tmp_path):
        inspector = UIInspector(max_depth=4)
        inspector.window = mock_window
        inspector.scan_current_screen("test_screen")

        output = tmp_path / "export.yaml"
        result_path = inspector.export_to_yaml(output)

        assert result_path == output
        assert output.exists()

    def test_export_yaml_structure(self, mock_window, tmp_path):
        inspector = UIInspector(max_depth=4)
        inspector.window = mock_window
        inspector.scan_current_screen("test_screen")

        output = tmp_path / "export.yaml"
        inspector.export_to_yaml(output)

        with open(output, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        assert data["version"] == "1.0"
        assert "generated_at" in data
        assert "test_screen" in data["screens"]

        screen = data["screens"]["test_screen"]
        assert "buttons" in screen["elements"]
        assert "text_fields" in screen["elements"]
        assert len(screen["elements"]["buttons"]) == 2

    def test_export_default_path(self, mock_window, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)

        inspector = UIInspector(max_depth=4)
        inspector.window = mock_window
        inspector.scan_current_screen("main")

        result_path = inspector.export_to_yaml()
        assert result_path == Path("inspector_export.yaml")


class TestConnect:
    """Test window connection."""

    @patch("win_gui_inspector.inspector._ensure_utf8_output")
    @patch("win_gui_inspector.inspector.Desktop")
    def test_connect_with_pattern(self, mock_desktop_cls, _mock_utf8):
        mock_desktop = MagicMock()
        mock_desktop_cls.return_value = mock_desktop
        mock_window = MagicMock()
        mock_window.window_text.return_value = "Test App"
        mock_window.handle = 12345
        mock_desktop.window.return_value = mock_window

        inspector = UIInspector(window_title="Test")
        result = inspector.connect()

        assert result is True
        assert inspector.window is mock_window

    @patch("win_gui_inspector.inspector._ensure_utf8_output")
    @patch("win_gui_inspector.inspector.Desktop")
    def test_connect_no_pattern_lists_windows(self, mock_desktop_cls, _mock_utf8):
        mock_desktop = MagicMock()
        mock_desktop_cls.return_value = mock_desktop
        mock_desktop.windows.return_value = []

        inspector = UIInspector()
        result = inspector.connect()

        assert result is False

    @patch("win_gui_inspector.inspector._ensure_utf8_output")
    @patch("win_gui_inspector.inspector.Desktop")
    def test_connect_pattern_not_found(self, mock_desktop_cls, _mock_utf8):
        mock_desktop = MagicMock()
        mock_desktop_cls.return_value = mock_desktop
        mock_desktop.window.side_effect = Exception("Not found")

        inspector = UIInspector(window_title="NonExistent")
        result = inspector.connect()

        assert result is False
