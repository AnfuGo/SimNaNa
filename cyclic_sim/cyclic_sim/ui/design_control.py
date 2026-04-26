from PyQt6.QtWidgets import (
    QMainWindow, QGraphicsView, QGraphicsScene,
    QGraphicsRectItem, QGraphicsTextItem,
    QGraphicsLineItem, QGraphicsItem, QGraphicsEllipseItem,
    QGraphicsPolygonItem,
    QDockWidget, QListWidget, QListWidgetItem
)
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton,
    QLineEdit, QFormLayout
)
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QPen, QBrush, QPolygonF
from PyQt6.QtWidgets import QGraphicsSimpleTextItem


# =========================
# MAIN WINDOW
# =========================
class BlockEditorWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Editor de Diagramas")

        self.scene = QGraphicsScene()
        self.view = GraphicsView(self.scene, self)
        self.setCentralWidget(self.view)

        self.selected_block = None
        self.temp_line = None
        self.start_port = None

        self.init_ui()
        self.create_block_palette()

        #self.add_block("PID tunable")
        #self.add_block("Planta")

    def init_ui(self):
        self.scene.setSceneRect(0, 0, 1000, 600)

    def add_block(self, name="PID"):
        block = BlockItem(name, self)
        block.setPos(100, 100)
        self.scene.addItem(block)

    def add_block_from_palette(self, item):
        name = item.text()

        block = BlockItem(name, self)

        view_center = self.view.mapToScene(
            self.view.viewport().rect().center()
        )
        block.setPos(view_center)

        self.scene.addItem(block)

    # =========================
    # CONEXÕES
    # =========================
    def start_connection(self, port):
        self.start_port = port
        self.temp_line = QGraphicsLineItem()
        self.temp_line.setPen(QPen(Qt.GlobalColor.red, 2))
        self.scene.addItem(self.temp_line)

    def update_temp_line(self, pos):
        if self.temp_line and self.start_port:
            p1 = self.start_port.scenePos()
            p2 = pos
            self.temp_line.setLine(p1.x(), p1.y(), p2.x(), p2.y())

    # =========================
    # PALETTE
    # =========================
    def create_block_palette(self):
        self.dock = QDockWidget("Blocos", self)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dock)

        self.block_list = QListWidget()

        blocks = ["PID tunable", "Planta", "K", "+/-", "Entrada", "Saída"]

        for b in blocks:
            self.block_list.addItem(QListWidgetItem(b))

        self.dock.setWidget(self.block_list)

        self.block_list.itemDoubleClicked.connect(self.add_block_from_palette)


# =========================
# CUSTOM VIEW
# =========================
class GraphicsView(QGraphicsView):
    def __init__(self, scene, editor):
        super().__init__(scene)
        self.editor = editor

    def mouseMoveEvent(self, event):
        pos = self.mapToScene(event.pos())
        self.editor.update_temp_line(pos)
        super().mouseMoveEvent(event)


