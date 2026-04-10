import numpy as np
from models import Stage, CyclicSystemConfig, SimulationConfig
from simulator import CyclicStateSpaceSimulator

# Criar matrizes exemplo
A1 = np.eye(4)
B1 = np.zeros((4,1))
C1 = np.eye(4)
D1 = np.zeros((4,1))

A2 = A1.copy()
B2 = B1.copy()
C2 = C1.copy()
D2 = D1.copy()

A3 = A1.copy()
B3 = B1.copy()
C3 = C1.copy()
D3 = D1.copy()

stage1 = Stage(A1, B1, C1, D1)
stage2 = Stage(A2, B2, C2, D2)
stage3 = Stage(A3, B3, C3, D3)

system_config = CyclicSystemConfig(
    stages=[stage1, stage2, stage3],
    duty_cycles=[0.5, 0.25, 0.25],
    switching_frequency=100000,
    state_limits=[
        (-np.inf, np.inf),
        (-np.inf, np.inf),
        (0, np.inf),
        (-np.inf, np.inf)
    ]
)

sim_config = SimulationConfig(
    x0=[0,0,0,0],
    t_final=0.050,
    input_function=48,
    resolution=50
)

simulator = CyclicStateSpaceSimulator(system_config)

t, y, xf = simulator.simulate(sim_config)

print("Estado final:", xf)
