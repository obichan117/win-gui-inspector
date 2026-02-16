"""Shared test fixtures for win-gui-inspector.

Provides mock pywinauto objects for testing without a live Windows desktop.
"""

from __future__ import annotations

from unittest.mock import MagicMock, PropertyMock

import pytest


def make_mock_element(
    name: str = "",
    control_type: str = "",
    automation_id: str = "",
    class_name: str = "",
    children: list | None = None,
    rect: tuple[int, int, int, int] | None = (0, 0, 100, 50),
    value: str = "",
    toggle_state: int | None = None,
) -> MagicMock:
    """Create a mock pywinauto element with element_info.

    Args:
        name: Element name.
        control_type: UIA control type (e.g., "Button", "Edit").
        automation_id: UIA automation ID.
        class_name: Window class name.
        children: List of child mock elements.
        rect: (left, top, width, height) or None.
        value: Value for Edit controls (legacy_properties).
        toggle_state: Toggle state for CheckBox controls.
    """
    elem = MagicMock()

    # element_info properties
    info = MagicMock()
    info.name = name
    info.control_type = control_type
    info.automation_id = automation_id
    info.class_name = class_name
    elem.element_info = info

    # Rectangle
    if rect:
        mock_rect = MagicMock()
        mock_rect.left = rect[0]
        mock_rect.top = rect[1]
        mock_rect.width.return_value = rect[2]
        mock_rect.height.return_value = rect[3]
        elem.rectangle.return_value = mock_rect
    else:
        elem.rectangle.side_effect = Exception("No rect")

    # Children
    elem.children.return_value = children or []

    # Edit value
    if value:
        elem.legacy_properties.return_value = {"Value": value}
    else:
        elem.legacy_properties.return_value = {}

    # CheckBox toggle
    if toggle_state is not None:
        elem.get_toggle_state.return_value = toggle_state
    else:
        elem.get_toggle_state.side_effect = Exception("Not a checkbox")

    # Window text (for window-level elements)
    elem.window_text.return_value = name
    type(elem).handle = PropertyMock(return_value=12345)

    return elem


@pytest.fixture
def mock_window():
    """A mock window with a small element tree."""
    buy_btn = make_mock_element(
        name="Buy",
        control_type="Button",
        automation_id="116",
    )
    sell_btn = make_mock_element(
        name="Sell",
        control_type="Button",
        automation_id="117",
    )
    symbol_field = make_mock_element(
        name="Symbol",
        control_type="Edit",
        automation_id="102",
        value="7203",
    )
    quantity_field = make_mock_element(
        name="Quantity",
        control_type="Edit",
        automation_id="136",
    )
    skip_check = make_mock_element(
        name="Skip confirmation",
        control_type="CheckBox",
        automation_id="200",
        toggle_state=1,
    )
    pane = make_mock_element(
        name="OrderPane",
        control_type="Pane",
        automation_id="pane1",
        children=[buy_btn, sell_btn, symbol_field, quantity_field, skip_check],
    )

    window = make_mock_element(
        name="Test Window",
        control_type="Window",
        automation_id="",
        class_name="TestClass",
        children=[pane],
        rect=(0, 0, 800, 600),
    )
    return window


@pytest.fixture
def mock_tiny_window():
    """A tiny window that should be filtered out by the mapper."""
    return make_mock_element(
        name="Tiny",
        control_type="Window",
        rect=(0, 0, 50, 50),
    )
