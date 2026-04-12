from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit,
    QSplitter, QTabWidget, QFormLayout,
    QTextEdit, QMessageBox,
    QSpinBox, QTableWidget,
    QHeaderView, QSizePolicy,
    QComboBox, QDoubleSpinBox,
    QFileDialog, QHBoxLayout,
    QGroupBox, QScrollArea
)
from .function_matrix import MatrixController, parse_si_value 
from PyQt6.QtCore import Qt
from ..models import Stage, CyclicSystemConfig, SimulationConfig
from ..API_python import CyclicStateSpaceSimulator
from .plot_editor_window import PlotEditorWindow
from ..config import PlotConfig
from ..comparison_plot import load_txt_file, comparison_functions
from .symbolic_builder import SymbolicMatrix
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib import rcParams, font_manager
from .design_control import BlockEditorWindow
import control as ct
import numpy as np
import copy
from ..control_mat_3_12 import run_controller_design, convergency_results

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        MainWindow.update_stage_list = MatrixController.update_stage_list
        MainWindow.initialize_stages = MatrixController.initialize_stages
        MainWindow.update_duty_cycle = MatrixController.update_duty_cycle
        MainWindow.load_stage_data = MatrixController.load_stage_data
        MainWindow.populate_table = MatrixController.populate_table
        MainWindow.update_matrix_size = MatrixController.update_matrix_size
        MainWindow.matrix_changed = MatrixController.matrix_changed
        MainWindow.resize_matrix = MatrixController.resize_matrix
        #MainWindow.update_parameter_panel = MatrixController.update_parameter_panel
        MainWindow.on_matrix_changed = MatrixController.on_matrix_changed
        MainWindow.evaluate_matrix = MatrixController.evaluate_matrix
        MainWindow.load_current_matrix = MatrixController.load_current_matrix
        MainWindow._resize_matrix = MatrixController._resize_matrix
        MainWindow.load_comparison_file = comparison_functions.load_comparison_file
        MainWindow.plot_comparison = comparison_functions.plot_comparison
        MainWindow.open_file_dialog = comparison_functions.open_file_dialog
        MainWindow.configs_edit = PlotConfig.configs_edit

        self.stages_data = {}

        self.setWindowTitle("Simulador")
        self.setMinimumSize(700, 700)

        print("Programa Iniciado")

        self.control_methods = {
            "P": ["pidtune", "looptune"],
            "PI": ["pidtune", "looptune"],
            "PID": ["pidtune", "looptune"],
            "Retroativo": ["acker", "place"],
            "Adaptativo": []
        }

        # ==========================================
        # WIDGET CENTRAL
        # ==========================================
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # ==========================================
        # TAB PRINCIPAL
        # ==========================================
        self.main_tabs = QTabWidget()
        main_layout.addWidget(self.main_tabs)

        # ==========================================
        # ABA 1 — Layout Original com Splitter
        # ==========================================
        self.tab_main = QWidget()
        tab_main_layout = QVBoxLayout()
        self.tab_main.setLayout(tab_main_layout)

        self.main_splitter = QSplitter(Qt.Orientation.Vertical)
        self.top_splitter = QSplitter(Qt.Orientation.Horizontal)

        # painel resultados original
        self.results_panel = self.create_results_panel()

        self.top_splitter.addWidget(self.create_tabs_panel())

        self.main_splitter.addWidget(self.top_splitter)
        self.main_splitter.addWidget(self.results_panel)

        self.main_splitter.setStretchFactor(0, 3)
        self.main_splitter.setStretchFactor(1, 2)

        tab_main_layout.addWidget(self.main_splitter)

        self.main_tabs.addTab(self.tab_main, "Simulação")

        # ==========================================
        # ABA 2 — Resultados Expandido
        # ==========================================
        self.tab_results_large = QWidget()
        results_large_layout = QVBoxLayout()
        self.tab_results_large.setLayout(results_large_layout)

        self.tf_text_tab = QTextEdit()
        self.tf_text_tab.setReadOnly(True)
        self.tf_text_tab.setStyleSheet("""
            font-family: Consolas;
            font-size: 12pt;
            padding: 10px;
        """)

        results_large_layout.addWidget(self.tf_text_tab)

        self.main_tabs.addTab(self.tab_results_large, "Resultados (TFs / Controle)")


    # ==========================================================
    # PAINEL DE ABAS (Matrizes / Parâmetros / Simulação)
    # ==========================================================

    def create_tabs_panel(self):

        tabs = QTabWidget()

        tabs.addTab(self.create_matrix_tab(), "Matrizes")
        tabs.addTab(self.create_parameter_tab(), "Parâmetros")
        tabs.addTab(self.create_simulation_tab(), "Simulação")
        tabs.addTab(self.create_config_tab(), "Configuração")
        tabs.addTab(self.create_comparison_tab(), "Comparação de resultados")
        tabs.addTab(self.create_control_tab(), "Controle")

        return tabs

    # ==========================================================
    # ABA MATRIZES
    # ==========================================================

    def create_matrix_tab(self):

        widget = QWidget()
        layout = QVBoxLayout()

    # ================================
    # NÚMERO DE ETAPAS
    # ================================
        stage_count_layout = QHBoxLayout()

        self.stage_count_spin = QSpinBox()
        self.stage_count_spin.setMinimum(1)
        self.stage_count_spin.setValue(3)
        self.stage_count_spin.valueChanged.connect(self.update_stage_list)

        stage_count_layout.addWidget(QLabel("Número de Etapas:"))
        stage_count_layout.addWidget(self.stage_count_spin)

        layout.addLayout(stage_count_layout)

    # ================================
    # SELEÇÃO DE ETAPA + DC
    # ================================
        stage_select_layout = QHBoxLayout()

        self.stage_selector = QComboBox()
        self.stage_selector.currentIndexChanged.connect(self.load_stage_data)

        self.duty_spin = QDoubleSpinBox()
        self.duty_spin.setRange(0.0, 1.0)
        self.duty_spin.setSingleStep(0.01)
        self.duty_spin.setValue(0.5)
        self.duty_spin.valueChanged.connect(self.update_duty_cycle)

        stage_select_layout.addWidget(QLabel("Etapa:"))
        stage_select_layout.addWidget(self.stage_selector)
        stage_select_layout.addWidget(QLabel("Duty Cycle:"))
        stage_select_layout.addWidget(self.duty_spin)

        layout.addLayout(stage_select_layout)

    # ================================
    # SELEÇÃO DA MATRIZ (A B C D)
    # ================================
        matrix_select_layout = QHBoxLayout()

        self.matrix_selector = QComboBox()
        self.matrix_selector.addItems(["A", "B", "C", "D"])
        self.matrix_selector.currentIndexChanged.connect(self.on_matrix_changed)

        matrix_select_layout.addWidget(QLabel("Matriz:"))
        matrix_select_layout.addWidget(self.matrix_selector)

        layout.addLayout(matrix_select_layout)

    # ================================
    # DIMENSÕES DO SISTEMA
    # ================================
        dimension_layout = QHBoxLayout()

        self.n_states_spin = QSpinBox()
        self.n_states_spin.setMinimum(1)
        self.n_states_spin.setValue(4)
        self.n_states_spin.valueChanged.connect(self.update_matrix_size)

        self.n_inputs_spin = QSpinBox()
        self.n_inputs_spin.setMinimum(1)
        self.n_inputs_spin.setValue(1)
        self.n_inputs_spin.valueChanged.connect(self.update_matrix_size)

        self.n_outputs_spin = QSpinBox()
        self.n_outputs_spin.setMinimum(1)
        self.n_outputs_spin.setValue(1)
        self.n_outputs_spin.valueChanged.connect(self.update_matrix_size)
        self.n_outputs_spin.valueChanged.connect(self.remade_config)

        dimension_layout.addWidget(QLabel("Estados (n):"))
        dimension_layout.addWidget(self.n_states_spin)

        dimension_layout.addWidget(QLabel("Entradas (m):"))
        dimension_layout.addWidget(self.n_inputs_spin)

        dimension_layout.addWidget(QLabel("Saídas (p):"))
        dimension_layout.addWidget(self.n_outputs_spin)

        layout.addLayout(dimension_layout)
        # ================================
        # BOTÕES SALVAR / CARREGAR CONFIG
        # ================================
        config_buttons_layout = QHBoxLayout()

        self.save_config_button = QPushButton("Salvar Configuração")
        self.load_config_button = QPushButton("Carregar Configuração")

        self.save_config_button.clicked.connect(self.save_matrix_config)
        self.load_config_button.clicked.connect(self.load_matrix_config)

        config_buttons_layout.addWidget(self.save_config_button)
        config_buttons_layout.addWidget(self.load_config_button)

        layout.addLayout(config_buttons_layout)


        # ================================
        # TABELA
        # ================================
        self.matrix_table = QTableWidget(4, 4)

        self.matrix_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.matrix_table.verticalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        self.matrix_table.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

        self.matrix_table.cellChanged.connect(self.matrix_changed)

        layout.addWidget(self.matrix_table)

        widget.setLayout(layout)

        # Inicialização
        self.initialize_stages()

        return widget

    # ==========================================================
    # ABA PARÂMETROS
    # ==========================================================

    def create_parameter_tab(self):

        widget = QWidget()
        layout = QFormLayout()

        self.param_placeholder = QLineEdit()
        self.param_placeholder.setPlaceholderText(
            "Os parâmetros detectados aparecerão aqui dinamicamente."
        )

        layout.addRow("Parâmetros:", self.param_placeholder)
        self.param_layout = layout
        widget.setLayout(self.param_layout)
        self.parameters = {}
        self.param_inputs = {}
        return widget

    def update_parameter_tab(self):

        # Limpa estrutura auxiliar também
        self.param_inputs.clear()

        while self.param_layout.rowCount():
            self.param_layout.removeRow(0)

        for name in sorted(self.parameters.keys()):

            line = QLineEdit()
            line.setText(str(self.parameters[name]))

            line.editingFinished.connect(
                lambda n=name, l=line:
                    self._update_param_value(n, l)
            )

            self.param_layout.addRow(name, line)
            self.param_inputs[name] = line

    def _update_param_value(self, name, line):

        try:
            value = parse_si_value(line.text())
            self.parameters[name] = value

        except ValueError as e:
            QMessageBox.critical(self, "Erro de parâmetro", str(e))

        # Restaura valor anterior
            line.setText(str(self.parameters[name]))
    # ==========================================================
    # ABA SIMULAÇÃO
    # ==========================================================

    def create_simulation_tab(self):

        widget = QWidget()
        layout = QFormLayout()

        # ===== Simulação Normal =====
        self.freq_input = QLineEdit()
        self.freq_input.setObjectName("freq_input")
        self.freq_input.setPlaceholderText("Frequência (kHz)")

        self.time_input = QLineEdit()
        self.time_input.setObjectName("time")
        self.time_input.setPlaceholderText("Tempo total (ms)")

        self.resolution_input = QLineEdit()
        self.resolution_input.setObjectName("resolution_input")
        self.resolution_input.setPlaceholderText("Resolução (pontos por estágio)")

        self.function_input = QLineEdit()
        self.function_input.setObjectName("function_input")
        self.function_input.setPlaceholderText("Entrada constante (ex: 10)")

        self.run_button = QPushButton("Executar Simulação")
        self.run_button.clicked.connect(self.run_simulation)

        # ===== Pequenos Sinais =====
        self.disturbance_input = QLineEdit()
        self.disturbance_input.setPlaceholderText("Vetor perturbação (m entradas + 1 duty) (ex: 0.01,0,...)")

        self.disturbance_start_input = QLineEdit()
        self.disturbance_start_input.setPlaceholderText("Início perturbação (ms) [vetor]")

        self.disturbance_end_input = QLineEdit()
        self.disturbance_end_input.setPlaceholderText("Fim perturbação (ms) [vetor]")

        self.small_signal_button = QPushButton("Simular Pequenos Sinais")
        self.small_signal_button.clicked.connect(self.run_small_signal_simulation)

        # ===== Função de Transferência =====
        self.tf_button = QPushButton("Gerar Funções de Transferência")
        self.tf_button.clicked.connect(self.generate_transfer_functions)

        # ===== Layout =====
        layout.addRow("Frequência:", self.freq_input)
        layout.addRow("Tempo:", self.time_input)
        layout.addRow("Resolução:", self.resolution_input)
        layout.addRow("Entrada:", self.function_input)

        layout.addRow(self.run_button)

        layout.addRow(QLabel("------ Pequenos Sinais / TFs ------"))
        layout.addRow("Vetor Perturbação:", self.disturbance_input)
        layout.addRow("Início (ms):", self.disturbance_start_input)
        layout.addRow("Fim (ms):", self.disturbance_end_input)
        layout.addRow(self.small_signal_button)

        layout.addRow(self.tf_button)
        
        widget.setLayout(layout)
        return widget


    def run_small_signal_simulation(self):

        try:
            freq = float(self.freq_input.text()) * 1000
            t_final = float(self.time_input.text()) / 1000
            resolution = int(self.resolution_input.text())
            input_function = np.array(
                [float(x) for x in self.function_input.text().split(",")]
            )

            perturb_values = np.array(
                [float(x) for x in self.disturbance_input.text().split(",")]
            )

            t_start_vec = np.array(
                [float(x)/1000 for x in self.disturbance_start_input.text().split(",")]
            )

            t_end_vec = np.array(
                [float(x)/1000 for x in self.disturbance_end_input.text().split(",")]
            )

        except ValueError:
            QMessageBox.critical(self, "Erro",
                                 "Preencha corretamente os campos de pequenos sinais.")
            return

        # Número de entradas físicas
        m = self.n_inputs_spin.value()

        # Verificação dimensional correta
        if len(perturb_values) != m + 1:
            QMessageBox.critical(
                self,
                "Erro dimensional",
                f"O vetor de perturbação deve ter tamanho {m+1} "
                "(entradas + duty cycle)."
            )
            return

        if not (len(t_start_vec) == len(t_end_vec) == m + 1):
            QMessageBox.critical(
                self,
                "Erro dimensional",
                f"Os vetores de início e fim devem ter tamanho {m+1}."
            )
            return

        

        # ===== Criar sistema =====


        system_config = CyclicSystemConfig(
                stages=self.get_stages_from_ui(),
                duty_cycles=self.get_duty_cycles_from_ui(),
                switching_frequency=freq
            )

        try:
            simulator = CyclicStateSpaceSimulator(system_config)

        except ValueError as e:
            QMessageBox.critical(self, "Erro de Configuração", str(e))
            return
        
        try:
            t, y = simulator.find_small_signal_matrix(
                input_function=input_function,
                x0=[0]*self.n_states_spin.value(),
                perturb_values=perturb_values,
                t_start_vec=t_start_vec,
                t_end_vec=t_end_vec,
               t_final=t_final,
                resolution=resolution
            )

            self.create_results_selectors(y, t)
            #self.plot_results(t, y.T)

        except Exception as e:
            QMessageBox.critical(self, "Erro Small Signal", str(e))


    def generate_transfer_functions(self):

        try:
            freq = float(self.freq_input.text()) * 1000
            input_operating_point = float(self.function_input.text())
            input_operating_point = np.array(
                [float(x) for x in self.function_input.text().split(",")]
            )
            self.input = input_operating_point

        except ValueError:
            QMessageBox.critical(self, "Erro", "Preencha frequência e entrada.")
            return

        try:
            system_config = CyclicSystemConfig(
                stages=self.get_stages_from_ui(),
                duty_cycles=self.get_duty_cycles_from_ui(),
                switching_frequency=freq
            )

            simulator = CyclicStateSpaceSimulator(system_config)

            self.sys_ss, self.sys_tf, self.r = simulator.generate_tf(input_operating_point)
            try:
                result = simulator.generate_amp_matrix(input_operating_point)
                if result is None:
                    raise ValueError ("O sistema aumentado não é controlável")
                self.A_aug, self.B_aug, self.Ap, self.Bp, self.Cp, self.Dp = result

            except ValueError as e:

                QMessageBox.critical(
                    self,
                    "Erro ao gerar matrizes aumentadas:",
                    str(e)
                )

            
            self.display_transfer_functions(self.sys_tf)
            self.create_bode_selectors(self.sys_ss)

        except Exception as e:
            QMessageBox.critical(self, "Erro Transfer Function", str(e))
            
    # ==========================================================
    # PAINEL DE RESULTADOS
    # ==========================================================

    def create_results_panel(self):
        #matplotlib.font_manager._rebuild()
        rcParams["font.family"] = "CMU Serif"
        rcParams["font.size"] = 12
        plt.rcParams["mathtext.fontset"] = "custom"
        plt.rcParams["mathtext.rm"] = "CMU Serif"
        plt.rcParams["mathtext.it"] = "CMU Serif:italic"
        plt.rcParams["mathtext.bf"] = "CMU Serif:bold"

        #rcParams.update({
        #    "font.family": "CMU Serif",
        #    "font.size": 12,
        #   "mathtext.fontset": "custom",
        #    "mathtext.rm": "CMU Serif",
        #    "mathtext.it": "CMU Serif:italic",
        #    "mathtext.bf": "CMU Serif:bold"
        #})

        widget = QWidget()
        layout = QVBoxLayout()
        self.tf_text = QTextEdit()
        self.tf_text.setReadOnly(True)
        #layout.addWidget(self.tf_text)

        layout.addWidget(QLabel("Gráficos (Resultados):"))

        # ===== Figura =====
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)

        layout.addWidget(self.canvas)

        widget.setLayout(layout)
        self.open_plot_editor_btn = QPushButton("Abrir Editor de Gráfico")
        self.open_plot_editor_btn.clicked.connect(self.open_plot_editor)
        layout.addWidget(self.open_plot_editor_btn)
        
        self.output_results_selector = QComboBox()
        
        self.results_selector_layout = QHBoxLayout()

        self.results_button = QPushButton("Plotar Gráfico")
        self.results_button.clicked.connect(self.plot_results)

        self.results_selector_layout.addWidget(QLabel("Saída:"))
        self.results_selector_layout.addWidget(self.output_results_selector)
        self.results_selector_layout.addWidget(self.results_button)

        self.bode_selector_layout = QHBoxLayout()
        #self.results_selector_layout = QHBoxLayout()

        self.output_selector = QComboBox()
        self.input_selector = QComboBox()
     
        self.bode_button = QPushButton("Plotar Bode")
        self.bode_button.clicked.connect(self.plot_selected_bode)

        self.bode_selector_layout.addWidget(QLabel("Saída:"))
        self.bode_selector_layout.addWidget(self.output_selector)

        self.bode_selector_layout.addWidget(QLabel("Entrada:"))
        self.bode_selector_layout.addWidget(self.input_selector)

        self.bode_selector_layout.addWidget(self.bode_button)

        layout.addLayout(self.bode_selector_layout)
        layout.addLayout(self.results_selector_layout)
        
        return widget

    def open_plot_editor(self):

        if hasattr(self, "figure"):

            figure_copy = self.figure

            self.plot_editor_window = PlotEditorWindow(figure_copy, self.results, self.t, self.output_results_selector.currentIndex())
            self.plot_editor_window.show()
        else: Warning ("Deve-se plotar primeiro o gráfico")  

    def plot_results(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        i_result = self.output_results_selector.currentIndex()
        label = self.plot_config.get_output_name(i_result)

        if self.results.ndim == 1:
            ax.plot(self.t, self.results, label=label)
        else:
            ax.plot(self.t,
                self.results[i_result, :],
                label=label,
                color=self.plot_config.line_color,
                linewidth=self.plot_config.line_width)

        ax.set_xlabel("Tempo (s)")
        ax.set_ylabel("Saídas")
        ax.legend()
        ax.grid(True)

        self.canvas.draw()
        #self.current_x = self.t
        #self.current_y = self.results[i_result, :]

    def create_results_selectors(self, y, t):
        self.results = y
        self.t = t

        self.output_results_selector.clear()

        n_outputs = y.shape[0]  # sempre (p, N)

        for i in range(n_outputs):
            self.output_results_selector.addItem(f"Saída {i+1}")
            
    def create_bode_selectors(self, sys_ss):

        self.current_sys = sys_ss

        self.output_selector.clear()
        self.input_selector.clear()

        for i in range(sys_ss.noutputs):
            self.output_selector.addItem(f"Saída {i+1}")

        for j in range(sys_ss.ninputs):
            self.input_selector.addItem(f"Entrada {j+1}")

    def plot_selected_bode(self):

        if not hasattr(self, "current_sys"):
            return

        i = self.output_selector.currentIndex()
        j = self.input_selector.currentIndex()

        sys_ij = self.current_sys[i, j]

        w = np.logspace(1, 6, 1000)

        mag, phase, omega = ct.bode(sys_ij, w, plot=False)

        self.figure.clear()

        ax1 = self.figure.add_subplot(211)
        ax2 = self.figure.add_subplot(212)

        ax1.semilogx(omega, 20*np.log10(mag))
        ax1.set_ylabel("Magnitude (dB)")
        ax1.grid(True)

        ax2.semilogx(omega, phase * 180/np.pi)
        ax2.set_ylabel("Fase (graus)")
        ax2.set_xlabel("Frequência (rad/s)")
        ax2.grid(True)

        self.canvas.draw()
        #self.current_bode_data = (omega, mag, phase)

    def display_transfer_functions(self, sys_tf):

        self.tf_text.clear()

        n_outputs = sys_tf.noutputs
        n_inputs = sys_tf.ninputs

        text = "FUNÇÕES DE TRANSFERÊNCIA:\n\n"

        for i in range(n_outputs):
            for j in range(n_inputs):
                tf_ij = sys_tf[i, j]
                text += f"G({i},{j})(s) =\n{tf_ij}\n\n"

        self.tf_text.setText(text)
        # Atualiza aba expandida
        self.tf_text_tab.setText(text)

        # Alterna automaticamente para aba expandida
        self.main_tabs.setCurrentWidget(self.tab_results_large)

    # ==========================================================
    # SIMULAÇÃO
    # ==========================================================

    def run_simulation(self):

        try:
            
            freq_input = self.findChild(QLineEdit, "freq_input")
            freq = float(freq_input.text()) * 1000
            #freq = float(self.freq_input.text()) * 1000
            time = self.findChild(QLineEdit, "time")
            t_final = float(time.text()) / 1000
            resolution_input = self.findChild(QLineEdit, "resolution_input")
            resolution = int(resolution_input.text())
            input_fun = self.findChild(QLineEdit, "function_input")
            input_function = float(input_fun.text())

        except ValueError:
            QMessageBox.critical(self, "Erro", "Preencha os campos corretamente.")
            return

        try:
            system_config = CyclicSystemConfig(
                stages=self.get_stages_from_ui(),
                duty_cycles=self.get_duty_cycles_from_ui(),
                switching_frequency=freq
            )

            sim_config = SimulationConfig(
                x0=[0]*self.n_states_spin.value(),
                t_final=t_final,
                input_function=input_function,
                resolution=resolution
            )

            try:
                simulator = CyclicStateSpaceSimulator(system_config)

            except ValueError as e:
                QMessageBox.critical(self, "Erro de Configuração", str(e))
                return

            t, y, xf = simulator.simulate(
                x0=sim_config.x0,
                t_final=sim_config.t_final,
                input_function=sim_config.input_function,
                resolution=sim_config.resolution
            )

            #self.plot_results(t, y)
            self.create_results_selectors(y, t)

        except Exception as e:
            QMessageBox.critical(self, "Erro na simulação", str(e))
    def get_stages_from_ui(self):

        param_values = {}

        try:
            if hasattr(self, "param_inputs"):

                for param, line in self.param_inputs.items():

                    raw_value = parse_si_value(line.text())

                    param_values[param] = raw_value

        except Exception as e:
            QMessageBox.critical(self, "Erro de parâmetros", str(e))
            return None


        stages = []

        for idx in sorted(self.stages_data.keys()):

            stage_dict = self.stages_data[idx]

            A = self.evaluate_matrix(stage_dict["A"], param_values)
            B = self.evaluate_matrix(stage_dict["B"], param_values)
            C = self.evaluate_matrix(stage_dict["C"], param_values)
            D = self.evaluate_matrix(stage_dict["D"], param_values)

            stages.append(Stage(A=A, B=B, C=C, D=D))

        return stages 

    def get_duty_cycles_from_ui(self):

        duty_cycles = []

        for idx in sorted(self.stages_data.keys()):
            duty_cycles.append(self.stages_data[idx]["duty"])

        return duty_cycles

    # ==========================================================
    # ABA Configurações
    # ==========================================================

    def create_config_tab(self):
        self.plot_config = PlotConfig()

        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(5)

        # ==========================================
        # GRUPO — NOMES DAS SAÍDAS
        # ==========================================
        self.group_outputs = QGroupBox("Nomes das Saídas")
        self.group_layout = QFormLayout()
        self.group_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.group_layout.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        self.group_layout.setVerticalSpacing(4)
        self.group_layout.setHorizontalSpacing(10)
        self.group_outputs.setLayout(self.group_layout)

        self.output_name_inputs = []

        n_outputs = self.n_outputs_spin.value()

        for i in range(n_outputs):
            line = QLineEdit()
            line.setPlaceholderText(f"Saída {i+1}")
            line.setMinimumWidth(200)

            def make_callback(idx, line_edit):
                return lambda: self.plot_config.set_output_name(idx, line_edit.text())

            line.editingFinished.connect(make_callback(i, line))
            self.output_name_inputs.append(line)
            self.group_layout.addRow(f"Saída {i+1}:", line)

        # ==========================================
        # SCROLL AREA 
        # ==========================================
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.group_outputs)
        self.scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.scroll.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

        main_layout.addWidget(self.scroll)

        # Remove stretch para que scroll ocupe todo espaço
        # main_layout.addStretch(1)  # removido

        self.n_outputs_spin.valueChanged.connect(self.remade_config)

        return widget


    def create_comparison_tab(self):
        """Cria a aba de comparação de arquivos de resultados."""

        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # ===== Seleção de arquivo =====
        file_layout = QHBoxLayout()
        self.file_path_input = QLineEdit()
        self.file_path_input.setPlaceholderText("Selecione o arquivo .txt")

        self.browse_button = QPushButton("Procurar")
        self.browse_button.clicked.connect(self.open_file_dialog)

        file_layout.addWidget(self.file_path_input)
        file_layout.addWidget(self.browse_button)
        layout.addLayout(file_layout)

        # ===== Botão de carregar =====
        self.load_button = QPushButton("Carregar Arquivo")
        self.load_button.clicked.connect(self.load_comparison_file)
        layout.addWidget(self.load_button)

        # ===== Seleção de saída =====
        form_layout = QFormLayout()
        self.compare_selector = QComboBox()
        form_layout.addRow("Selecionar Saída:", self.compare_selector)
        layout.addLayout(form_layout)

        # ===== Botão de plotagem =====
        self.compare_button = QPushButton("Plotar Comparação")
        self.compare_button.setMinimumHeight(30)
        layout.addWidget(self.compare_button)
        self.compare_button.clicked.connect(self.plot_comparison)

        # Espaço final para alongar layout
        layout.addStretch()

        return widget

    def remade_config(self):
        """Atualiza dinamicamente os nomes das saídas quando n_outputs muda."""

        # Limpar lista antiga
        self.output_name_inputs.clear()

        # Limpar todos os widgets do group_layout
        while self.group_layout.count():
            item = self.group_layout.takeAt(0)
            if item is None:
                continue
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
            else:
                # Caso seja layout interno
                layout_item = item.layout()
                if layout_item is not None:
                    while layout_item.count():
                        w = layout_item.takeAt(0).widget()
                        if w is not None:
                            w.setParent(None)
                            w.deleteLater()

        # Novo número de saídas
        n_outputs = self.n_outputs_spin.value()

        # Recriar campos
        for i in range(n_outputs):
            line = QLineEdit()
            line.setPlaceholderText(f"Saída {i+1}")
            line.setMinimumWidth(200)

            # Callback correto
            def make_callback(idx, line_edit):
                return lambda: self.plot_config.set_output_name(idx, line_edit.text())
            line.editingFinished.connect(make_callback(i, line))

            self.output_name_inputs.append(line)
            self.group_layout.addRow(f"Saída {i+1}:", line)

        # Forçar atualização do scroll e do layout
        self.group_outputs.update()
        self.scroll.update()
        self.scroll.repaint()
    # ==========================================================
    # ABA Controle
    # ==========================================================

    def create_control_tab(self):

        widget = QWidget()
        layout = QFormLayout()

        # =========================
        # Tipo de controlador
        # =========================

        self.control_type_combo = QComboBox()
        self.control_type_combo.addItems(self.control_methods.keys())
        self.control_type_combo.currentTextChanged.connect(self.update_method_box)

        # =========================
        # Método
        # =========================

        self.method_combo = QComboBox()
        self.method_combo.currentTextChanged.connect(self.update_method_value)

        # =========================
        # Banda de frequência
        # =========================

        self.freq_banda_input = QLineEdit()
        self.freq_banda_input.setPlaceholderText("Ex: 10,100 (Hz)")

        self.freq_banda_label = QLabel("Faixa de frequência desejada [wmin,wmax]:")

        # =========================
        # Polos desejados
        # =========================

        self.poles_input = QLineEdit()
        self.poles_input.setPlaceholderText("Ex: -2,-3-46j,-5+46.54i...")

        self.poles_label = QLabel("Polos desejados:")

        self.poles_label.setVisible(False)
        self.poles_input.setVisible(False)

        # =========================
        # Botões
        # =========================

        self.control_button = QPushButton("Gerar Parâmetros do Controlador")
        self.control_button.clicked.connect(self.generate_control_parameters)

        self.bode_control_button = QPushButton("Gerar Bode do Controlador")
        self.bode_control_button.clicked.connect(self.generate__bode_control_parameters)

        self.convergency_button = QPushButton("Avaliar Convergência do Controlador a zero")
        self.convergency_button.clicked.connect(self.generate_convergency_display)
        self.convergency_button.setVisible(False)

        self.btn_design_control = QPushButton("Abrir Editor de Controle")
        self.btn_design_control.clicked.connect(self.open_block_editor)

        # inicializa
        self.update_method_box()


        # =========================
        # Layout
        # =========================

        layout.addRow("Tipo de Controlador:", self.control_type_combo)
        layout.addRow("Método:", self.method_combo)
        layout.addRow(self.freq_banda_label, self.freq_banda_input)
        layout.addRow(self.poles_label, self.poles_input)
        layout.addRow(self.control_button)
        layout.addRow(self.bode_control_button)
        layout.addRow(self.convergency_button)
        layout.addRow(self.btn_design_control)

        widget.setLayout(layout)

        return widget

    def update_method_box(self):

        control_type = self.control_type_combo.currentText()

        self.method_combo.clear()

        methods = self.control_methods.get(control_type, [])

        if methods:
            self.method_combo.addItems(methods)
            self.method_combo.setEnabled(True)
            self.method_control = methods[0]   # método default
        else:
            self.method_combo.setEnabled(False)
            self.method_control = None

    def update_method_value(self):

        self.method_control = self.method_combo.currentText()
        # métodos que usam polos
        pole_methods = ["acker", "place", "pole placement"]

        if self.method_control in pole_methods:
            self.poles_label.setVisible(True)
            self.poles_input.setVisible(True)
            self.freq_banda_label.setVisible(False)
            self.freq_banda_input.setVisible(False)
            self.convergency_button.setVisible(True)
        else:
            self.freq_banda_label.setVisible(True)
            self.freq_banda_input.setVisible(True)
            self.poles_label.setVisible(False)
            self.poles_input.setVisible(False)
            self.convergency_button.setVisible(False)

    def generate_control_parameters(self):

        if self.method_control is None:
            QMessageBox.warning(self, "Método", "Selecione um método de projeto.")
            return

        # leitura da banda de frequência
        if self.method_control in ["pidtune", "looptune"]:
            freq_banda = np.array(
                [float(x) for x in self.freq_banda_input.text().split(",")]
            )
        else:
            freq_banda = None

        polos_desejados = None

        # leitura dos polos (caso necessário)
        if self.method_control in ["acker", "place", "pole placement"]:

            try:
                polos_desejados = self.parse_poles(self.poles_input.text())
                #polos_desejados = [complex(x) for x in self.poles_input.text().split(",")]

            except ValueError:

                QMessageBox.critical(
                    self,
                    "Erro nos polos",
                    "Digite os polos no formato: -2,-3+54j,-5-54i"
                )
                return

        control_type = self.control_type_combo.currentText()
        self.poles = polos_desejados
        try:

            #print(self.sys_tf)
            if not hasattr(self, "sys_tf"):
                self.generate_transfer_functions()

            self.gains_control = run_controller_design(
                self.sys_tf,
                control_type,
                self.method_control,
                freq_banda,
                polos_desejados,
                self
            )

            self.method_control_calc = self.method_control
            self.generate_control_text()

        except ValueError as e:

            QMessageBox.critical(
                self,
                "Erro ao gerar os parâmetros de controle",
                str(e)
            )
            print(e)

            return None
    def generate_convergency_display(self):

        try:
            time = float(self.time_input.text()) / 1000

        except Exception:
            QMessageBox.critical(
                self,
                "Erro",
                "Tente adicionar o tempo na aba de simulação"
            )
            return

        if not hasattr(self, "gains_control"):
            QMessageBox.warning(self, "Aviso", "Projete o controlador primeiro")
            return

        pole_methods = ["acker", "place", "pole placement"]

        if self.method_control_calc in pole_methods:
            K = self.gains_control
            C = self.Cp
            D = self.Dp
            D = D[:,1:2] # retira os estados referentes as entradas deixando apenas o que refere-se ao DC
            if self.integrator == 1:
                A = self.A_aug
                B = self.B_aug

            elif self.integrator == 0:
                A = self.Ap
                B = self.Bp
                B = B[:,1:2]
        else:
            QMessageBox.warning(self, "Aviso", "Método de controle não suportado")
            return

        print(f"entrada: {self.input}")
        print(f"r: {self.r}")
        t, x, erro, integral, y  = convergency_results(K, A, B, C, D, self.input, self.r, time, self.integrator)
        #if self.integrator == 1:
        #    C = np.hstack((C, np.zeros((C.shape[0],1))))
            #C = np.vstack((C, np.eye(1, C.shape[1], C.shape[1]-1)))
        #    Ci = np.zeros((1, C.shape[1]))
        #    Ci[0, -1] = 1
        #    C = np.vstack((C, Ci))
         
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        print("X shape:", x.shape)
        print("C shape:", C.shape)
        print("C:", C)
        print("Erro shape:", erro.shape)
        print("Tempo shape:", t.shape)
        #y = C@x[:-1] + D@self.input

        #for i in range(x.shape[0]):
        #   ax.plot(t, x[i, :], label=f"$x_{i+1}$")
        for i in range(y.shape[0]):
            ax.plot(t, y[i, :], label=f"$y_{i+1}$")

        for i in range(erro.shape[0]):
            ax.plot(t, erro[i, :], label=f"$erro_{i+1}$")
            
        if self.integrator: 
            ax.plot(t, integral, label=f"$integral$")
            
        ax.set_xlabel("Tempo (s)")
        ax.set_ylabel("Saídas")
        ax.legend()
        ax.grid(True)

        self.canvas.draw()
   
    def generate_control_text(self):

        if not hasattr(self, "gains_control"):
            self.tf_text.setText("Ganhos não calculados.")
            return

        if not hasattr(self, "current_sys"):
            self.tf_text.setText("Sistema não definido.")
            return

        self.tf_text.clear()

        control_type = self.control_type_combo.currentText()

        text = "GANHOS DO CONTROLADOR:\n\n"

        # =========================
        # CASO RETROATIVO
        # =========================

        if control_type.lower() == "retroativo":

            text += f"Tipo de controle: Retroação de Estados\n"
            text += f"Método utilizado: {self.method_control}\n\n"

            K = self.gains_control
            
            text += "Matriz de ganhos K [K1 K2... Kn -Ki]:\n\n"
            text += f"{np.array2string(K, precision=6)}\n\n"

            text += "Lei de controle:\n"
            if self.integrator:
                text += "u = - Kx + "
                text += r"$k_i$ξ\n"
            else:
                text += "u = r - Kx\n"

            poles = self.poles

            text += "Polos de malha fechada:\n\n"
            text += f"{np.array2string(poles, precision=6)}\n\n"

            text += "Os métodos de acker ou place fazem o controle para a entrada DutyCycle(DC)\n\n"

            self.tf_text.setText(text)
            self.tf_text_tab.setText(text)
            self.main_tabs.setCurrentWidget(self.tab_results_large)

            return

        # =========================
        # CASO PID / PI / P
        # =========================

        sys_tf = self.current_sys

        n_outputs = sys_tf.noutputs
        n_inputs = sys_tf.ninputs

        idx = 0

        for i in range(n_outputs):
            for j in range(n_inputs):

                G = sys_tf[i, j]
                gains = self.gains_control[idx]

                Kp = float(gains["Kp"])
                Ki = float(gains["Ki"])
                Kd = float(gains["Kd"])
                Ti = float(gains["Ti"])
                Td = float(gains["Td"])

                text += f"Canal G({i},{j})(s):\n"
                text += f"{G}\n\n"

                text += (
                    f"Kp = {Kp:.6g}\n"
                    f"Ki = {Ki:.6g}\n"
                    f"Kd = {Kd:.6g}\n"
                )

                if Ti != 0:
                    text += f"Ti = {Ti:.6g}\n"

                if Td != 0:
                    text += f"Td = {Td:.6g}\n"

                text += "\n-----------------------------\n\n"

                idx += 1

        self.tf_text.setText(text)
        self.tf_text_tab.setText(text)
        self.main_tabs.setCurrentWidget(self.tab_results_large)

    def generate__bode_control_parameters(self):

        if not hasattr(self, "current_sys"):
            return
    
        if not hasattr(self, "gains_control"):
            print("Ganhos não definidos")
            return

        i = self.output_selector.currentIndex()
        j = self.input_selector.currentIndex()

        G = self.current_sys[i, j]

    # ===== Seleção dos ganhos =====
        try:
        # Caso estrutura tipo dict[i][j]
            gains_ij = self.gains_control[i][j]

            Kp = gains_ij.get("Kp", 0)
            Ki = gains_ij.get("Ki", 0)
            Kd = gains_ij.get("Kd", 0)

        except Exception:
            try:
            # Caso matrizes separadas
                Kp = self.Kp_matrix[i, j]
                Ki = self.Ki_matrix[i, j]
                Kd = self.Kd_matrix[i, j]

            except Exception:
                print("Formato de ganhos inválido.")
                QMessageBox.warning(self, "Aviso", "Formato de ganhos inválido.")
                
                return

        s = ct.tf("s")

    # ===== Controlador =====
        if self.control_type_combo == "P":
            C = Kp

        elif self.control_type_combo == "PI":
            C = Kp + Ki / s

        elif self.control_type_combo == "PID":
            C = Kp + Ki / s + Kd * s

        else:
            print("Tipo de controlador inválido")
            return

    # ===== Malha aberta =====
        L = C * G

    # ===== Frequência =====
        w = np.logspace(1, 6, 1000)

        mag_C, phase_C, _ = ct.bode(C, w, plot=False)
        mag_L, phase_L, omega = ct.bode(L, w, plot=False)

    # ===== Plot =====
        self.figure.clear()

        ax1.set_title(f"Bode Controlador + Malha Aberta → Canal G({i},{j})")

        ax1 = self.figure.add_subplot(211)
        ax2 = self.figure.add_subplot(212)

    # --- Magnitude ---
        ax1.semilogx(omega, 20*np.log10(mag_C), linestyle='--', label="|C(s)|")
        ax1.semilogx(omega, 20*np.log10(mag_L), label="|L(s)=C·G|")

        ax1.set_ylabel("Magnitude (dB)")
        ax1.grid(True)
        ax1.legend()

    # --- Fase ---
        ax2.semilogx(omega, phase_C * 180/np.pi, linestyle='--', label="∠C(s)")
        ax2.semilogx(omega, phase_L * 180/np.pi, label="∠L(s)")

        ax2.set_ylabel("Fase (graus)")
        ax2.set_xlabel("Frequência (rad/s)")
        ax2.grid(True)
        ax2.legend()

        self.canvas.draw()

    def save_matrix_config(self):

        from ..save_configs import save_config_to_txt

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar configuração",
            "",
            "Arquivos TXT (*.txt)"
        )

        if not file_path:
            return

        try:
            save_config_to_txt(self, file_path)
            QMessageBox.information(self, "Sucesso", "Configuração salva com sucesso.")
        except Exception as e:
            QMessageBox.critical(self, "Erro ao salvar", str(e))


    def load_matrix_config(self):

        from ..save_configs import load_config_from_txt

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Carregar configuração",
            "",
            "Arquivos TXT (*.txt)"
        )

        if not file_path:
            return

        try:
            load_config_from_txt(self, file_path)
            QMessageBox.information(self, "Sucesso", "Configuração carregada com sucesso.")
        except Exception as e:
            QMessageBox.critical(self, "Erro ao carregar", str(e))


    def parse_poles(self, text):

        poles = []

        for p in text.split(","):
            p = p.strip().replace("i","j")
            poles.append(complex(p))

        return np.array(poles, dtype=complex)
    
    def open_block_editor(self):
        self.editor = BlockEditorWindow()
        self.editor.show()




        
