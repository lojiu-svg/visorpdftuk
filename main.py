import sys
from pathlib import Path
import shutil

import fitz
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtPrintSupport import QPrinter, QPrintPreviewDialog
from PySide6.QtWidgets import (
    QAction,
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)


class PdfViewerMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("visorpdftuk")
        self.resize(1300, 850)

        self.doc = None
        self.file_path = None
        self.current_page = 0
        self.zoom_factor = 1.6

        self.build_ui()
        self.apply_theme()
        self.update_controls()

    def build_ui(self):
        toolbar = QToolBar("Herramientas")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(18, 18))
        self.addToolBar(toolbar)

        self.action_open = QAction("Abrir", self)
        self.action_open.triggered.connect(self.open_pdf)
        toolbar.addAction(self.action_open)

        self.action_save_copy = QAction("Guardar copia", self)
        self.action_save_copy.triggered.connect(self.save_copy)
        toolbar.addAction(self.action_save_copy)

        self.action_close = QAction("Cerrar", self)
        self.action_close.triggered.connect(self.close_document)
        toolbar.addAction(self.action_close)

        toolbar.addSeparator()

        self.action_prev = QAction("Anterior", self)
        self.action_prev.triggered.connect(self.previous_page)
        toolbar.addAction(self.action_prev)

        self.action_next = QAction("Siguiente", self)
        self.action_next.triggered.connect(self.next_page)
        toolbar.addAction(self.action_next)

        self.action_print = QAction("Imprimir", self)
        self.action_print.triggered.connect(self.print_preview)
        toolbar.addAction(self.action_print)

        toolbar.addSeparator()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar en el documento")
        self.search_input.setMinimumWidth(230)
        self.search_input.returnPressed.connect(self.search_document)
        toolbar.addWidget(self.search_input)

        self.action_search = QAction("Buscar", self)
        self.action_search.triggered.connect(self.search_document)
        toolbar.addAction(self.action_search)

        self.page_input = QLineEdit("1")
        self.page_input.setMaximumWidth(70)
        self.page_input.setAlignment(Qt.AlignCenter)
        self.page_input.returnPressed.connect(self.go_to_page_from_input)
        toolbar.addWidget(self.page_input)

        self.page_separator = QLabel("/")
        self.page_separator.setAlignment(Qt.AlignCenter)
        self.page_separator.setMinimumWidth(20)
        toolbar.addWidget(self.page_separator)

        self.page_total = QLabel("0")
        self.page_total.setMinimumWidth(25)
        self.page_total.setAlignment(Qt.AlignCenter)
        toolbar.addWidget(self.page_total)

        toolbar.addSeparator()

        self.action_zoom_out = QAction("Zoom -", self)
        self.action_zoom_out.triggered.connect(self.zoom_out)
        toolbar.addAction(self.action_zoom_out)

        self.action_zoom_in = QAction("Zoom +", self)
        self.action_zoom_in.triggered.connect(self.zoom_in)
        toolbar.addAction(self.action_zoom_in)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        central = QWidget()
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(10, 10, 10, 10)
        root_layout.setSpacing(10)

        thumbnail_panel = QWidget()
        thumbnail_panel.setMinimumWidth(225)
        thumbnail_panel.setMaximumWidth(225)
        thumbnail_layout = QVBoxLayout(thumbnail_panel)
        thumbnail_layout.setContentsMargins(0, 0, 0, 0)

        thumbnail_title = QLabel("Páginas")
        thumbnail_title.setStyleSheet("font-weight: bold; margin-bottom: 8px;")
        thumbnail_layout.addWidget(thumbnail_title)

        self.thumbnail_scroll = QScrollArea()
        self.thumbnail_scroll.setWidgetResizable(True)
        self.thumbnail_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.thumbnail_container = QWidget()
        self.thumbnail_container_layout = QVBoxLayout(self.thumbnail_container)
        self.thumbnail_container_layout.setContentsMargins(6, 6, 6, 6)
        self.thumbnail_container_layout.setSpacing(8)
        self.thumbnail_container_layout.setAlignment(Qt.AlignTop)

        self.thumbnail_scroll.setWidget(self.thumbnail_container)
        thumbnail_layout.addWidget(self.thumbnail_scroll)

        root_layout.addWidget(thumbnail_panel)

        viewer_widget = QWidget()
        viewer_layout = QVBoxLayout(viewer_widget)
        viewer_layout.setContentsMargins(0, 0, 0, 0)

        self.page_view = QLabel()
        self.page_view.setAlignment(Qt.AlignCenter)
        self.page_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.page_view.setMinimumSize(320, 420)
        self.page_view.setStyleSheet("""
            QLabel {
                background: #f8fafc;
                border: 1px solid #d1d5db;
                border-radius: 12px;
            }
        """)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.page_view)
        viewer_layout.addWidget(self.scroll_area)
        root_layout.addWidget(viewer_widget)

        self.setCentralWidget(central)

    def apply_theme(self):
        self.setStyleSheet("""
            QMainWindow {
                background: #0f172a;
                color: #e2e8f0;
            }

            QWidget {
                background: #111827;
                color: #e2e8f0;
            }

            QToolBar {
                background: #0f172a;
                border: 1px solid #1f2937;
                border-radius: 10px;
                padding: 4px;
            }

            QToolBar QToolButton {
                background: transparent;
                color: #e2e8f0;
                border: 1px solid transparent;
                border-radius: 8px;
                padding: 7px 11px;
                margin: 2px;
            }

            QToolBar QToolButton:hover {
                background: #1f2937;
                border: 1px solid #374151;
            }

            QLineEdit {
                background: #1f2937;
                color: #f8fafc;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 8px 10px;
            }

            QLabel {
                color: #e2e8f0;
            }

            QScrollArea {
                border: 1px solid #1f2937;
                border-radius: 10px;
                background: #0f172a;
            }

            QStatusBar {
                background: #0f172a;
                color: #e2e8f0;
                border-top: 1px solid #1f2937;
            }

            QPushButton {
                background: #1f2937;
                color: #e2e8f0;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 8px 10px;
            }

            QPushButton:hover {
                background: #374151;
            }
        """)

    def update_controls(self):
        has_doc = self.doc is not None

        self.action_save_copy.setEnabled(has_doc)
        self.action_close.setEnabled(has_doc)
        self.action_prev.setEnabled(has_doc and self.current_page > 0)
        self.action_next.setEnabled(has_doc and self.current_page < self.doc.page_count - 1 if has_doc else False)
        self.action_print.setEnabled(has_doc)
        self.action_search.setEnabled(has_doc)
        self.search_input.setEnabled(has_doc)
        self.page_input.setEnabled(has_doc)
        self.action_zoom_in.setEnabled(has_doc)
        self.action_zoom_out.setEnabled(has_doc)

        if not has_doc:
            self.page_input.setText("1")
            self.page_total.setText("0")
            self.page_view.clear()
            self.clear_thumbnails()
            return

        self.page_input.setText(str(self.current_page + 1))
        self.page_total.setText(str(self.doc.page_count))

    def clear_thumbnails(self):
        while self.thumbnail_container_layout.count():
            item = self.thumbnail_container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def get_page_pixmap(self, page, zoom_factor):
        if zoom_factor <= 0:
            zoom_factor = 0.5
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom_factor, zoom_factor), alpha=False)
        image = QImage(
            pix.samples,
            pix.width,
            pix.height,
            pix.stride,
            QImage.Format_RGB888,
        )
        return QPixmap.fromImage(image)

    def render_current_page(self):
        if self.doc is None:
            self.page_view.clear()
            return

        if self.current_page < 0:
            self.current_page = 0
        elif self.current_page >= self.doc.page_count:
            self.current_page = self.doc.page_count - 1

        page = self.doc[self.current_page]
        pixmap = self.get_page_pixmap(page, self.zoom_factor)
        self.page_view.setPixmap(pixmap)
        self.page_view.setFixedSize(pixmap.size())
        self.page_input.setText(str(self.current_page + 1))
        self.page_total.setText(str(self.doc.page_count))
        self.status_bar.showMessage(f"Página {self.current_page + 1} de {self.doc.page_count}")
        self.update_controls()

    def generate_thumbnails(self):
        self.clear_thumbnails()
        if self.doc is None:
            return

        for index in range(self.doc.page_count):
            page = self.doc[index]
            pixmap = self.get_page_pixmap(page, 0.2)

            thumb_label = QLabel()
            thumb_label.setPixmap(pixmap.scaled(180, 220, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            thumb_label.setAlignment(Qt.AlignCenter)
            thumb_label.setStyleSheet("""
                border: 1px solid #374151;
                border-radius: 8px;
                background: #0f172a;
                padding: 4px;
            """)

            button = QPushButton(f"Página {index + 1}")
            button.clicked.connect(lambda checked, page_number=index: self.go_to_page(page_number))
            button.setStyleSheet("padding: 7px;")

            thumb_widget = QWidget()
            thumb_layout = QVBoxLayout(thumb_widget)
            thumb_layout.setContentsMargins(0, 0, 0, 0)
            thumb_layout.addWidget(thumb_label)
            thumb_layout.addWidget(button)

            self.thumbnail_container_layout.addWidget(thumb_widget)

    def open_pdf(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Abrir PDF",
            str(Path.home()),
            "Archivos PDF (*.pdf)"
        )

        if not path:
            return

        try:
            self.doc = fitz.open(path)
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"No se pudo abrir el archivo PDF:\n{exc}")
            self.doc = None
            self.file_path = None
            self.current_page = 0
            self.update_controls()
            return

        self.file_path = path
        self.current_page = 0
        self.generate_thumbnails()
        self.render_current_page()
        self.status_bar.showMessage(f"Documento abierto: {Path(path).name}")

    def close_document(self):
        self.doc = None
        self.file_path = None
        self.current_page = 0
        self.page_view.clear()
        self.clear_thumbnails()
        self.update_controls()
        self.status_bar.showMessage("Documento cerrado")

    def save_copy(self):
        if self.file_path is None:
            QMessageBox.warning(self, "Guardar copia", "Primero abre un documento PDF.")
            return

        default_name = Path(self.file_path).stem + "_copia.pdf"
        destination, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar copia",
            str(Path.home() / default_name),
            "Archivos PDF (*.pdf)"
        )

        if not destination:
            return

        if not destination.lower().endswith(".pdf"):
            destination += ".pdf"

        try:
            shutil.copy2(self.file_path, destination)
            self.status_bar.showMessage(f"Copia guardada: {destination}")
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"No se pudo guardar la copia:\n{exc}")

    def previous_page(self):
        if self.doc is None:
            return
        if self.current_page > 0:
            self.current_page -= 1
            self.render_current_page()

    def next_page(self):
        if self.doc is None:
            return
        if self.current_page < self.doc.page_count - 1:
            self.current_page += 1
            self.render_current_page()

    def go_to_page(self, page_index):
        if self.doc is None:
            return
        if 0 <= page_index < self.doc.page_count:
            self.current_page = page_index
            self.render_current_page()

    def go_to_page_from_input(self):
        if self.doc is None:
            return

        try:
            value = int(self.page_input.text())
        except ValueError:
            self.page_input.setText(str(self.current_page + 1))
            return

        if value < 1:
            value = 1
        elif value > self.doc.page_count:
            value = self.doc.page_count

        self.current_page = value - 1
        self.render_current_page()

    def zoom_in(self):
        if self.doc is None:
            return
        if self.zoom_factor < 3.0:
            self.zoom_factor += 0.2
            self.render_current_page()

    def zoom_out(self):
        if self.doc is None:
            return
        if self.zoom_factor > 0.5:
            self.zoom_factor -= 0.2
            self.render_current_page()

    def search_document(self):
        if self.doc is None:
            return

        query = self.search_input.text().strip()
            
