"""Tests for CLI argument parsing and dispatch."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from win_gui_inspector.cli import cmd_inspect, cmd_map, main, parse_args


class TestParseArgs:
    """Test argument parsing."""

    @patch("sys.argv", ["prog", "inspect", "--title", "Test"])
    def test_inspect_defaults(self):
        args = parse_args()
        assert args.command == "inspect"
        assert args.title == "Test"
        assert args.depth == 4
        assert args.export is False
        assert args.backend == "uia"

    @patch(
        "sys.argv",
        [
            "prog",
            "inspect",
            "--title",
            "MyApp",
            "--depth",
            "6",
            "--export",
            "--screen",
            "order",
            "--output",
            "out.yaml",
        ],
    )
    def test_inspect_all_options(self):
        args = parse_args()
        assert args.depth == 6
        assert args.export is True
        assert args.screen == "order"
        assert args.output == "out.yaml"

    @patch("sys.argv", ["prog", "map", "--title", "Test"])
    def test_map_defaults(self):
        args = parse_args()
        assert args.command == "map"
        assert args.title == "Test"
        assert args.depth == 5
        assert args.export is None

    @patch("sys.argv", ["prog", "map", "--title", "App", "--export", "out.json", "--depth", "3"])
    def test_map_with_export(self):
        args = parse_args()
        assert args.export == "out.json"
        assert args.depth == 3

    @patch("sys.argv", ["prog", "--version"])
    def test_version_flag(self):
        args = parse_args()
        assert args.version is True


class TestCmdDispatch:
    """Test command dispatch."""

    @patch("win_gui_inspector.inspector.UIInspector")
    @patch("sys.argv", ["prog", "inspect", "--title", "Test"])
    def test_cmd_inspect_interactive(self, mock_inspector_cls):
        mock_inspector = MagicMock()
        mock_inspector.connect.return_value = True
        mock_inspector_cls.return_value = mock_inspector

        args = parse_args()
        result = cmd_inspect(args)

        assert result == 0
        mock_inspector.interactive_mode.assert_called_once()

    @patch("win_gui_inspector.inspector.UIInspector")
    @patch("sys.argv", ["prog", "inspect", "--title", "Test", "--export"])
    def test_cmd_inspect_export(self, mock_inspector_cls):
        mock_inspector = MagicMock()
        mock_inspector.connect.return_value = True
        mock_inspector_cls.return_value = mock_inspector

        args = parse_args()
        result = cmd_inspect(args)

        assert result == 0
        mock_inspector.scan_current_screen.assert_called_once()
        mock_inspector.export_to_yaml.assert_called_once()

    @patch("win_gui_inspector.inspector.UIInspector")
    @patch("sys.argv", ["prog", "inspect", "--title", "Test"])
    def test_cmd_inspect_connect_failure(self, mock_inspector_cls):
        mock_inspector = MagicMock()
        mock_inspector.connect.return_value = False
        mock_inspector_cls.return_value = mock_inspector

        args = parse_args()
        result = cmd_inspect(args)

        assert result == 1

    @patch("win_gui_inspector.mapper.WindowMapper")
    @patch("sys.argv", ["prog", "map", "--title", "Test"])
    def test_cmd_map(self, mock_mapper_cls):
        mock_mapper = MagicMock()
        mock_mapper_cls.return_value = mock_mapper

        args = parse_args()
        result = cmd_map(args)

        assert result == 0
        mock_mapper.run.assert_called_once()

    @patch("sys.argv", ["prog", "--version"])
    def test_main_version(self):
        result = main()
        assert result == 0
