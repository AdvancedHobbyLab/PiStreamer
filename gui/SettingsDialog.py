from PyQt6.QtWidgets import (
    QApplication, QDialog, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QCheckBox, QPushButton, QTabWidget, QComboBox, QSpinBox
)
from PyQt6.QtCore import Qt, QSettings
from core.PlaybackOptions import PlaybackOptions

import sys

class InputTab(QWidget):
    def __init__(self, options):
        super().__init__()

        self.options = options

        layout = QGridLayout()

        layout.addWidget(QLabel("Device: "), 0, 0)
        self.device = QComboBox()
        self.device.setModel(options.GetDevices())
        self.device.currentIndexChanged.connect(self.__device_changed)
        layout.addWidget(self.device, 0, 1)

        layout.addWidget(QLabel("Format: "), 1, 0)
        self.format = QComboBox()
        layout.addWidget(self.format)

        self.setLayout(layout)

    def __device_changed(self, index):
        device = self.device.model().item(self.device.currentIndex()).data(Qt.ItemDataRole.UserRole)
        model = self.options.GetFormats(device)
        self.format.setModel(model)
        self.format.setModelColumn(2)

    def LoadSettings(self, settings):

        settings.beginGroup("Input")

        device = settings.value("device", "/dev/video0")
        model = self.device.model()
        for row in range(model.rowCount()):
            item = model.item(row)
            if item.data(Qt.ItemDataRole.UserRole) == device:
                self.device.setCurrentIndex(row)
                self.__device_changed(row)
                break

        self.format.setCurrentText(settings.value("format", "rgb24"))

        settings.endGroup()

    def SaveSettings(self, settings):

        settings.beginGroup("Input")

        settings.setValue("device", self.device.currentData())
        settings.setValue("format", self.format.currentText())

        settings.endGroup()

class OutputTab(QWidget):
    def __init__(self, options):
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


class EncoderTab(QWidget):
    def __init__(self, options):
        super().__init__()

        layout = QGridLayout()

        layout.addWidget(QLabel("Encoder: "), 0, 0)
        self.encoder = QComboBox()
        self.encoder.addItems(["copy", "libx264"])
        self.encoder.currentIndexChanged.connect(self.__encoder_changed)
        layout.addWidget(self.encoder, 0, 1)

        self.crf_label = QLabel("CRF: ")
        layout.addWidget(self.crf_label, 1, 0)

        self.crf_edit = QSpinBox()
        self.crf_edit.setMinimum(0)
        self.crf_edit.setMaximum(28)
        layout.addWidget(self.crf_edit, 1, 1)

        self.setLayout(layout)

    def __encoder_changed(self, index):
        encoder = self.encoder.itemText(index)

        enable = encoder == "libx264"
        self.crf_label.setEnabled(enable)
        self.crf_edit.setEnabled(enable)

    def LoadSettings(self, settings):
        settings.beginGroup("Encoder")

        encoder = settings.value("encoder", "libx264")
        self.encoder.setCurrentText(encoder)

        if encoder == "libx264":
            self.crf_edit.setValue(int(settings.value("crf", "0")))

        settings.endGroup()

    def SaveSettings(self, settings):
        settings.beginGroup("Encoder")

        encoder = self.encoder.currentText()
        settings.setValue("encoder", encoder)

        if encoder == "libx264":
            settings.setValue("crf", self.crf_edit.value())

        settings.endGroup()

class SettingsDialog(QDialog):
    def __init__(self, settings, parent):
        super().__init__(parent)

        self.__settings = settings

        self.setWindowTitle("Settings")

        layout = QVBoxLayout()

        options = PlaybackOptions()

        # Setup Tabs
        tabs = QTabWidget()
        self.__tabs = [
            InputTab(options),
            EncoderTab(options),
            OutputTab(options)
        ]
        display_names = ["Input", "Encoder", "Output"]
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