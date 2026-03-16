from PyQt6.QtWidgets import (
    QApplication, QDialog, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QCheckBox, QPushButton, QTabWidget, QComboBox, QSpinBox,
    QSizePolicy
)
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt, QSettings

class StreamSettingsDialog(QDialog):
    def __init__(self, settings, parent, index):
        super().__init__(parent)

        self.__settings = settings
        self.__index = index

        self.setWindowTitle("Stream Settings")
        self.setMinimumWidth(500)

        layout = QVBoxLayout()

        grid_layout = QGridLayout()

        config = {}
        if self.__index >= 0:
            config = self.__settings.get_stream_config(self.__index)

        grid_layout.addWidget(QLabel("Name:"), 0, 0)
        self.name_edit = QLineEdit(config.get("name", "Default"))
        grid_layout.addWidget(self.name_edit, 0, 1)

        grid_layout.addWidget(QLabel("Address:"), 1, 0)
        self.address_edit = QLineEdit(config.get("address", "udp://127.0.0.1:5000"))
        grid_layout.addWidget(self.address_edit, 1, 1)

        layout.addLayout(grid_layout)

        # Buttons: Save / Cancel
        buttons_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(cancel_btn)
        layout.addLayout(buttons_layout)

        # Connect buttons
        save_btn.clicked.connect(self.__save_clicked)
        save_btn.clicked.connect(self.accept)  # accept closes dialog with QDialog.Accepted
        cancel_btn.clicked.connect(self.reject)  # reject closes with QDialog.Rejected

        self.setLayout(layout)

    def __save_clicked(self):
        if self.__index >= 0:
            config = self.__settings.get_stream_config(self.__index)
        else:
            config = {"enabled": True}

        config["name"] = self.name_edit.text()
        config["address"] = self.address_edit.text()

        if self.__index >= 0:
            self.__settings.update_stream_config(self.__index, config)
        else:
            self.__settings.add_stream_config(config)