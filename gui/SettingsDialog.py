from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QCheckBox, QPushButton
)
from PyQt6.QtCore import QSettings

import sys

class SettingsDialog(QDialog):
    def __init__(self, settings):
        super().__init__()
        self.setWindowTitle("Settings")

        layout = QVBoxLayout()
        
        self.__settings = settings
        
        self.__settings.beginGroup("Output")
        address_layout = QHBoxLayout()
        address_layout.addWidget(QLabel("Address:"))
        self.address_edit = QLineEdit(settings.value("address", "127.0.0.1:5000"))
        address_layout.addWidget(self.address_edit)
        layout.addLayout(address_layout)
        self.__settings.endGroup()

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
        self.__settings.beginGroup("Output")
        self.__settings.setValue("address", self.address_edit.text())
        self.__settings.endGroup()