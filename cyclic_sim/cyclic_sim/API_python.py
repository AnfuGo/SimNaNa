import numpy as np
from scipy import signal
from scipy.integrate import solve_ivp
import control as ct


class CyclicStateSpaceSimulator:

    def __init__(self, system_config):

        self.config = system_config

        ok, msg = self.config.validate()
        if not ok:
            raise ValueError(msg)

        self.stages = self.config.stages
        self.duty_cycles = np.array(self.config.duty_cycles, dtype=float)
        self.fs = self.config.switching_frequency
        self.Ts = 1.0 / self.fs
        self.state_limits = self.config.state_limits

        if not self._validate_dimensions():
            raise ValueError("Dimensões incompatíveis entre estágios.")

    def _validate_dimensions(self):
        """
        Garante que todos os estágios tenham mesma dimensão de estado.
        """
        n_states = self.stages[0].A.shape[0]

        for stage in self.stages:
            if stage.A.shape[0] != n_states:
                raise ValueError("Todos os estágios devem ter o mesmo número de estados.")
                return False
        return True

    def simulate(self,
                 x0,
                 t_final,
                 input_function,
                 resolution=50):

        x_current = np.array(x0, dtype=float)
        total_cycles = int(t_final * self.fs)

        t_total = None
        y_total = None

        global_time = 0.0

        for _ in range(total_cycles):

            for duty, stage in zip(self.duty_cycles, self.stages):

                duration = duty * self.Ts

                system = signal.StateSpace(
                    stage.A,
                    stage.B,
                    stage.C,
                    stage.D
                )

                t_local = np.linspace(0, duration, resolution, endpoint=False)

                # gerar entrada
                if callable(input_function):
                    u_local = np.array(
                        [input_function(global_time + t)
                         for t in t_local]
                    )
                else:
                    u_local = np.ones_like(t_local) * input_function

                tout, yout, xout = signal.lsim(
                    system,
                    U=u_local,
                    T=t_local,
                    X0=x_current
                )

                if yout.ndim == 1:
                    yout = yout.reshape(-1, 1)

                # aplicar limites de estado
                if self.state_limits is not None:
                    for i, (xmin, xmax) in enumerate(self.state_limits):
                        xout[:, i] = np.clip(xout[:, i], xmin, xmax)

                tout_global = tout + global_time

                if t_total is None:
                    t_total = tout_global
                    y_total = yout
                else:
                    t_total = np.concatenate((t_total, tout_global))
                    y_total = np.vstack((y_total, yout))

                x_current = xout[-1]
                global_time += duration

        return t_total, y_total.T, x_current
    
    def u_p_func(self, t, perturb_values, t_start_vec, t_end_vec):

        perturb_values = np.asarray(perturb_values)
        t_start_vec = np.asarray(t_start_vec)
        t_end_vec = np.asarray(t_end_vec)

        if not (len(perturb_values) == len(t_start_vec) == len(t_end_vec)):
            raise ValueError("Os vetores de perturbação devem ter o mesmo tamanho.")

        u = np.zeros(len(perturb_values))

        for i in range(len(perturb_values)):
            if t_start_vec[i] <= t <= t_end_vec[i]:
                u[i] = perturb_values[i]

        return u

    def find_small_signal_matrix(self,
                             input_function,
                             x0,
                             perturb_values,
                             t_start_vec,
                             t_end_vec,
                             t_final,
                             resolution):

        self.resolution = resolution
        x = np.array(x0, dtype=float)
        n = self.stages[0].A.shape[0]
        x2 = np.zeros(n)
        A, B, C, D, aux1, aux2, aux3, aux4 = self.calcular_matrizes_derivadas()
        # Ponto de operação
        U = np.atleast_2d(input_function).reshape(-1,1)
        X = -np.linalg.pinv(A) @ B @ U
        #Y = C @ X + D * input_function
        Ap = A
        Bp = np.hstack([B, aux1 @ X + aux2 @ U])
        Cp = C
        Ep = np.hstack([D, aux3 @ X + aux4 @ U])
        def u_func(t):
            return self.u_p_func(t, perturb_values, t_start_vec, t_end_vec)

        t, estados_pert = self.simular_pequenos_sinais(Ap, Bp, Cp, Ep, x2, t_final, u_func)
        t2, x_base, y_base = self.simular_cc(A, B, C, D, x, t_final, input_function)
        assert np.allclose(t, t2)
        y = y_base + estados_pert
        return t, y

    def simular_pequenos_sinais(self, Ap, Bp, Cp, Dp, x0_hat, t_final, u_func):

        def dxdt(t, x):
            u_p = np.array(u_func(t)).reshape(-1,1)
            return (Ap @ x.reshape(-1,1) + Bp @ u_p).flatten()

        t_span = (0, t_final)
        t_eval = np.linspace(0, t_final, self.resolution)

        sol = solve_ivp(dxdt, t_span, x0_hat, t_eval=t_eval)

        y_hat = Cp @ sol.y + Dp @ np.array([u_func(t) for t in sol.t]).T

        return sol.t, y_hat

    def calcular_matrizes_derivadas(self):

        n = self.stages[0].A.shape[0]
        m = self.stages[0].B.shape[1]
        p = self.stages[0].C.shape[0]

        Afinal = np.zeros((n, n))
        Bfinal = np.zeros((n, m))
        Cfinal = np.zeros((p, n))
        Dfinal = np.zeros((p, m))

        for duty, stage in zip(self.duty_cycles, self.stages):
            Afinal += duty * stage.A
            Bfinal += duty * stage.B
            Cfinal += duty * stage.C
            Dfinal += duty * stage.D

        # derivadas
        A1 = self.stages[0].A
        B1 = self.stages[0].B
        C1 = self.stages[0].C
        D1 = self.stages[0].D

        Arest = np.zeros_like(A1)
        Brest = np.zeros_like(B1)
        Crest = np.zeros_like(C1)
        Drest = np.zeros_like(D1)
        for i in range(1, len(self.stages)):
            alpha = self.duty_cycles[i] / (1 - self.duty_cycles[0])
            Arest += alpha * self.stages[i].A
            Brest += alpha * self.stages[i].B
            Crest += alpha * self.stages[i].C
            Drest += alpha * self.stages[i].D

        dA_dD = A1 - Arest
        dB_dD = B1 - Brest
        dC_dD = C1 - Crest
        dD_dD = D1 - Drest

        return Afinal, Bfinal, Cfinal, Dfinal, dA_dD, dB_dD, dC_dD, dD_dD

    def simular_cc(self, A, B, C, D, x0, t_final, U):

        U = np.atleast_1d(U)

        def dxdt(t, x):
            return A @ x + B @ U

        t_span = (0, t_final)
        t_eval = np.linspace(0, t_final, self.resolution)

        sol = solve_ivp(dxdt, t_span, x0, t_eval=t_eval)

        y = C @ sol.y + D @ U.reshape(-1,1)

        return sol.t, sol.y, y


