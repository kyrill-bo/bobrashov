#!/usr/bin/env python3
"""
Qt GUI (PySide6) für den Export von LightBurn .lbrn/.lbrn2 nach PNG.

Vorteil: Kein Tkinter erforderlich (umgeht '_tkinter' Problem auf macOS).

Features:
- Drag & Drop von Dateien/Ordnern
- Liste verwalten (hinzufügen/entfernen/leeren)
- Ziel-Unterordner konfigurierbar (Standard: "png")
- Optional: bestehende Dateien überschreiben
- Log-Ausgabe

Start:
  pip install -r requirements.txt  # stellt PySide6/CairoSVG sicher
  python gui_qt.py
"""
from __future__ import annotations

import sys
import base64
from pathlib import Path
from typing import List

try:
    from PySide6 import QtCore, QtGui, QtWidgets
except Exception as e:
    print("PySide6 ist nicht installiert. Bitte ausführen: pip install PySide6")
    sys.exit(1)

try:
    from script import build_svg, write_png
except Exception as e:
    print("Fehler: Konnte Funktionen aus script.py nicht importieren. Stelle sicher, dass script.py im selben Ordner liegt.")
    sys.exit(1)


class DropListWidget(QtWidgets.QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event: QtGui.QDragMoveEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event: QtGui.QDropEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                p = Path(url.toLocalFile())
                self._add_path(p)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

    def _add_path(self, p: Path):
        if p.is_dir():
            for f in sorted(p.glob("**/*.lbrn*")):
                self._add_file(f)
        else:
            self._add_file(p)

    def _add_file(self, p: Path):
        if not p.exists():
            return
        if p.suffix.lower() not in (".lbrn", ".lbrn2"):
            return
        # avoid duplicates
        items = self.findItems(str(p), QtCore.Qt.MatchExactly)
        if items:
            return
        self.addItem(str(p))


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LightBurn → PNG Export (Qt)")
        self.resize(900, 600)

        central = QtWidgets.QWidget(self)
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)

        # Top area: list + side panel
        top_split = QtWidgets.QSplitter(self)
        top_split.setOrientation(QtCore.Qt.Horizontal)
        layout.addWidget(top_split, 1)

        left = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left)
        top_split.addWidget(left)

        info_label = QtWidgets.QLabel("Dateien/Ordner hier ablegen oder per Button hinzufügen")
        left_layout.addWidget(info_label)

        self.list_widget = DropListWidget()
        left_layout.addWidget(self.list_widget, 1)

        btn_row = QtWidgets.QHBoxLayout()
        left_layout.addLayout(btn_row)

        add_btn = QtWidgets.QPushButton("Dateien hinzufügen")
        add_btn.clicked.connect(self.add_files_dialog)
        btn_row.addWidget(add_btn)

        rem_btn = QtWidgets.QPushButton("Aus Liste entfernen")
        rem_btn.clicked.connect(self.remove_selected)
        btn_row.addWidget(rem_btn)

        clear_btn = QtWidgets.QPushButton("Liste leeren")
        clear_btn.clicked.connect(self.clear_list)
        btn_row.addWidget(clear_btn)
        btn_row.addStretch(1)

        right = QtWidgets.QWidget()
        right_layout = QtWidgets.QFormLayout(right)
        top_split.addWidget(right)
        top_split.setStretchFactor(0, 3)
        top_split.setStretchFactor(1, 2)

        self.subdir_edit = QtWidgets.QLineEdit("png")
        right_layout.addRow("Ziel-Unterordner:", self.subdir_edit)

        self.overwrite_chk = QtWidgets.QCheckBox("Bestehende Dateien überschreiben")
        self.overwrite_chk.setChecked(True)
        right_layout.addRow("", self.overwrite_chk)

        # Export button
        export_btn = QtWidgets.QPushButton("Export starten")
        export_btn.clicked.connect(self.export)
        layout.addWidget(export_btn, 0)

        # Log area
        self.log = QtWidgets.QPlainTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log, 1)

        # Menu actions (optional)
        file_menu = self.menuBar().addMenu("Datei")
        act_add = QtGui.QAction("Dateien hinzufügen", self)
        act_add.triggered.connect(self.add_files_dialog)
        file_menu.addAction(act_add)

        act_export = QtGui.QAction("Export starten", self)
        act_export.triggered.connect(self.export)
        file_menu.addAction(act_export)

        act_quit = QtGui.QAction("Beenden", self)
        act_quit.triggered.connect(self.close)
        file_menu.addAction(act_quit)

    # ---------- helpers ----------
    def log_msg(self, msg: str):
        self.log.appendPlainText(msg)
        self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())

    def add_files_dialog(self):
        dlg = QtWidgets.QFileDialog(self, "LightBurn-Dateien wählen")
        dlg.setFileMode(QtWidgets.QFileDialog.ExistingFiles)
        dlg.setNameFilters(["LightBurn (*.lbrn *.lbrn2)", "Alle Dateien (*.*)"])
        if dlg.exec():
            for path in dlg.selectedFiles():
                self.list_widget._add_path(Path(path))

    def remove_selected(self):
        for item in self.list_widget.selectedItems():
            row = self.list_widget.row(item)
            self.list_widget.takeItem(row)

    def clear_list(self):
        self.list_widget.clear()

    # ---------- export ----------
    def export(self):
        count = self.list_widget.count()
        if count == 0:
            QtWidgets.QMessageBox.information(self, "Hinweis", "Bitte zuerst Dateien hinzufügen.")
            return

        subdir_name = self.subdir_edit.text().strip() or "png"
        overwrite = self.overwrite_chk.isChecked()

        paths: List[Path] = [Path(self.list_widget.item(i).text()) for i in range(count)]

        total = len(paths)
        ok = 0
        for i, in_path in enumerate(paths, start=1):
            try:
                self.log_msg(f"[{i}/{total}] Verarbeite: {in_path}")
                out_dir = in_path.parent / subdir_name
                out_dir.mkdir(parents=True, exist_ok=True)
                out_path = out_dir / (in_path.stem + ".png")

                if out_path.exists() and not overwrite:
                    self.log_msg(f"  – Übersprungen (existiert bereits): {out_path}")
                    continue

                svg_text, has_elems, thumb_b64 = build_svg(in_path, out_dir)
                if has_elems:
                    try:
                        write_png(svg_text, out_path, out_dir)
                        ok += 1
                    except SystemExit as se:
                        self.log_msg("  ! Fehler beim PNG-Export (cairosvg installiert?): " + str(se))
                    except Exception as e:
                        self.log_msg("  ! Fehler beim PNG-Export: " + str(e))
                elif thumb_b64:
                    try:
                        raw = base64.b64decode(''.join(thumb_b64.split()))
                        out_path.write_bytes(raw)
                        self.log_msg(f"  – PNG exportiert (Thumbnail): {out_path}")
                        ok += 1
                    except Exception as e:
                        self.log_msg("  ! Konnte Thumbnail nicht schreiben: " + str(e))
                else:
                    self.log_msg("  ! Keine erkennbaren Vektorelemente und kein Thumbnail gefunden.")
            except Exception as e:
                self.log_msg(f"  ! Unerwarteter Fehler: {e}")

        self.log_msg(f"Fertig. Erfolgreich: {ok}/{total}")


def main():
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
