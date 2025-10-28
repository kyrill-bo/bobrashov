# LightBurn to PNG

Two ways to use:

- CLI
  - python script.py input.lbrn2 [output.png]
  - If output is omitted, input.png is placed next to the input file.
- GUI (Tkinter)
  - pip install -r requirements.txt
  - python gui.py
  - Drag files into the list (needs TkinterDnD2). If TkinterDnD2 isn’t installed, use the "Dateien hinzufügen" button.

- GUI (Qt, no Tk required)
  - pip install -r requirements.txt  # ensures PySide6
  - python gui_qt.py
  - Drag & Drop of files and folders supported natively.

## Output location

- The GUI writes PNGs to a subfolder (default: `png`) next to each input file. You can change the subfolder name in the GUI.

## Dependencies

- CairoSVG for vector to PNG rendering: `pip install cairosvg`
- TkinterDnD2 for drag & drop (optional): `pip install TkinterDnD2`

On macOS, Tkinter is included with Python.org installers. If you use a different Python distribution and get GUI errors, install a Python build with Tk support.

## Troubleshooting (macOS)

Error: `ModuleNotFoundError: No module named '_tkinter'`

This means your Python was built without Tk support.

Options:

1) Recommended: Install Python from python.org (includes Tk), then recreate your virtual environment and run the GUI.
   - https://www.python.org/downloads/macos/

2) Advanced: Use Homebrew tcl-tk with pyenv to build Python with Tk:
   - `brew install tcl-tk pyenv`
   - Add to zshrc:
     - `export PATH="/opt/homebrew/opt/tcl-tk/bin:$PATH"`
     - `export LDFLAGS="-L/opt/homebrew/opt/tcl-tk/lib"`
     - `export CPPFLAGS="-I/opt/homebrew/opt/tcl-tk/include"`
     - `export PKG_CONFIG_PATH="/opt/homebrew/opt/tcl-tk/lib/pkgconfig"`
   - Build Python with Tk (example):
     - `CONFIGURE_OPTS="--with-tcltk-includes='-I/opt/homebrew/opt/tcl-tk/include' --with-tcltk-libs='-L/opt/homebrew/opt/tcl-tk/lib -ltcl8.6 -ltk8.6'" pyenv install 3.12.4`
     - `pyenv local 3.12.4 && python -m venv .venv && source .venv/bin/activate`

If Tkinter is unavailable, the GUI won't run, but the CLI (`script.py`) still works.

If you prefer not to install Tkinter, use the Qt GUI (`gui_qt.py`).

## Windows: Build an EXE

Recommended target: Qt GUI (`gui_qt.py`). Build on Windows using PyInstaller.

1) Setup a venv and install deps:
  - `python -m venv venv`
  - `venv\Scripts\activate`
  - `pip install -r requirements.txt`

2) Run locally to test:
  - `python gui_qt.py`

3) Build a one-file EXE:
  - `pip install pyinstaller`
  - `pyinstaller --noconsole --onefile --name LightBurnPNG gui_qt.py`

Output: `dist\LightBurnPNG.exe`

Notes:
- CairoSVG is optional now: script falls back to Qt rendering (PySide6) if CairoSVG isn't present. The Qt fallback doesn't render external <image> hrefs; for embedded bitmaps and relative image references, CairoSVG is preferred.
- If onefile has issues with Qt plugins, try `--onedir` instead: `pyinstaller --noconsole --onedir --name LightBurnPNG gui_qt.py`