# ===========================================================
# --------- Função de Transferência do Modelo Python --------
# ===========================================================
    def generate_tf(self, input_operating_point):

        A, B, C, D, dA, dB, dC, dD = self.calcular_matrizes_derivadas()

        U = np.atleast_2d(input_operating_point).reshape(-1,1)

        # ponto de operação
        X = -np.linalg.pinv(A) @ B @ U
        y = C@X + D@U
        Ap = A
        Bp = np.hstack([B, dA @ X + dB @ U])
        Cp = C
        Dp = np.hstack([D, dC @ X + dD @ U])
    
        sys_ss = ct.ss(Ap, Bp, Cp, Dp)
        sys_tf = ct.ss2tf(sys_ss)

        return sys_ss, sys_tf, y

    def generate_amp_matrix(self, input_operating_point):
        
        
        A, B, C, D, dA, dB, dC, dD = self.calcular_matrizes_derivadas()
        U = np.atleast_2d(input_operating_point).reshape(-1,1)
        X = -np.linalg.pinv(A) @ B @ U
        Ap = A
        Bp = np.hstack([B, dA @ X + dB @ U])
        Bp_d = Bp[:,1:2]
        Cp = C
        Dp = np.hstack([D, dC @ X + dD @ U])

        n = Ap.shape[0]
        
        A_aug = np.block([
            [Ap, np.zeros((n, 1))],
            [-Cp, np.zeros((1, 1))]
        ])
        print(f"Matriz A aumentada: {A_aug}\n")

        B_aug = np.vstack([
            Bp_d,
            np.zeros((1, Bp_d.shape[1]))
        ])
        print(f"Matriz B aumentada: {B_aug}\n")
        if not self.check_controlability(A_aug, B_aug):
            return None
        
        return A_aug, B_aug, Ap, Bp, Cp, Dp

    def check_controlability(self, A, B):

        n = A.shape[0] 
        estados = A.shape[0]  
        print(f"shape da aumentada: {A.shape[0]}")
        

        # Primeira coluna = B
        controllability_matrix = B

        # Construção: [B AB A^2B ...]
        for i in range(1, n):
            controllability_matrix = np.hstack(
                (controllability_matrix, np.linalg.matrix_power(A, i) @ B)
            )
            print(f"Interação: {i}")

        rank = np.linalg.matrix_rank(controllability_matrix)
        
        print(f"O rank: {rank}")

        return rank == estados
