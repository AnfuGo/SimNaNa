from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QFileDialog,
    QMessageBox, QApplication
)
from PyQt6.QtGui import QImage
from PyQt6.QtWidgets import QTabWidget, QFormLayout

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_agg import FigureCanvasAgg
import matplotlib.pyplot as plt
from matplotlib import rcParams, font_manager
import io


class PlotEditorWindow(QMainWindow):
    def __init__(self, figure):
        super().__init__()
        self.setWindowTitle("Editor de Gráfico")
        self.setMinimumSize(1100, 750)
        font_manager.fontManager.ttflist
        fonts = sorted({f.name for f in font_manager.fontManager.ttflist})
        print(fonts)
        rcParams["font.family"] = "CMU Serif"
        rcParams["font.size"] = 12
        plt.rcParams["mathtext.fontset"] = "custom"
        plt.rcParams["mathtext.rm"] = "CMU Serif"
        plt.rcParams["mathtext.it"] = "CMU Serif:italic"
        plt.rcParams["mathtext.bf"] = "CMU Serif:bold"

        self.setWindowTitle("Editor de Gráfico")
        self.setMinimumSize(1100, 750)

        self.figure = figure
        self.canvas = FigureCanvas(self.figure)

        # ===== Central =====
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        # ===== Painel lateral com abas =====
        tabs = QTabWidget()

        # =========================
        # ABA 1 — EIXOS
        # =========================
        tab_axes = QWidget()
        axes_layout = QFormLayout()
        tab_axes.setLayout(axes_layout)

        self.title_edit = QLineEdit()
        axes_layout.addRow("Título:", self.title_edit)

        self.xlabel_edit = QLineEdit()
        axes_layout.addRow("Nome eixo X:", self.xlabel_edit)

        self.ylabel_edit = QLineEdit()
        axes_layout.addRow("Nome eixo Y:", self.ylabel_edit)

        self.xmin_edit = QLineEdit()
        axes_layout.addRow("Xmin:", self.xmin_edit)

        self.xmax_edit = QLineEdit()
        axes_layout.addRow("Xmax:", self.xmax_edit)

        self.ymin_edit = QLineEdit()
        axes_layout.addRow("Ymin:", self.ymin_edit)

        self.ymax_edit = QLineEdit()
        axes_layout.addRow("Ymax:", self.ymax_edit)

        tabs.addTab(tab_axes, "Eixos & Limites")

        # =========================
        # ABA 2 — CURVAS
        # =========================
        tab_style = QWidget()
        style_layout = QFormLayout()
        tab_style.setLayout(style_layout)

        self.outputs_edit = QLineEdit()
        style_layout.addRow("Nomes das curvas:", self.outputs_edit)

        self.colors_edit = QLineEdit()
        style_layout.addRow("Cores:", self.colors_edit)

        self.width_edit = QLineEdit()
        style_layout.addRow("Espessura:", self.width_edit)

        self.style_edit = QLineEdit()
        style_layout.addRow("Estilo (-, --, :):", self.style_edit)

        self.title_fontsize = QLineEdit()
        style_layout.addRow("Fonte título:", self.title_fontsize)

        self.axis_fontsize = QLineEdit()
        style_layout.addRow("Fonte eixos:", self.axis_fontsize)

        self.legend_fontsize = QLineEdit()
        style_layout.addRow("Fonte legenda:", self.legend_fontsize)

        tabs.addTab(tab_style, "Curvas & Estilo")

        control_layout = QVBoxLayout()
        control_layout.addWidget(tabs)

        update_btn = QPushButton("Aplicar Alterações")
        update_btn.clicked.connect(self.apply_changes)
        control_layout.addWidget(update_btn)

        log_btn = QPushButton("Alternar Log X")
        log_btn.clicked.connect(self.toggle_log_x)
        control_layout.addWidget(log_btn)

        save_btn = QPushButton("Salvar Figura")
        save_btn.clicked.connect(self.save_figure)
        control_layout.addWidget(save_btn)

        copy_btn = QPushButton("Copiar para Clipboard")
        copy_btn.clicked.connect(self.copy_to_clipboard)
        control_layout.addWidget(copy_btn)

        control_layout.addStretch()

        main_layout.addLayout(control_layout, 1)
        main_layout.addWidget(self.canvas, 4)

        self.populate_current_values()

    # ==============================
    # Preenche campos com valores atuais
    # ==============================
    def populate_current_values(self):
        if self.figure.axes:
            ax = self.figure.axes[0]

            self.title_edit.setText(ax.get_title())
            self.xlabel_edit.setText(ax.get_xlabel())
            self.ylabel_edit.setText(ax.get_ylabel())

            xmin, xmax = ax.get_xlim()
            ymin, ymax = ax.get_ylim()

            self.xmin_edit.setText(str(xmin))
            self.xmax_edit.setText(str(xmax))
            self.ymin_edit.setText(str(ymin))
            self.ymax_edit.setText(str(ymax))

            # nomes atuais das curvas
            labels = [line.get_label() for line in ax.get_lines()]
            self.outputs_edit.setText(",".join(labels))
            # Pegar propriedades da primeira linha
            lines = ax.get_lines()
            if lines:
                line = lines[0]
                self.width_edit.setText(str(line.get_linewidth()))
                self.style_edit.setText(line.get_linestyle())

                colors = [l.get_color() for l in lines]
                self.colors_edit.setText(",".join(colors))

            # Fontes
            self.title_fontsize.setText(str(ax.title.get_fontsize()))
            self.axis_fontsize.setText(str(ax.xaxis.label.get_fontsize()))

    # ==============================
    # Aplicar mudanças
    # ==============================
    def apply_changes(self):
        try:
            for ax in self.figure.axes:

                # Título e eixos
                ax.set_title(
                    self.title_edit.text(),
                    fontsize=float(self.title_fontsize.text() or 12)
                )

                ax.set_xlabel(
                    self.xlabel_edit.text(),
                    fontsize=float(self.axis_fontsize.text() or 10)
                )

                ax.set_ylabel(
                    self.ylabel_edit.text(),
                    fontsize=float(self.axis_fontsize.text() or 10)
                )

                xmin = float(self.xmin_edit.text())
                xmax = float(self.xmax_edit.text())
                ymin = float(self.ymin_edit.text())
                ymax = float(self.ymax_edit.text())

                ax.set_xlim(xmin, xmax)
                ax.set_ylim(ymin, ymax)

                # Atualizar curvas
                new_labels = [s.strip() for s in self.outputs_edit.text().split(",")]
                new_colors = [s.strip() for s in self.colors_edit.text().split(",")]

                linewidth = float(self.width_edit.text() or 1.5)
                linestyle = self.style_edit.text() or "-"

                lines = ax.get_lines()

                for i, line in enumerate(lines):

                    if i < len(new_labels):
                        line.set_label(new_labels[i])

                    if i < len(new_colors):
                        line.set_color(new_colors[i])

                    line.set_linewidth(linewidth)
                    line.set_linestyle(linestyle)

                legend_font = float(self.legend_fontsize.text() or 10)
                ax.legend(fontsize=legend_font)

            self.canvas.draw()

        except Exception as e:
            QMessageBox.warning(self, "Erro", str(e))

    # ==============================
    # Alternar escala log X
    # ==============================
    def toggle_log_x(self):
        for ax in self.figure.axes:
            current = ax.get_xscale()
            if current == "linear":
                ax.set_xscale("log")
            else:
                ax.set_xscale("linear")

        self.canvas.draw()

    # ==============================
    # Salvar figura
    # ==============================
    def save_figure(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Figura",
            "",
            "PNG (*.png);;PDF (*.pdf);;SVG (*.svg)"
        )

        if file_path:
            self.figure.savefig(file_path, dpi=300)

    # ==============================
    # Copiar para clipboard
    # ==============================
    def copy_to_clipboard(self):

        buffer = io.BytesIO()
        canvas = FigureCanvasAgg(self.figure)
        canvas.draw()
        canvas.print_png(buffer)

        image = QImage.fromData(buffer.getvalue())
        clipboard = QApplication.clipboard()
        clipboard.setImage(image)

        QMessageBox.information(self, "Copiado", "Figura copiada para a área de transferência.")
