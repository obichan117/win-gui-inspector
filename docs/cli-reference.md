# CLI Reference

## Commands

### `win-gui-inspector inspect`

Interactive UI element inspector. Connects to a window and provides a REPL for exploring its element tree.

```bash
win-gui-inspector inspect --title "MyApp"
win-gui-inspector inspect --title "MyApp" --depth 6
win-gui-inspector inspect --title "MyApp" --export --output elements.yaml
win-gui-inspector inspect --title "MyApp" --export --screen order_entry
```

| Option | Default | Description |
|---|---|---|
| `--title` | None | Window title pattern (regex). If omitted, lists available windows. |
| `--class-name` | None | Window class name filter |
| `--depth` | 4 | Max scan depth for element tree traversal |
| `--export` | False | Scan and export to YAML immediately (non-interactive) |
| `--screen` | `main` | Screen name label for export grouping |
| `--output` | `inspector_export.yaml` | Output file path for YAML export |
| `--backend` | `uia` | pywinauto backend (`uia` or `win32`) |

#### REPL Commands

When running in interactive mode:

| Command | Description |
|---|---|
| `scan [name]` | Scan current window. Optional name is used as a label in exports. |
| `tree` | Print the element tree (first 3 levels) |
| `summary` | Print element count by type + list key elements |
| `export` | Export all scans to YAML |
| `depth N` | Change the scan depth |
| `quit` / `q` | Exit |

---

### `win-gui-inspector map`

Bulk-map all windows matching a pattern. Discovers windows, maps every element in each, and optionally exports to JSON.

```bash
win-gui-inspector map --title "MyApp"
win-gui-inspector map --title "MyApp" --export elements.json
win-gui-inspector map --title "MyApp" --depth 6
```

| Option | Default | Description |
|---|---|---|
| `--title` | None | Window title pattern (regex). If omitted, maps all visible windows. |
| `--export` | None | Export element map to a JSON file at this path |
| `--depth` | 5 | Max scan depth for element tree traversal |
| `--backend` | `uia` | pywinauto backend (`uia` or `win32`) |

#### Output Format

Console output groups elements by control type with deduplication:

```
=== Button (5) ===
  [  116] Buy
  [  117] Sell
  [  140] Submit

=== Edit (3) ===
  [  102] Symbol value=[7203]
  [  136] Quantity
```

JSON export format:

```json
{
  "Window Title": {
    "size": "800x600",
    "elements": [
      {"depth": 2, "type": "Button", "id": "116", "name": "Buy", "class": "ButtonClass"},
      {"depth": 2, "type": "Edit", "id": "102", "name": "Symbol", "class": "EditClass", "value": "7203"}
    ],
    "mapped_at": "2026-02-16T10:30:00"
  }
}
```

---

### `win-gui-inspector --version`

Show the installed version.

```bash
win-gui-inspector --version
```
