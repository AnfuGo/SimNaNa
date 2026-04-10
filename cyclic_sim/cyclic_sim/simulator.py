import numpy as np
from scipy import signal


class CyclicStateSpaceSimulator:

    def __init__(self, system_config):
        self.config = system_config
        self.config.validate()

        self.Ts = 1 / self.config.switching_frequency

    def simulate(self, simulation_config):

        simulation_config.validate()

        x_current = np.array(simulation_config.x0, dtype=float)

        total_cycles = int(simulation_config.t_final *
                           self.config.switching_frequency)

        t_total = []
        y_total = []

        global_time = 0.0

        for _ in range(total_cycles):

            for duty, stage in zip(self.config.duty_cycles,
                                   self.config.stages):

                duration = duty * self.Ts

                system = signal.StateSpace(stage.A,
                                           stage.B,
                                           stage.C,
                                           stage.D)

                t_local = np.linspace(0,
                                      duration,
                                      simulation_config.resolution)

                if callable(simulation_config.input_function):
                    u_local = np.array(
                        [simulation_config.input_function(global_time + t)
                         for t in t_local]
                    )
                else:
                    u_local = np.ones_like(t_local) * \
                              simulation_config.input_function

                tout, yout, xout = signal.lsim(
                    system,
                    U=u_local,
                    T=t_local,
                    X0=x_current
                )

                # Aplicar limites de estado
                if self.config.state_limits is not None:
                    for i, (xmin, xmax) in enumerate(self.config.state_limits):
                        xout[:, i] = np.clip(xout[:, i], xmin, xmax)

                tout_global = tout + global_time

                if len(t_total) == 0:
                    t_total = tout_global
                    y_total = yout
                else:
                    t_total = np.concatenate((t_total,
                                              tout_global[1:]))
                    y_total = np.vstack((y_total,
                                         yout[1:]))

                x_current = xout[-1]
                global_time += duration

        return np.array(t_total), np.array(y_total).T, x_current

