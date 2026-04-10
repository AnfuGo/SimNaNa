from dataclasses import dataclass
import numpy as np


@dataclass
class Stage:
    """
    Representa um estágio do sistema.
    """
    A: np.ndarray
    B: np.ndarray
    C: np.ndarray
    D: np.ndarray

    def validate(self):
        if self.A.shape[0] != self.A.shape[1]:
            return False, "Matriz A deve ser quadrada."

        n = self.A.shape[0]

        if self.B.shape[0] != n:
            return False, "Dimensão de B incompatível com A."

        if self.C.shape[1] != n:
            return False, "Dimensão de C incompatível com A."

        return True, None


@dataclass
class CyclicSystemConfig:
    """
    Define o sistema com múltiplos estágios cíclicos.
    """
    stages: list
    duty_cycles: list
    switching_frequency: float
    state_limits: list = None  # [(min,max), ...]

    def validate(self):

        if len(self.stages) != len(self.duty_cycles):
            return False, "Número de estágios diferente do número de duty cycles."

        if not np.isclose(sum(self.duty_cycles), 1.0):
            return False, "A soma dos duty cycles deve ser 1."

        for i, stage in enumerate(self.stages):
            ok, msg = stage.validate()
            if not ok:
                return False, f"Erro no estágio {i+1}: {msg}"

        return True, None


@dataclass
class SimulationConfig:
    """
    Define parâmetros da simulação.
    """
    x0: list
    t_final: float
    input_function: object  # função ou valor constante
    resolution: int = 50

    def validate(self):

        if self.t_final <= 0:
            return False, "Tempo final deve ser positivo."

        if self.resolution <= 1:
            return False, "Resolução deve ser maior que 1."

        return True, None
