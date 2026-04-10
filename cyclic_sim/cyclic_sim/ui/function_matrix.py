import numpy as np
import sympy as sp
import re
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit,
    QSplitter, QTabWidget, QFormLayout,
    QTextEdit, QMessageBox,
    QSpinBox, QTableWidgetItem,
    QHeaderView, QSizePolicy,
    QComboBox, QDoubleSpinBox
)
class MatrixController:

    def on_matrix_changed(self):

        self.load_current_matrix()

    def load_current_matrix(self):

        stage_idx = self.stage_selector.currentIndex()
        matrix_name = self.matrix_selector.currentText()

        matrix = self.stages_data[stage_idx][matrix_name]
        rows = len(matrix)
        cols = len(matrix[0])
        #rows = matrix.shape[0]
        #cols = matrix.shape[1]

        self.matrix_table.blockSignals(True)

        self.matrix_table.setRowCount(rows)
        self.matrix_table.setColumnCount(cols)

        for i in range(rows):
            for j in range(cols):
                value = matrix[i][j]
                self.matrix_table.setItem(
                    i, j,
                    QTableWidgetItem(str(value))
                )

        self.matrix_table.blockSignals(False)

    def initialize_stages(self):
        self.update_stage_list()
    def update_stage_list(self):

        count = self.stage_count_spin.value()

        n = self.n_states_spin.value()
        m = self.n_inputs_spin.value()
        p = self.n_outputs_spin.value()

    # Se ainda não existir, cria estrutura
        if not hasattr(self, "stages_data"):
            self.stages_data = {}

        # Remove etapas excedentes
        keys_to_remove = [k for k in self.stages_data.keys() if k >= count]
        for k in keys_to_remove:
            del self.stages_data[k]

     # Cria novas etapas se necessário
        for i in range(count):
            if i not in self.stages_data:
                self.stages_data[i] = {
                    "A": np.zeros((n, n), dtype=object),
                    "B": np.zeros((n, m), dtype=object),
                    "C": np.zeros((p, n), dtype=object),
                    "D": np.zeros((p, m), dtype=object),
                    "duty": 0.5
                }

    # Atualiza combo
        self.stage_selector.blockSignals(True)
        self.stage_selector.clear()

        for i in range(count):
            self.stage_selector.addItem(f"Etapa {i+1}")

        self.stage_selector.blockSignals(False)

    # Garante índice válido
        if count > 0:
            self.stage_selector.setCurrentIndex(0)
            self.load_stage_data()


    def update_duty_cycle(self):
        stage_index = self.stage_selector.currentIndex()
        self.stages_data[stage_index]["duty"] = self.duty_spin.value()


    def load_stage_data(self):
        self.matrix_table.blockSignals(True)
        stage_index = self.stage_selector.currentIndex()
        matrix_name = self.matrix_selector.currentText()

        matrix_data = self.stages_data[stage_index][matrix_name]
        self.matrix_table.blockSignals(False)
        self.populate_table(matrix_data)

        self.duty_spin.setValue(self.stages_data[stage_index]["duty"])

    def populate_table(self, matrix_data):
        rows = len(matrix_data)
        cols = len(matrix_data[0]) if rows > 0 else 0

        self.matrix_table.blockSignals(True)
        self.matrix_table.setRowCount(rows)
        self.matrix_table.setColumnCount(cols)

        for i in range(rows):
            for j in range(cols):
                self.matrix_table.setItem(
                    i, j,
                    QTableWidgetItem(str(matrix_data[i][j]))
                )

        self.matrix_table.blockSignals(False)


    def resize_matrix(self):
        rows = self.rows_spin.value()
        cols = self.cols_spin.value()

        self.matrix_table.setRowCount(rows)
        self.matrix_table.setColumnCount(cols)

    def update_matrix_size(self):

        n = self.n_states_spin.value()
        m = self.n_inputs_spin.value()
        p = self.n_outputs_spin.value()

    # Atualiza todas as etapas internamente
        for stage_idx in self.stages_data.keys():

            stage = self.stages_data[stage_idx]

            stage["A"] = self._resize_matrix(stage["A"], n, n)
            stage["B"] = self._resize_matrix(stage["B"], n, m)
            stage["C"] = self._resize_matrix(stage["C"], p, n)
            stage["D"] = self._resize_matrix(stage["D"], p, m)

    # Agora força recarregar a matriz atualmente selecionada
        self.load_current_matrix()


    def matrix_changed(self):

        stage_idx = self.stage_selector.currentIndex()
        matrix_name = self.matrix_selector.currentText()

        rows = self.matrix_table.rowCount()
        cols = self.matrix_table.columnCount()

        new_matrix = np.zeros((rows, cols), dtype=object)

        for i in range(rows):
            for j in range(cols):
                item = self.matrix_table.item(i, j)
                new_matrix[i][j] = item.text() if item else "0"

        self.stages_data[stage_idx][matrix_name] = new_matrix

        # -------------------------------------------------
        # Detecta parâmetros atuais nas matrizes
        # -------------------------------------------------

        parameters_detected = set()

        for stage in self.stages_data.values():
            for mat_name in ["A", "B", "C", "D"]:
                matrix = stage[mat_name]

                for i in range(len(matrix)):
                    for j in range(len(matrix[0])):

                        text = str(matrix[i][j]).strip()
                        if not text:
                            continue

                        try:
                            expr = sp.sympify(text)
                            for s in expr.free_symbols:
                                parameters_detected.add(str(s))
                        except Exception:
                            pass

        # -------------------------------------------------
        # Sincronização
        # -------------------------------------------------

        if not hasattr(self, "parameters"):
            self.parameters = {}

        if not hasattr(self, "param_inputs"):
            self.param_inputs = {}

        current_params = set(self.parameters.keys())

        # 🔹 Parâmetros removidos
        removed = current_params - parameters_detected

        # 🔹 Parâmetros novos
        added = parameters_detected - current_params

        # -------------------------------------------------
        # Remove apenas os que sumiram
        # -------------------------------------------------

        for name in removed:
            self.parameters.pop(name, None)

            line = self.param_inputs.pop(name, None)
            if line:
                self.param_layout.removeWidget(line)
                line.deleteLater()

        # -------------------------------------------------
        # Adiciona apenas os novos
        # -------------------------------------------------

        for name in sorted(added):
            self.parameters[name] = 1.0

            line = QLineEdit()
            line.setText("1.0")

            line.editingFinished.connect(
                lambda n=name, l=line:
                    self._update_param_value(n, l)
            )

            self.param_layout.addRow(name, line)
            self.param_inputs[name] = line
        

    def evaluate_matrix(self, matrix_data, param_values):

        rows = len(matrix_data)
        cols = len(matrix_data[0])

        numeric_matrix = np.zeros((rows, cols), dtype=float)

        for i in range(rows):
            for j in range(cols):

                text = matrix_data[i][j]

                if text == "" or text is None:
                    numeric_matrix[i, j] = 0
                    continue

                try:
                    expr = sp.sympify(text)

                    if expr.free_symbols:
                        expr = expr.subs(param_values)

                    numeric_matrix[i, j] = float(expr)

                except Exception as e:
                    raise ValueError(f"Erro na célula ({i},{j}): {text}")

        return numeric_matrix

    def _resize_matrix(self, old_matrix, new_rows, new_cols):

        new_matrix = np.zeros((new_rows, new_cols), dtype=object)

        old_rows = len(old_matrix)
        old_cols = len(old_matrix[0])

        min_rows = min(old_rows, new_rows)
        min_cols = min(old_cols, new_cols)

        for i in range(min_rows):
            for j in range(min_cols):
                new_matrix[i][j] = old_matrix[i][j]

        return new_matrix





def parse_si_value(text):
    """
    Converte strings como:
    47u → 47e-6
    10k → 10e3
    2.2m → 2.2e-3
    """

    prefix_map = {
        'p': 1e-12,
        'n': 1e-9,
        'u': 1e-6,
        'm': 1e-3,
        'c': 1e-2,
        'd': 1e-1,
        '': 1.0,
        'k': 1e3,
        'M': 1e6,
        'G': 1e9
    }

    text = text.strip()

    match = re.fullmatch(r'([-+]?\d*\.?\d+)([pnumcdkMG]?)', text)

    if not match:
        raise ValueError(f"Valor inválido: {text}")

    value, prefix = match.groups()

    factor = prefix_map.get(prefix)
    if factor is None:
        raise ValueError(f"Prefixo SI inválido: {prefix}")

    return float(value) * factor
