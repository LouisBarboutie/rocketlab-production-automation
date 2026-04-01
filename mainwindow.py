from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QGridLayout,
)

from ui.discovery import DiscoveryBox
from ui.testmanager import TestManager
from ui.selection import SelectionBox


class MainWindow(QMainWindow):

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("RocketLab Production Automation Demo")

        # --- Widget creation ---

        self.discovery_box = DiscoveryBox()
        self.selection_box = SelectionBox()
        self.test_manager = TestManager()

        # --- Widget connections ---

        self.selection_box.confirmed_device.connect(self.test_manager.add_test)

        # --- Widget placement ---

        layout = QGridLayout()
        layout.addWidget(self.discovery_box, 0, 0)
        layout.addWidget(self.selection_box, 1, 0)
        layout.addWidget(self.test_manager, 0, 1, 2, 1)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 3)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)
