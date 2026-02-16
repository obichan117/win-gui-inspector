# win-gui-inspector

A dev tool for discovering UI elements in Windows applications using [pywinauto](https://github.com/pywinauto/pywinauto).

Used during the development phase of GUI automation projects to scan windows, find element IDs/names/types, and export the results to YAML or JSON.

## Installation

```bash
pip install win-gui-inspector
```

Or with uv:

```bash
uv add win-gui-inspector
```

## Quick Start

### Interactive Inspector

Connect to a window and explore its element tree interactively:

```bash
win-gui-inspector inspect --title "Notepad"
```

This opens a REPL where you can scan elements, browse the tree, and export results:

```
> scan main
> summary
> tree
> export elements.yaml
> quit
```

### Bulk Mapper

Auto-discover all windows of an application and map every UI element:

```bash
win-gui-inspector map --title "MyApp" --export elements.json
```

## Python API

```python
from win_gui_inspector import UIInspector, WindowMapper

# Interactive inspection
inspector = UIInspector(window_title="Notepad", max_depth=4)
inspector.connect()
result = inspector.scan_current_screen("main")
inspector.export_to_yaml("elements.yaml")

# Bulk mapping
mapper = WindowMapper(title_pattern="MyApp")
results = mapper.run(export_path="elements.json")
```

## Origin

Extracted from the [ms2auto](https://github.com/obichan117/marketspeed2-autogui) project where it was used to map all UI elements in the Rakuten MarketSpeed2 trading application. The code is generic -- no application-specific dependencies.
