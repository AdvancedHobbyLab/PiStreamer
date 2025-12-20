
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QGroupBox, QLabel, QSizePolicy
from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QIcon
from core.PlaybackController import PlaybackController
from gui.SettingsDialog import SettingsDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self._settings = QSettings("AHL", "PiStreamer")
        
        self._playback = PlaybackController(self._settings)
        self._playback.state_change.connect(self.__playback_state_change)
        
        self.setWindowTitle("Pi Streamer")
        
        # Set Window Icon
        icon = QIcon.fromTheme(
            "com.ahl.pistreamer",
            QIcon("./icon.svg")
        )
        if not icon.isNull():
            self.setWindowIcon(icon)
        else:
            print("Unable to find window icon.")
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Button layout
        button_layout = QVBoxLayout()
        button_widget = QWidget()
        button_widget.setMinimumWidth(300)
        button_widget.setLayout(button_layout)
        button_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Record Button
        self.__record_button = QPushButton("Start")
        self.__record_button.setStyleSheet("background-color: green;")
        self.__record_button.clicked.connect(self._record_button_clicked)
        
        # Settings Button
        self.__settings_button = QPushButton("Settings")
        self.__settings_button.clicked.connect(self._settings_button_clicked)
        
        # Exit Button
        self.__exit_button = QPushButton("Exit")
        self.__exit_button.clicked.connect(self._exit_button_clicked)
        
        for btn in (self.__record_button, self.__settings_button, self.__exit_button):
            btn.setStyleSheet("""
                font-size: 18px;
                padding: 10px;
            """)
            btn.setSizePolicy(
                QSizePolicy.Policy.Expanding,   # respects minimum size
                QSizePolicy.Policy.Fixed
            )
            button_layout.addWidget(btn)
            
        self.__record_button.setStyleSheet("background-color: green;")
        
        # Info Area
        info = QGroupBox("Info")
        info.setFixedWidth(200)
        info_layout = QGridLayout()
        info_layout.setColumnStretch(0, 0)
        info_layout.setColumnStretch(1, 1)
        vbox = QVBoxLayout()
        vbox.addLayout(info_layout)
        vbox.addStretch(1)
        info.setLayout(vbox)
        
        info_layout.addWidget(QLabel("Frame: "), 0, 0)
        info_layout.addWidget(QLabel("FPS: "), 1, 0)
        info_layout.addWidget(QLabel("BitRate: "), 2, 0)
        
        self.__frame_label = QLabel("0")
        info_layout.addWidget(self.__frame_label, 0, 1)
        self._playback.frame.connect(lambda t: self.__frame_label.setText(str(t)))
        
        self.__fps_label = QLabel("0.0")
        info_layout.addWidget(self.__fps_label, 1, 1)
        self._playback.fps.connect(lambda t: self.__fps_label.setText(str(t)))
        
        self.__bitrate_label = QLabel("0.0")
        info_layout.addWidget(self.__bitrate_label, 2, 1)
        self._playback.bitrate.connect(lambda t: self.__bitrate_label.setText(str(t)+"kbits/s"))
        
        layout = QHBoxLayout()
        layout.addWidget(info)
        layout.addWidget(button_widget)
        layout.setStretch(0, 0); # Prevent info area from stretching
        layout.setStretch(1, 1); # Allow the buttons to stretch
        
        # Layout
        central_widget.setLayout(layout)
        
        
    def _record_button_clicked(self, clicked):
        if self._playback.state():
            self._playback.stop_playback()
        else:
            self._playback.start_playback()
    
    def _settings_button_clicked(self, clicked):
        dialog = SettingsDialog(self._settings, self)
        dialog.exec()
    
    def _exit_button_clicked(self, clicked):
        self.close()
    
    def __playback_state_change(self, state):
        if state:
            self.__record_button.setText("Stop")
            self.__record_button.setStyleSheet("background-color: red;")
        else:
            self.__record_button.setText("Start")
            self.__record_button.setStyleSheet("background-color: green;")