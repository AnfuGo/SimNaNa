# config.py
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit,
    QSplitter, QTabWidget, QFormLayout,
    QTextEdit, QMessageBox,
    QSpinBox, QTableWidget,
    QHeaderView, QSizePolicy,
    QComboBox, QDoubleSpinBox,
    QFileDialog, QHBoxLayout
)
class PlotConfig:
    def __init__(self):
        self.output_names = {}
        self.line_color = "blue"
        self.line_width = 1.5
        self.figure_width = 8
        self.figure_height = 5

    def set_output_name(self, index, name):
        self.output_names[index] = name

    def get_output_name(self, index):
        return self.output_names.get(index, None)

    def configs_edit(self):
        self.layout_config.addWidget(QLabel("Cor da linha:"))

        self.color_selector = QComboBox()
        self.color_selector.addItems(["blue", "red", "green", "black"])
        self.color_selector.currentTextChanged.connect(
            lambda text: setattr(self.plot_config, "line_color", text)
        )
        self.layout_config.addWidget(self.color_selector)

        self.layout_config.addWidget(QLabel("Espessura da linha:"))

        self.linewidth_spin = QDoubleSpinBox()
        self.linewidth_spin.setRange(0.5, 5)
        self.linewidth_spin.setValue(1.5)
        self.linewidth_spin.valueChanged.connect(
            lambda val: setattr(self.plot_config, "line_width", val)
        )
        self.layout_config.addWidget(self.linewidth_spin)
