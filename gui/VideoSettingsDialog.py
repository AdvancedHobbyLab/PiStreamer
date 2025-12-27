from PyQt6.QtWidgets import (
    QApplication, QDialog, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QCheckBox, QPushButton, QTabWidget, QComboBox, QSpinBox,
    QSizePolicy
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
        layout.addWidget(self.format, 1, 1)

        layout.addWidget(QLabel("Resolution: "), 2, 0)
        self.resolution_width = QSpinBox()
        self.resolution_width.setMinimum(720)
        self.resolution_width.setMaximum(4096)
        self.resolution_height = QSpinBox()
        self.resolution_height.setMinimum(480)
        self.resolution_height.setMaximum(2400)
        resolution_layout = QHBoxLayout()
        resolution_layout.addWidget(QLabel("Width: "), 0)
        resolution_layout.addWidget(self.resolution_width, 1)
        resolution_layout.addWidget(QLabel("Height: "), 0)
        resolution_layout.addWidget(self.resolution_height, 1)
        layout.addLayout(resolution_layout, 2, 1)

        layout.addWidget(QLabel("Framerate: "), 3, 0)
        self.framerate = QSpinBox()
        self.framerate.setMinimum(10)
        self.framerate.setMaximum(120)
        layout.addWidget(self.framerate, 3, 1)

        layout.setRowStretch(4, 1)
        self.setLayout(layout)

    def __device_changed(self, index):
        device = self.device.model().item(self.device.currentIndex()).data(Qt.ItemDataRole.UserRole)
        model = self.options.GetFormats(device)
        self.format.setModel(model)
        self.format.setModelColumn(2)

    def LoadSettings(self, config):
        device = config.get("device", "/dev/video0")
        model = self.device.model()
        for row in range(model.rowCount()):
            item = model.item(row)
            if item.data(Qt.ItemDataRole.UserRole) == device:
                self.device.setCurrentIndex(row)
                self.__device_changed(row)
                break

        format = config.get("format", "rgb24")
        model = self.format.model()
        for row in range(model.rowCount()):
            item = model.item(row, 1)
            if item.text() == format:
                self.format.setCurrentIndex(row)
                break

        width = config.get("width", 1920)
        self.resolution_width.setValue(int(width))

        height = config.get("height", 1080)
        self.resolution_height.setValue(int(height))

        framerate = config.get("framerate", 60)
        self.framerate.setValue(int(framerate))

    def GetSettings(self):
        return {
            "device": self.device.currentData(),
            "format": self.format.model().item(self.format.currentIndex(), 1).text(),
            "width": self.resolution_width.value(),
            "height": self.resolution_height.value(),
            "framerate": self.framerate.value()
        }

class OutputTab(QWidget):
    def __init__(self, options):
        super().__init__()

        layout = QVBoxLayout()
        address_layout = QHBoxLayout()
        layout.addLayout(address_layout)

        address_layout.addWidget(QLabel("Address:"))
        self.address_edit = QLineEdit()
        address_layout.addWidget(self.address_edit)

        layout.addWidget(QLabel("Ex. udp://<remote_address>:5000"))

        layout.addStretch()
        self.setLayout(layout)

    def LoadSettings(self, config):
        self.address_edit.setText(config.get("address", "127.0.0.1:5000"))

    def GetSettings(self):
        return {"address": self.address_edit.text()}


class EncoderTab(QWidget):
    def __init__(self, options):
        super().__init__()

        layout = QGridLayout()
        layout.setColumnStretch(0, 0)
        layout.setColumnStretch(1, 1)

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

        layout.setRowStretch(2, 1)
        self.setLayout(layout)

    def __encoder_changed(self, index):
        encoder = self.encoder.itemText(index)

        enable = encoder == "libx264"
        self.crf_label.setEnabled(enable)
        self.crf_edit.setEnabled(enable)

    def LoadSettings(self, config):
        encoder = config.get("encoder", "libx264")
        self.encoder.setCurrentText(encoder)

        if encoder == "libx264":
            self.crf_edit.setValue(int(config.get("crf", "0")))

    def GetSettings(self):
        config = {}

        encoder = self.encoder.currentText()
        config["encoder"] = encoder

        if encoder == "libx264":
            config["crf"] = self.crf_edit.value()

        return config

class VideoSettingsDialog(QDialog):
    def __init__(self, settings, parent, index):
        super().__init__(parent)

        self.__settings = settings
        self.__index = index

        self.setWindowTitle("Video Settings")

        layout = QVBoxLayout()

        options = PlaybackOptions()

        # Add Name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        self.name_edit = QLineEdit("Default")
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)

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

        config = {}
        if index >= 0:
            config = self.__settings.get_video_config(self.__index)

        self.name_edit.setText(config.get("name", "Default"))
        for tab in self.__tabs:
            tab.LoadSettings(config)

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
        config = {"name": self.name_edit.text()}
        for tab in self.__tabs:
            config.update(tab.GetSettings())

        print("Save: ", config)
        if self.__index >= 0:
            self.__settings.update_video_config(self.__index, config)
        else:
            self.__settings.add_video_config(config)