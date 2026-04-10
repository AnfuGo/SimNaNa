import subprocess
import control as ct

def run_controller_design(sys_tf, ctrl_type="PI", method="pidtune", wc=None):
    """
    Envia TF(s) para tuneControllers.exe
    Aceita:
        - TransferFunction
        - StateSpace
        - Lista de sistemas
    """

    # ============================
    # Normalização de entrada
    # ============================

    if not isinstance(sys_tf, list):
        sys_tf = [sys_tf]

    # Converte StateSpace para TF se necessário
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
    # Extrai todas as TFs
    # ============================

    num_list = []
    den_list = []

    for system in sys_tf:

        for i in range(system.noutputs):
            for j in range(system.ninputs):

                tf_ij = system[i, j]

                num = tf_ij.num[0][0]
                den = tf_ij.den[0][0]

                num_str = ",".join(map(str, num))
                den_str = ",".join(map(str, den))

                num_list.append(num_str)
                den_list.append(den_str)

    # ============================
    # Converte para bloco único
    # ============================

    num_block = ";".join(num_list)
    den_block = ";".join(den_list)

    cmd = [
        "tuneControllers.exe",
        num_block,
        den_block,
        ctrl_type,
        method.lower(),
        str(wmin),
        str(wmax)
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    return parse_output(result.stdout)
# ============================
# Parser para múltiplos sistemas
# ============================

def parse_output(output):
    """
    Espera saída no formato:
    Kp=...
    Ki=...
    Kd=...
    Ti=...
    Td=...
    """

    gains = []

    current = {}

    for line in output.splitlines():

        if '=' in line:
            key, value = line.split('=')
            current[key.strip()] = float(value.strip())

        # Detecta fim de bloco (linha vazia)
        if line.strip() == "" and current:
            gains.append(current)
            current = {}

    if current:
        gains.append(current)

    return gains
