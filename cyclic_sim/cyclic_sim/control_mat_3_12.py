import control as ct
import matlab.engine
import matlab
import numpy as np
from scipy.signal import place_poles

def run_controller_design(sys_tf, ctrl_type="PI", method="pidtune", wc=None, polos_desejados=None, Main_Window=None):
    """
    Envia TF(s) para função MATLAB tuneControllers
    Aceita:
        - TransferFunction
        - StateSpace
        - Lista de sistemas
    """
    # ============================
    # Controle por retroação de estados
    # ============================
    if ctrl_type == "Retroativo":
        #result = simulator.generate_amp_matrix()
        #if result is None:
            #raise ValueError ("O sistema aumentado não é controlável")
        #Main_Window.A_aug, Main_Window.B_aug = result
        if method == "acker":
            #print(Main_Window.Ap)
            print(Main_Window.Bp)
            print(f"Bp[0]: {Main_Window.Bp}")
            Bp = Main_Window.Bp[:,1]
            print(f"Bp[1]: {Bp}")
            Bp = Main_Window.Bp[:,1:2]
            print(f"Bp[2]: {Bp}")
            #print(type(polos_desejados))
            #print(polos_desejados)
            #K = ct.acker(Main_Window.A_aug, Main_Window.B_aug, polos_desejados)
            if (len(polos_desejados)) == Main_Window.Ap.shape[0]:
                print("SEM INTEGRADOR")
                Main_Window.integrator = 0
                K = ct.acker(Main_Window.Ap, Bp, polos_desejados)
            else:
                print("COM INTEGRADOR")
                Main_Window.integrator = 1
                K = ct.acker(Main_Window.A_aug, Main_Window.B_aug, polos_desejados)
        elif method == "place":
            K = ct.place(Main_Window.A_aug, Main_Window.B_aug, polos_desejados)
            Main_Window.poles = np.linalg.eigvals(Main_Window.A_aug - Main_Window.B_aug @ K)
            #result_max = place_poles(A, B, polos_desejados)
            #K = result_max.gain_matrix
        else:
             raise ValueError("Método de controle inválido")
        return K
                

    # ============================
    # Normalização de entrada
    # ============================
    if not isinstance(sys_tf, list):
        sys_tf = [sys_tf]

    sys_tf = [
        ct.ss2tf(sys) if isinstance(sys, ct.StateSpace) else sys
        for sys in sys_tf
    ]

    # ============================
    # Frequência
    # ============================

    if wc is None:
        wc = [0, 0]

    wmin, wmax = wc

    # ============================
    # Extrai numeradores e denominadores
    # ============================

    num_all = []
    den_all = []

    for system in sys_tf:

        for i in range(system.noutputs):
            for j in range(system.ninputs):

                tf_ij = system[i, j]

                num = np.array(tf_ij.num[0][0], dtype=float)
                den = np.array(tf_ij.den[0][0], dtype=float)

                num_all.append(matlab.double(num.tolist()))
                den_all.append(matlab.double(den.tolist()))

    # ============================
    # Inicia MATLAB
    # ============================

    eng = matlab.engine.start_matlab()

    try:
        result = eng.tuneControllers(
            num_all,
            den_all,
            ctrl_type,
            method.lower(),
            float(wmin),
            float(wmax),
            nargout=1
        )
    except Exception as e:
        print("Erro MATLAB:")
        print(e)
        raise
    finally:
        eng.quit()
    # ============================
    # Converte saída MATLAB → Python
    # ============================

    gains = []

    for r in result:  # cada elemento é um struct MATLAB

        gains.append({
            "Kp": float(r["Kp"]),
            "Ki": float(r["Ki"]),
            "Kd": float(r["Kd"]),
            "Ti": float(r["Ti"]),
            "Td": float(r["Td"]),
        })

    return gains

def convergency_results(K, A, B, C, D, input_, r, time, integrator):

    pts_resolution = 5000
    t = 0
    step = time/pts_resolution
    
    x = np.zeros((A.shape[0],1))

    K = np.atleast_2d(K)
    input_ = np.atleast_2d(input_).reshape(-1,1)

    if K.shape[0] != 1:
        K = K.T
    
    X = []
    T = []
    Y = []
    E = []
    XI = []

    print("A shape:", A.shape)
    print("B shape:", B.shape)
    print("K shape:", K.shape)

    print(f"Matriz D: {D}")
    print(f"input_: {input_}")

    eigvals = np.linalg.eig(A - B @ K)[0]

    Br = np.zeros((x.shape[0], 1))
    Br[-1, 0] = r
    print(f"Matriz Br: {Br}")

    if np.all(np.real(eigvals) < 0):
        print("Sistema estável")
    else:
        print("Sistema instável")
        
    def f(x_T):
        if integrator == 1:
            u_e = - K @ x_T
            return A @ x_T + B @ u_e + Br
        else:
            u = r - K @ x_T
            return A @ x_T + B @ u 
            

    while t < time:

        # ===============================
        # MÉTODO ANTIGO (Euler)
        # ===============================
        # u = r - K@x
        # x = x + step*(A - B@K)@x
        # ou
        # x = x + step*(A@x + B*u)

        # ===============================
        # NOVO MÉTODO (Runge-Kutta 4)
        # ===============================

        k1 = f(x)
        k2 = f(x + 0.5*step*k1)
        k3 = f(x + 0.5*step*k2)
        k4 = f(x + step*k3)

        x = x + (step/6)*(k1 + 2*k2 + 2*k3 + k4)
        u = - K @ x
        if integrator == 1:
            y = C @ x[:-1] + D @ u #tira o integrador (ultimo estado)
            XI.append(x[-1].item())
        else:
            y = C @ x + D @ u #sem integrador

        e = r - y
        
        X.append(x.copy())
        Y.append(y.copy()) 
        T.append(t)
        E.append(e.copy())
        t += step

    return np.array(T), np.hstack(X), np.atleast_2d(np.hstack(E)), np.array(XI), np.atleast_2d(np.hstack(Y))
