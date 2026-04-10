import sympy as sp
import numpy as np


class SymbolicMatrix:

    def __init__(self, matrix_strings):
        """
        matrix_strings: lista de listas contendo strings
        """
        self.matrix_strings = matrix_strings
        self.symbolic_matrix = None
        self.parameters = set()

        self._parse()

    def _parse(self):
        rows = []

        for row in self.matrix_strings:
            symbolic_row = []
            for item in row:
                expr = sp.sympify(item)
                self.parameters.update(expr.free_symbols)
                symbolic_row.append(expr)
            rows.append(symbolic_row)

        self.symbolic_matrix = rows

    def get_parameters(self):
        return sorted([str(p) for p in self.parameters])

    def evaluate(self, param_values):
        numeric_matrix = []

        for row in self.symbolic_matrix:
            numeric_row = []
            for expr in row:
                value = expr.subs(param_values)
                numeric_row.append(float(value))
            numeric_matrix.append(numeric_row)

        return np.array(numeric_matrix, dtype=float)
