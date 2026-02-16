"""Tests for WindowMapper."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from tests.conftest import make_mock_element
from win_gui_inspector.mapper import WindowMapper


class TestFindWindows:
    """Test window discovery."""

    @patch("win_gui_inspector.mapper.Desktop")
    def test_find_windows_returns_visible(self, mock_desktop_cls):
        mock_desktop = MagicMock()
        mock_desktop_cls.return_value = mock_desktop

        win1 = make_mock_element(name="App Window", rect=(0, 0, 800, 600))
        win2 = make_mock_element(name="Dialog", rect=(100, 100, 400, 300))

        mock_desktop.windows.return_value = [win1, win2]

        mapper = WindowMapper()
        windows = mapper.find_windows()

        assert len(windows) == 2
        assert windows[0]["title"] == "App Window"
        assert windows[0]["width"] == 800
        assert windows[1]["title"] == "Dialog"

    @patch("win_gui_inspector.mapper.Desktop")
    def test_find_windows_filters_tiny(self, mock_desktop_cls):
        mock_desktop = MagicMock()
        mock_desktop_cls.return_value = mock_desktop

        big = make_mock_element(name="Main", rect=(0, 0, 800, 600))
        tiny = make_mock_element(name="Hidden", rect=(0, 0, 50, 50))

        mock_desktop.windows.return_value = [big, tiny]

        mapper = WindowMapper()
        windows = mapper.find_windows()

        assert len(windows) == 1
        assert windows[0]["title"] == "Main"

    @patch("win_gui_inspector.mapper.Desktop")
    def test_find_windows_with_title_pattern(self, mock_desktop_cls):
        mock_desktop = MagicMock()
        mock_desktop_cls.return_value = mock_desktop
        mock_desktop.windows.return_value = []

        mapper = WindowMapper(title_pattern="Order.*")
        mapper.find_windows()

        mock_desktop.windows.assert_called_with(title_re="Order.*")

    @patch("win_gui_inspector.mapper.Desktop")
    def test_find_windows_skips_untitled(self, mock_desktop_cls):
        mock_desktop = MagicMock()
        mock_desktop_cls.return_value = mock_desktop

        untitled = make_mock_element(name="", rect=(0, 0, 800, 600))
        mock_desktop.windows.return_value = [untitled]

        mapper = WindowMapper()
        windows = mapper.find_windows()

        assert len(windows) == 0


class TestMapWindowElements:
    """Test element extraction."""

    def test_extracts_useful_elements(self, mock_window):
        mapper = WindowMapper(max_depth=5)
        elements = mapper.map_window_elements(mock_window)

        types = [e["type"] for e in elements]
        assert types.count("Button") == 2
        assert types.count("Edit") == 2
        assert types.count("CheckBox") == 1

    def test_extracts_edit_values(self):
        edit = make_mock_element(
            name="Price",
            control_type="Edit",
            automation_id="50",
            value="1500",
        )
        window = make_mock_element(
            name="Win",
            control_type="Window",
            children=[edit],
        )

        mapper = WindowMapper(max_depth=2)
        elements = mapper.map_window_elements(window)

        price_elem = next(e for e in elements if e["name"] == "Price")
        assert price_elem["value"] == "1500"

    def test_extracts_checkbox_state(self):
        cb = make_mock_element(
            name="Agree",
            control_type="CheckBox",
            automation_id="99",
            toggle_state=0,
        )
        window = make_mock_element(
            name="Win",
            control_type="Window",
            children=[cb],
        )

        mapper = WindowMapper(max_depth=2)
        elements = mapper.map_window_elements(window)

        cb_elem = next(e for e in elements if e["name"] == "Agree")
        assert cb_elem["checked"] == 0

    def test_respects_depth_limit(self, mock_window):
        mapper = WindowMapper(max_depth=0)
        elements = mapper.map_window_elements(mock_window)

        assert len(elements) == 0

    def test_skips_elements_without_id_or_name(self):
        anon = make_mock_element(
            name="",
            control_type="Button",
            automation_id="",
        )
        window = make_mock_element(
            name="Win",
            control_type="Window",
            children=[anon],
        )

        mapper = WindowMapper(max_depth=2)
        elements = mapper.map_window_elements(window)

        assert len(elements) == 0


class TestRun:
    """Test full mapping workflow."""

    @patch("win_gui_inspector.mapper._ensure_utf8_output")
    @patch("win_gui_inspector.mapper.Application")
    @patch("win_gui_inspector.mapper.Desktop")
    def test_run_exports_json(
        self, mock_desktop_cls, mock_app_cls, _mock_utf8, mock_window, tmp_path
    ):
        mock_desktop = MagicMock()
        mock_desktop_cls.return_value = mock_desktop
        mock_desktop.windows.return_value = [mock_window]

        mock_app = MagicMock()
        mock_app_cls.return_value.connect.return_value = mock_app
        mock_app.window.return_value = mock_window

        output = tmp_path / "map.json"
        mapper = WindowMapper(max_depth=4)
        result = mapper.run(export_path=str(output))

        assert len(result) == 1
        assert output.exists()

        with open(output, encoding="utf-8") as f:
            data = json.load(f)
        assert "Test Window" in data

    @patch("win_gui_inspector.mapper._ensure_utf8_output")
    @patch("win_gui_inspector.mapper.Desktop")
    def test_run_no_windows(self, mock_desktop_cls, _mock_utf8):
        mock_desktop = MagicMock()
        mock_desktop_cls.return_value = mock_desktop
        mock_desktop.windows.return_value = []

        mapper = WindowMapper()
        result = mapper.run()

        assert result == {}
