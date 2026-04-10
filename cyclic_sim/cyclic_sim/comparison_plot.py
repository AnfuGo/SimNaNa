# comparison_plot.py
import numpy as np
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
def load_txt_file(filepath):

    # Lê header
    with open(filepath, 'r') as f:
        header = f.readline().strip()

    column_names = header.split()

    # Lê dados numéricos
    data = np.loadtxt(filepath, skiprows=1)

    time = data[:, 0]

    signals = {}

    for i, name in enumerate(column_names[1:], start=1):
        signals[name] = data[:, i]

    return time, signals


class comparison_functions:
    def load_comparison_file(self):

            try:
                t_ext, signals_ext = load_txt_file(
                    self.file_path_input.text()
                )

                self.psim_time = t_ext
                self.psim_signals = signals_ext

                self.compare_selector.clear()

            # Verifica interseção entre nomes
                if self.results is None:
                    results = self.n_outputs_spin.value()
                else: 
                    results = self.results.shape[0]
                for i in range(results):

                    nome_saida = self.plot_config.get_output_name(i)

                    if nome_saida in self.psim_signals:
                        self.compare_selector.addItem(nome_saida)

                if self.compare_selector.count() == 0:
                    QMessageBox.warning(
                        self,
                        "Aviso",
                        "Nenhuma variável do arquivo corresponde aos nomes configurados."
                    )

            except Exception as e:
                QMessageBox.critical(self, "Erro ao carregar arquivo", str(e))

    def plot_comparison(self):

            nome = self.compare_selector.currentText()

            if nome not in self.psim_signals:
                QMessageBox.critical(self, "Erro",
                    "Variável não encontrada no arquivo.")
                return

        # descobrir índice interno correspondente
            indice_modelo = None

            for i in range(self.results.shape[0]):
                if self.plot_config.get_output_name(i) == nome:
                    indice_modelo = i
                    break

            if indice_modelo is None:
                QMessageBox.critical(self, "Erro",
                    "Variável não encontrada no modelo.")
                return

            self.figure.clear()
            ax = self.figure.add_subplot(111)

    # --- Modelo ---
            ax.plot(
                self.t,
                self.results[indice_modelo, :],
                label=f"{nome} Modelo",
                linewidth=self.plot_config.line_width,
                color=self.plot_config.line_color
            )

    # --- PSIM ---
            ax.plot(
                self.psim_time,
                self.psim_signals[nome],
                '--',
                label=f"{nome} PSIM",
                linewidth=2
            )

            ax.set_xlabel("Tempo (s)")
            ax.set_title(f"Comparativo {nome} - Modelo vs PSIM")
            ax.grid(True)
            ax.legend()

            self.canvas.draw()

    def open_file_dialog(self):

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar arquivo TXT",
            "",
            "Arquivos TXT (*.txt);;Todos os arquivos (*)"
        )

        if file_path:
            self.file_path_input.setText(file_path)
