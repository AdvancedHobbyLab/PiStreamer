from PyQt6.QtWidgets import (
    QApplication, QDialog, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QCheckBox, QPushButton, QTabWidget
)
from PyQt6.QtCore import QSettings

import sys

class InputTab(QWidget):
    def __init__(self):
        super().__init__()
        
        layout = QGridLayout()

        layout.addWidget(QLabel("Device: "), 0, 0)
        self.device_edit = QLineEdit()
        layout.addWidget(self.device_edit, 0, 1)

        self.setLayout(layout)

    def LoadSettings(self, settings):

        settings.beginGroup("Input")

        self.device_edit.setText(settings.value("device", ""))

        settings.endGroup()

    def SaveSettings(self, settings):

        settings.beginGroup("Input")

        settings.setValue("device", self.device_edit.text())

        settings.endGroup()

class OutputTab(QWidget):
    def __init__(self):
        super().__init__()

        address_layout = QHBoxLayout()

        address_layout.addWidget(QLabel("Address:"))
        self.address_edit = QLineEdit()
        address_layout.addWidget(self.address_edit)

        self.setLayout(address_layout)

    def LoadSettings(self, settings):

        settings.beginGroup("Output")

        self.address_edit.setText(settings.value("address", "127.0.0.1:5000"))

        settings.endGroup()

    def SaveSettings(self, settings):

        settings.beginGroup("Output")

        settings.setValue("address", self.address_edit.text())

        settings.endGroup()

class SettingsDialog(QDialog):
    def __init__(self, settings, parent):
        super().__init__(parent)

        self.__settings = settings

        self.setWindowTitle("Settings")

        layout = QVBoxLayout()

        # Setup Tabs
        tabs = QTabWidget()
        self.__tabs = [
            InputTab(),
            OutputTab()
        ]
        display_names = ["Input", "Output"]
        for tab, label in zip(self.__tabs, display_names):
            tabs.addTab(tab, label)

        for tab in self.__tabs:
            tab.LoadSettings(self.__settings)

        layout.addWidget(tabs)

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
        for tab in self.__tabs:
            tab.SaveSettings(self.__settings)