# =========================
# BLOCO
# =========================
class BlockItem(QGraphicsItem):
    def __init__(self, name="Bloco", editor=None):
        super().__init__()

        self.editor = editor
        self.name = name
        self.shape_item = None

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
        )

        self.create_shape()

        # Texto (não mostrar em Entrada/Saída)
        if self.name not in ["Entrada", "Saída", "+/-"]:
            self.text = QGraphicsTextItem(name, self)
            self.text.setDefaultTextColor(Qt.GlobalColor.black)
            self.text.setPos(35, 22)
        if self.name == "K":
            self.text.setPos(12, 8)
        show_ports = self.name not in ["Entrada", "Saída"]

        self.input_port = PortItem(
            self, editor,
            is_output=False,
            visible_port=show_ports
        )

        self.output_port = PortItem(
            self, editor,
            is_output=True,
            visible_port=show_ports
        )

        self.position_ports()
    def mouseDoubleClickEvent(self, event):
        self.open_config()
        super().mouseDoubleClickEvent(event)


    def open_config(self):

        dlg = QDialog()
        dlg.setWindowTitle(f"Configurar {self.name}")
        layout = QVBoxLayout()

        if self.name == "K":
            form = QFormLayout()
            ganho = QLineEdit()
            form.addRow("Valor de K:", ganho)
            layout.addLayout(form)

        elif self.name == "PID tunable":
            form = QFormLayout()

            kp = QLineEdit()
            ki = QLineEdit()
            kd = QLineEdit()

            form.addRow("Kp:", kp)
            form.addRow("Ki:", ki)
            form.addRow("Kd:", kd)

            layout.addLayout(form)

        elif self.name == "Planta":
            form = QFormLayout()

            num = QLineEdit()
            den = QLineEdit()

            form.addRow("Numerador:", num)
            form.addRow("Denominador:", den)

            layout.addLayout(form)

        else:
            layout.addWidget(QLabel("Sem configuração"))

        btn = QPushButton("Fechar")
        btn.clicked.connect(dlg.accept)
        layout.addWidget(btn)

        dlg.setLayout(layout)
        dlg.exec()

    def boundingRect(self):
        return self.childrenBoundingRect()

    def paint(self, painter, option, widget=None):
        pass

    def create_shape(self):

        # =====================
        # SOMADOR PEQUENO
        # =====================
        if self.name == "+/-":
            self.shape_item = QGraphicsEllipseItem(0, 0, 36, 36, self)
            self.shape_item.setBrush(QBrush(Qt.GlobalColor.lightGray))
            self.shape_item.setPen(QPen(Qt.GlobalColor.black, 2))

            txt1 = QGraphicsSimpleTextItem("+", self)
            txt2 = QGraphicsSimpleTextItem("-", self)

            font = txt1.font()
            font.setPointSize(10)

            txt1.setFont(font)
            txt2.setFont(font)
            

            txt1.setPos(7, 8)
            txt2.setPos(16, 18)
            

        # =====================
        # GAIN K PEQUENO
        # =====================
        elif self.name == "K":
            poly = QPolygonF([
                QPointF(0, 0),
                QPointF(0, 40),
                QPointF(55, 20)
            ])
            self.shape_item = QGraphicsPolygonItem(poly, self)
            self.shape_item.setBrush(QBrush(Qt.GlobalColor.lightGray))
            self.shape_item.setPen(QPen(Qt.GlobalColor.black, 2))

        # =====================
        # ENTRADA PEQUENA
        # =====================
        elif self.name == "Entrada":
            pen = QPen(Qt.GlobalColor.black, 3)

            self.line1 = QGraphicsLineItem(0, 5, 0, 25, self)
            self.line2 = QGraphicsLineItem(0, 15, 35, 15, self)

            self.line1.setPen(pen)
            self.line2.setPen(pen)

        # =====================
        # SAÍDA PEQUENA
        # =====================
        elif self.name == "Saída":
            pen = QPen(Qt.GlobalColor.black, 3)

            self.line1 = QGraphicsLineItem(0, 15, 35, 15, self)
            self.line2 = QGraphicsLineItem(35, 5, 35, 25, self)

            self.line1.setPen(pen)
            self.line2.setPen(pen)

        # =====================
        # RETANGULAR NORMAL
        # =====================
        else:
            self.shape_item = QGraphicsRectItem(0, 0, 140, 70, self)
            self.shape_item.setBrush(QBrush(Qt.GlobalColor.lightGray))
            self.shape_item.setPen(QPen(Qt.GlobalColor.black, 2))
    def position_ports(self):

        if self.name == "+/-":
            self.input_port.setPos(0, 18)

            self.input_port2 = PortItem(self, self.editor, is_output=False)
            self.input_port2.setPos(18, 36)

            self.output_port.setPos(36, 18)

        elif self.name == "K":
            self.input_port.setPos(0, 20)
            self.output_port.setPos(55, 20)

        elif self.name == "Entrada":
            self.input_port.setPos(-8, 15)
            self.output_port.setPos(35, 15)

        elif self.name == "Saída":
            self.input_port.setPos(0, 15)
            self.output_port.setPos(43, 15)

        else:
            self.input_port.setPos(0, 35)
            self.output_port.setPos(140, 35)


# =========================
# CONEXÃO
# =========================
class ConnectionItem(QGraphicsLineItem):
    def __init__(self, source, target):
        super().__init__()

        self.source = source   # porta de saída
        self.target = target   # porta de entrada

        self.setPen(QPen(Qt.GlobalColor.black, 2))
        self.update_position()

    def update_position(self):
        p1 = self.source.scenePos()
        p2 = self.target.scenePos()

        self.setLine(p1.x(), p1.y(), p2.x(), p2.y())


# =========================
# PORTA
# =========================
class PortItem(QGraphicsEllipseItem):
    def __init__(self, parent, editor, is_output=False, visible_port=True):
        super().__init__(-5, -5, 10, 10, parent)

        self.editor = editor
        self.is_output = is_output

        if visible_port:
            self.setBrush(Qt.GlobalColor.black)
            self.setPen(QPen(Qt.GlobalColor.black))
        else:
            self.setBrush(Qt.GlobalColor.transparent)
            self.setPen(QPen(Qt.GlobalColor.transparent))

    def mousePressEvent(self, event):

        # PRIMEIRO CLIQUE = escolher saída
        if self.is_output:
            self.editor.start_connection(self)

        # SEGUNDO CLIQUE = conectar na entrada
        else:
            if self.editor.start_port is not None:

                # só conecta saída -> entrada
                if self.editor.start_port.is_output:

                    line = ConnectionItem(
                        self.editor.start_port,
                        self
                    )

                    self.editor.scene.addItem(line)

                # limpa linha temporária
                if self.editor.temp_line:
                    self.editor.scene.removeItem(
                        self.editor.temp_line
                    )

                self.editor.temp_line = None
                self.editor.start_port = None

        super().mousePressEvent(event)

# =========================
# EXECUTAR
# =========================
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    win = BlockEditorWindow()
    win.resize(1200, 700)
    win.show()
    sys.exit(app.exec())