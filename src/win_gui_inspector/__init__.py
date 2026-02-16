"""Windows GUI element inspector and mapper.

Generic tool for discovering UI elements in any Windows application
using pywinauto. No broker or application-specific dependencies.

Usage:
    # CLI
    win-gui-inspector inspect --title "MarketSpeed" --depth 4
    win-gui-inspector map --title "MarketSpeed" --export elements.json

    # Python API
    from win_gui_inspector import UIInspector, WindowMapper
    inspector = UIInspector(window_title="MarketSpeed", max_depth=4)
"""

__version__ = "0.1.0"

from win_gui_inspector.inspector import UIInspector
from win_gui_inspector.mapper import WindowMapper

__all__ = [
    "__version__",
    "UIInspector",
    "WindowMapper",
]
