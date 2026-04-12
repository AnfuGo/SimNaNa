from PyQt6.QtWidgets import (
    QMainWindow, QGraphicsView, QGraphicsScene,
    QGraphicsRectItem, QGraphicsTextItem,
    QGraphicsLineItem, QGraphicsItem, QGraphicsEllipseItem,
    QDockWidget, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPen


# =========================
# MAIN WINDOW
# =========================
class BlockEditorWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Editor de Diagramas")

        # Scene/View primeiro
        self.scene = QGraphicsScene()
        self.view = GraphicsView(self.scene, self)
        self.setCentralWidget(self.view)

        self.selected_block = None
        self.temp_line = None
        self.start_port = None

        self.init_ui()
        self.create_block_palette()

        self.add_block("PID")
        self.add_block("Planta")

    def init_ui(self):
        self.scene.setSceneRect(0, 0, 1000, 600)

    # =========================
    # BLOCO
    # =========================
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

        blocks = ["PID", "Planta", "Ganho", "Soma", "Entrada", "Saída"]

        for b in blocks:
            self.block_list.addItem(QListWidgetItem(b))

        self.dock.setWidget(self.block_list)

        self.block_list.itemDoubleClicked.connect(self.add_block_from_palette)

    # =========================
    # GRAPH
    # =========================
    def build_graph(self):
        nodes = []
        edges = []

        for item in self.scene.items():
            if isinstance(item, BlockItem):
                nodes.append(item)

            if isinstance(item, ConnectionItem):
                edges.append((item.source, item.target))

        return nodes, edges


# =========================
# CUSTOM VIEW (ESSENCIAL)
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
class BlockItem(QGraphicsRectItem):
    def __init__(self, name="Bloco", editor=None):
        super().__init__(0, 0, 140, 70)

        self.editor = editor
        self.name = name

        self.setBrush(Qt.GlobalColor.lightGray)
        self.setPen(QPen(Qt.GlobalColor.black, 2))

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
        )

        # Texto
        self.text = QGraphicsTextItem(name, self)
        self.text.setPos(30, 20)

        # Portas
        self.input_port = PortItem(self, editor, is_output=False)
        self.input_port.setPos(0, 35)

        self.output_port = PortItem(self, editor, is_output=True)
        self.output_port.setPos(140, 35)


# =========================
# CONEXÃO
# =========================
class ConnectionItem(QGraphicsLineItem):
    def __init__(self, source, target):
        super().__init__()

        self.source = source
        self.target = target

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
    def __init__(self, parent, editor, is_output=False):
        super().__init__(-5, -5, 10, 10, parent)

        self.editor = editor
        self.is_output = is_output

        self.setBrush(Qt.GlobalColor.black)

    def mousePressEvent(self, event):
        if self.is_output:
            self.editor.start_connection(self)
        super().mousePressEvent(event)