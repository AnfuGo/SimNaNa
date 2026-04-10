import numpy as np
import sympy as sp


def save_config_to_txt(main_window, file_path):

    with open(file_path, "w") as f:

        # ===== Dimensões =====
        f.write(f"n_states={main_window.n_states_spin.value()}\n")
        f.write(f"n_inputs={main_window.n_inputs_spin.value()}\n")
        f.write(f"n_outputs={main_window.n_outputs_spin.value()}\n")
        f.write(f"n_stages={main_window.stage_count_spin.value()}\n\n")

        # ===== Stages =====
        for idx in sorted(main_window.stages_data.keys()):

            stage = main_window.stages_data[idx]

            f.write(f"[STAGE_{idx}]\n")
            f.write(f"duty={stage['duty']}\n")

            for matrix_name in ["A", "B", "C", "D"]:

                matrix = stage[matrix_name]

                f.write(f"{matrix_name}=\n")

                for row in matrix:
                    row_str = ",".join(str(x) for x in row)
                    f.write(row_str + "\n")

                f.write("\n")

            f.write("\n")


import sympy as sp


def load_config_from_txt(main_window, file_path):

    with open(file_path, "r") as f:
        lines = f.readlines()

    # ===============================
    # BLOQUEAR SINAIS TEMPORARIAMENTE
    # ===============================
    main_window.n_states_spin.blockSignals(True)
    main_window.n_inputs_spin.blockSignals(True)
    main_window.n_outputs_spin.blockSignals(True)
    main_window.stage_count_spin.blockSignals(True)

    main_window.stages_data.clear()
    main_window.parameters = {}

    current_stage = None
    matrix_name = None
    matrix = []

    for line in lines:

        line = line.strip()

        if not line:
            continue

        # Dimensões
        if line.startswith("n_states"):
            main_window.n_states_spin.setValue(int(line.split("=")[1]))

        elif line.startswith("n_inputs"):
            main_window.n_inputs_spin.setValue(int(line.split("=")[1]))

        elif line.startswith("n_outputs"):
            main_window.n_outputs_spin.setValue(int(line.split("=")[1]))

        elif line.startswith("n_stages"):
            main_window.stage_count_spin.setValue(int(line.split("=")[1]))

        # Novo estágio
        elif line.startswith("[STAGE_"):
            if matrix_name is not None:
                main_window.stages_data[current_stage][matrix_name] = matrix
                matrix_name = None

            current_stage = int(line.split("_")[1].replace("]", ""))
            main_window.stages_data[current_stage] = {}

        elif line.startswith("duty"):
            duty = float(line.split("=")[1])
            main_window.stages_data[current_stage]["duty"] = duty

        # Nova matriz
        elif line in ["A=", "B=", "C=", "D="]:

            if matrix_name is not None:
                main_window.stages_data[current_stage][matrix_name] = matrix

            matrix_name = line.replace("=", "")
            matrix = []

        # Linha simbólica
        else:

            row_expr = []

            for value in line.split(","):

                expr = sp.sympify(value.strip())
                row_expr.append(expr)

                for symbol in expr.free_symbols:
                    name = str(symbol)
                    if name not in main_window.parameters:
                        main_window.parameters[name] = 1.0

            matrix.append(row_expr)

    # salvar última matriz
    if matrix_name is not None:
        main_window.stages_data[current_stage][matrix_name] = matrix

    # ===============================
    # RECRIAR STAGES VAZIOS PRIMEIRO
    # ===============================
    main_window.initialize_stages()

    # ===============================
    # LIBERAR SINAIS
    # ===============================
    main_window.n_states_spin.blockSignals(False)
    main_window.n_inputs_spin.blockSignals(False)
    main_window.n_outputs_spin.blockSignals(False)
    main_window.stage_count_spin.blockSignals(False)

    # ===============================
    # AGORA ATUALIZAR UI
    # ===============================
    main_window.load_stage_data()
    main_window.update_parameter_tab()
    main_window.remade_config()
