# Workflow Guide

How to use win-gui-inspector to map out a Windows application's UI for automation.

This documents the workflow used during development of [ms2auto](https://github.com/obichan117/marketspeed2-autogui), where every screen of the Rakuten MarketSpeed2 trading application was systematically mapped to build a YAML element registry.

## Step 1: Discover All Windows

Start by mapping everything the application exposes:

```bash
win-gui-inspector map --title "MarketSpeed" --export full_map.json
```

This produces a complete inventory of every window and every UI element (buttons, text fields, checkboxes, combo boxes, tabs, etc.) across the entire application.

Example output:

```
FINDING WINDOWS
======================================================================

Found 5 windows:
  1. [MarketSpeed II] 1920x1080
  2. [リンク注文(現物買い→現物売り)] 800x600
  3. [リンク注文(信用新規→信用返済)] 800x600
  4. [建玉一覧] 600x400
  5. [信用全返済] 400x300

MAPPING: リンク注文(現物買い→現物売り)
======================================================================

Found 42 elements:

  === Button (8) ===
    [  116] 買い
    [  117] 売り
    [  140] 注文発注
    ...

  === Edit (5) ===
    [  102] 銘柄コード value=[]
    [  136] 数量 value=[]
    ...
```

## Step 2: Interactive Drill-Down

For each screen that needs automation, use the interactive inspector for detailed exploration:

```bash
win-gui-inspector inspect --title "注文" --depth 5
```

REPL session:

```
> scan order_entry
[Scanning] order_entry (depth=5)...

[OK] Scanned 'order_entry'
----------------------------------------------------------------------
ELEMENT SUMMARY
----------------------------------------------------------------------
  Button: 8
  Edit: 5
  CheckBox: 2
  ComboBox: 1
  RadioButton: 4

> find Button
[Button] (8 found)
  - Name: '買い' | ID: 116
  - Name: '売り' | ID: 117
  - Name: '注文発注' | ID: 140
  ...

> find Edit
[Edit] (5 found)
  - Name: '銘柄コード' | ID: 102
  - Name: '数量' | ID: 136
  ...

> export order_elements.yaml
[OK] Exported to: order_elements.yaml
```

## Step 3: Build Element Registry

Take the exported data and manually curate it into a structured element map:

**From inspector export:**
```yaml
# Raw scan results:
#   Button "買い" (ID: 116)
#   Button "売り" (ID: 117)
#   Edit "銘柄コード" (ID: 102)
#   Edit "数量" (ID: 136)
```

**Curated into structured registry:**
```yaml
windows:
  spot_order:
    title_pattern: "リンク注文(現物買い→現物売り)"
    class_name: "xWinClass"

spot_order_entry:
  inputs:
    symbol:
      automation_id: "102"
      control_type: "Edit"
      description: "Stock symbol input"
    quantity:
      automation_id: "136"
      control_type: "Edit"
  side:
    buy:
      automation_id: "116"
    sell:
      automation_id: "117"
  actions:
    submit:
      automation_id: "140"
      control_type: "Button"
```

This structured YAML becomes the single source of truth for your automation code.

## Step 4: Verify After Updates

When the target application updates, re-run the mapper and compare:

```bash
win-gui-inspector map --title "MarketSpeed" --export current_map.json
```

Compare `current_map.json` against your previous export to identify any element ID changes. Update your registry accordingly.

## Tips

- **Start with depth 3-4** for the initial scan. Increase if you're missing deeply nested elements.
- **Use `--title` with specific patterns** to focus on one window at a time. Scanning too many windows at once can be slow.
- **Look for `automation_id` first** -- these are the most stable identifiers. Fall back to `name` only when no ID exists.
- **Elements without both `id` and `name`** are filtered out by the mapper as they can't be reliably targeted for automation.
- **CheckBox states and Edit values** are captured by the mapper, which helps identify the current state of form elements.
