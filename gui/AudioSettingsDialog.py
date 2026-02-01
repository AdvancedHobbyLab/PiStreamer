from PyQt6.QtWidgets import (
    QApplication, QDialog, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QCheckBox, QPushButton, QTabWidget, QComboBox, QSpinBox,
    QSizePolicy
)
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt, QSettings

from core.PlaybackOptions import PlaybackOptions

class AudioSettingsDialog(QDialog):
    def __init__(self, settings, parent, index):
        super().__init__(parent)

        self.__settings = settings
        self.__index = index

        self.setWindowTitle("Audio Settings")

        self.options = PlaybackOptions()


        layout = QVBoxLayout()

        grid_layout = QGridLayout()

        config = {}
        if self.__index >= 0:
            config = self.__settings.get_audio_config(self.__index)

        grid_layout.addWidget(QLabel("Name:"), 0, 0)
        self.name_edit = QLineEdit(config.get("name", "Default"))
        grid_layout.addWidget(self.name_edit, 0, 1)

        devices = self.options.GetAudioDevices()
        grid_layout.addWidget(QLabel("Device:"), 1, 0)
        self.device = QComboBox()
        self.device.setModel(devices)
        self.device.currentIndexChanged.connect(self.__device_changed)
        grid_layout.addWidget(self.device, 1, 1)

        grid_layout.addWidget(QLabel("Format:"), 2, 0)
        self.format = QComboBox()
        grid_layout.addWidget(self.format, 2, 1)

        grid_layout.addWidget(QLabel("Channels:"), 3, 0)
        self.channels = QComboBox()
        grid_layout.addWidget(self.channels, 3, 1)

        model = QStandardItemModel()
        item = QStandardItem("opus")
        item.setData("opus", Qt.ItemDataRole.UserRole)
        model.appendRow(item)

        grid_layout.addWidget(QLabel("Encoder:"), 4, 0)
        self.encoder = QComboBox()
        self.encoder.setModel(model)
        grid_layout.addWidget(self.encoder, 4, 1)

        grid_layout.addWidget(QLabel("Address:"), 5, 0)
        self.address_edit = QLineEdit(config.get("address", "udp://127.0.0.1:5000"))
        grid_layout.addWidget(self.address_edit, 5, 1)

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

        # Initialize
        dev_name = config.get("device", "hw:2,0")
        for row in range(devices.rowCount()):
            item = devices.item(row)
            if item.data(Qt.ItemDataRole.UserRole) == dev_name:
                self.device.setCurrentIndex(row)
                self.__device_changed(row)
                break

        format = config.get("format", "S16LE")
        format_model = self.format.model()
        for row in range(format_model.rowCount()):
            item = format_model.item(row)
            if item.data(Qt.ItemDataRole.UserRole) == format:
                self.format.setCurrentIndex(row)
                break

        channel = config.get("channels", "1")
        channel_model = self.channels.model()
        for row in range(channel_model.rowCount()):
            item = channel_model.item(row)
            if item.data(Qt.ItemDataRole.UserRole) == channel:
                self.channels.setCurrentIndex(row)
                break

    def __device_changed(self, row):
        formats = self.options.GetAudioFormats(self.device.currentData())
        self.format.setModel(formats)

        channels = self.options.GetAudioChannels(self.device.currentData())
        self.channels.setModel(channels)

    def __save_clicked(self):
        config = {"name": self.name_edit.text()}
        config["device"] = self.device.currentData()
        config["format"] = self.format.currentData()
        config["channels"] = self.channels.currentData()
        config["encoder"] = self.encoder.currentData()
        config["address"] = self.address_edit.text()

        if self.__index >= 0:
            self.__settings.update_audio_config(self.__index, config)
        else:
            self.__settings.add_audio_config(config)