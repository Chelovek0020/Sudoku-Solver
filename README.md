# Sudoku Studio

Desktop Sudoku app (Python + Tkinter) with solver, generator, tabs, and multiple Sudoku variants.

## Features

- Board size from **3x3 to 30x30**.
- Variants (single-choice): **Classic**, **Diagonal**, **Hyper**, **Killer**.
- Rule validation while typing.
- Multi-cell selection (drag, Shift+click), delete selection with `Del`.
- Keyboard input, arrow movement, and solve shortcut via keypad arrow button.
- Multi-tab support for working with several boards simultaneously.
- Killer cages editor (text format + create cage from selected cells).
- Built-in puzzle generator (easy/medium/hard).
- Save puzzle/solution to PNG with adaptive font sizing.
- EN/RU language support (default: English).

## Local run

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python src/main.py
```

## Build locally

```bash
pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm --onefile --windowed --name SudokuSolver src/main.py
```

If you place your icon in `assets/app.ico`, include `--icon assets/app.ico`.

## Killer format

```text
15:r1c1,r1c2;10:r2c1,r3c1
```

`rXcY` coordinates are 1-based.

## GitHub Actions output variants

On tag push `v*`, workflow builds 3 variants per OS:

1. **embedded** – onefile executable with Python/deps bundled.
2. **thin** – source package requiring Python and dependencies on user machine.
3. **beta-compressed** – onefile bundled build with UPX compression when available.
