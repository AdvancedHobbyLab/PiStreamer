from PyQt5.QtWidgets import QApplication
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QGroupBox, QLabel, QSizePolicy, QTableView, QToolButton, QHeaderView, QStyledItemDelegate, QStyleOptionButton, QStyle
from PyQt6.QtCore import Qt, QSettings, QRect
from PyQt6.QtGui import QIcon, QStandardItemModel, QStandardItem

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

        # Layout
        layout = QVBoxLayout()

        layout.addWidget(self._build_video_table())
        layout.addWidget(self._build_audio_table())
        layout.addLayout(self._build_button_box())
        
        # Layout
        central_widget.setLayout(layout)

    def __build_source_table(self, name, model):
        box = QGroupBox(name)
        box.setMinimumWidth(500)

        # Layout
        layout = QVBoxLayout()

        # QTableView
        table = QTableView()
        table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        table.setEditTriggers(table.EditTrigger.NoEditTriggers)
        table.setModel(model)

        table.setSelectionBehavior(table.SelectionBehavior.SelectRows)
        table.setSelectionMode(table.SelectionMode.SingleSelection)
        table.setAlternatingRowColors(True)
        layout.addWidget(table)

        # Set Header Column Behavior
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        if model.columnCount() == 3:
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
            table.setColumnWidth(2, 200)
        else:
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
            table.setColumnWidth(2, 120)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
            table.setColumnWidth(3, 200)

        # Vertical Header
        table.verticalHeader().setVisible(False)

        # Button Box
        button_layout = QHBoxLayout()
        add_button = QPushButton("Add")
        add_button.setToolTip("Add")

        remove_button = QPushButton("Remove")
        remove_button.setToolTip("Remove")
        remove_button.setEnabled(False)

        edit_button = QPushButton("Edit")
        edit_button.setToolTip("Edit")
        edit_button.setEnabled(False)

        for btn in (add_button, remove_button, edit_button):
            btn.setStyleSheet("""
                font-size: 18px;
                padding: 10px;
            """)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            button_layout.addWidget(btn)

        # Finalize
        layout.addLayout(button_layout)
        box.setLayout(layout)

        return box, table, add_button, remove_button, edit_button

    def _build_video_table(self):
        # Build Model
        eye_icon = QIcon.fromTheme("view-visible")

        self.video_model = QStandardItemModel()
        self.video_model.setHorizontalHeaderLabels(["", "Name", "Frame Rate", "Bit Rate"])
        self.video_model.setHeaderData(0, Qt.Orientation.Horizontal, eye_icon, Qt.ItemDataRole.DecorationRole)

        # Populate Model
        check_box = QStandardItem()
        check_box.setEditable(True)
        check_box.setCheckable(True)
        check_box.setCheckState(Qt.CheckState.Checked)
        check_box.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self.video_model.appendRow([
            check_box,
            QStandardItem("HDMI"),
            QStandardItem("60.0 FPS"),
            QStandardItem("18345.12 kbps"),
        ])

        # Build Table
        layout, table, add_button, remove_button, edit_button = self.__build_source_table("Video Sources", self.video_model)

        self.video_table = table
        self.video_table.selectionModel().selectionChanged.connect(self._video_selection_changed)
        self.video_add = add_button
        self.video_remove = remove_button
        self.video_edit = edit_button

        return layout

    def _build_audio_table(self):
        # Build Model
        eye_icon = QIcon.fromTheme("view-visible")

        self.audio_model = QStandardItemModel()
        self.audio_model.setHorizontalHeaderLabels(["", "Name", "Bit Rate"])
        self.audio_model.setHeaderData(0, Qt.Orientation.Horizontal, eye_icon, Qt.ItemDataRole.DecorationRole)

        # Populate Model
        check_box = QStandardItem()
        check_box.setEditable(True)
        check_box.setCheckable(True)
        check_box.setCheckState(Qt.CheckState.Checked)
        check_box.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self.audio_model.appendRow([
            check_box,
            QStandardItem("HDMI"),
            QStandardItem("45.12 kbps"),
        ])

        # Build Table
        layout, table, add_button, remove_button, edit_button = self.__build_source_table("Audio Sources", self.audio_model)

        self.audio_table = table
        self.audio_table.selectionModel().selectionChanged.connect(self._audio_selection_changed)
        self.audio_add = add_button
        self.audio_remove = remove_button
        self.audio_edit = edit_button

        return layout

    def _build_button_box(self):
        layout = QHBoxLayout()

        # Start Button
        self.__start_button = QPushButton("Start")
        self.__start_button.setStyleSheet("background-color: green;")
        self.__start_button.clicked.connect(self._start_button_clicked)
        layout.addWidget(self.__start_button)

        # Exit Button
        self.__exit_button = QPushButton("Exit")
        self.__exit_button.clicked.connect(self._exit_button_clicked)
        layout.addWidget(self.__exit_button)

        return layout

    def _video_selection_changed(self, selected, deselected):
        self.video_edit.setEnabled(True)
        self.video_remove.setEnabled(True)

    def _audio_selection_changed(self, selected, deselected):
        self.audio_edit.setEnabled(True)
        self.audio_remove.setEnabled(True)

    def _start_button_clicked(self, clicked):
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
            self.__start_button.setText("Stop")
            self.__start_button.setStyleSheet("background-color: red;")
        else:
            self.__start_button.setText("Start")
            self.__start_button.setStyleSheet("background-color: green;")