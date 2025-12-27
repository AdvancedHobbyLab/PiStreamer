from PyQt5.QtWidgets import QApplication
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QGroupBox, QLabel, QSizePolicy, QTableView, QToolButton, QHeaderView, QStyledItemDelegate, QStyleOptionButton, QStyle
from PyQt6.QtCore import Qt, QSettings, QRect, QTimer
from PyQt6.QtGui import QIcon, QStandardItemModel, QStandardItem

from core.SettingsManager import SettingsManager
from core.PlaybackController import PlaybackController
from gui.VideoSettingsDialog import VideoSettingsDialog
from gui.AudioSettingsDialog import AudioSettingsDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self._settings = SettingsManager()
        self._settings.video_config_added.connect(self._video_config_added)
        self._settings.video_config_changed.connect(self._video_config_changed)
        self._settings.video_config_removed.connect(self._video_config_removed)
        self._settings.audio_config_added.connect(self._audio_config_added)
        self._settings.audio_config_changed.connect(self._audio_config_changed)
        self._settings.audio_config_removed.connect(self._audio_config_removed)

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

        # Initialize
        for i in range(self._settings.num_video_configs()):
            config = self._settings.get_video_config(i)
            self._video_config_added(i, config)

        for i in range(self._settings.num_audio_configs()):
            config = self._settings.get_audio_config(i)
            self._audio_config_added(i, config)

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

        # Build Table
        layout, table, add_button, remove_button, edit_button = self.__build_source_table("Video Sources", self.video_model)

        self.video_table = table
        self.video_table.selectionModel().selectionChanged.connect(self._video_selection_changed)
        self.video_add = add_button
        self.video_add.clicked.connect(self._add_video_button_clicked)
        self.video_remove = remove_button
        self.video_remove.clicked.connect(self._remove_video_button_clicked)
        self.video_edit = edit_button
        self.video_edit.clicked.connect(self._edit_video_button_clicked)

        return layout

    def _build_audio_table(self):
        # Build Model
        eye_icon = QIcon.fromTheme("view-visible")

        self.audio_model = QStandardItemModel()
        self.audio_model.setHorizontalHeaderLabels(["", "Name", "Bit Rate"])
        self.audio_model.setHeaderData(0, Qt.Orientation.Horizontal, eye_icon, Qt.ItemDataRole.DecorationRole)

        # Build Table
        layout, table, add_button, remove_button, edit_button = self.__build_source_table("Audio Sources", self.audio_model)

        self.audio_table = table
        self.audio_table.selectionModel().selectionChanged.connect(self._audio_selection_changed)
        self.audio_add = add_button
        self.audio_add.clicked.connect(self._add_audio_button_clicked)
        self.audio_remove = remove_button
        self.audio_remove.clicked.connect(self._remove_audio_button_clicked)
        self.audio_edit = edit_button
        self.audio_edit.clicked.connect(self._edit_audio_button_clicked)

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

    def _video_config_added(self, index, video_config):
        # Populate Model
        check_box = QStandardItem()
        check_box.setEditable(True)
        check_box.setCheckable(True)
        check_box.setCheckState(Qt.CheckState.Checked)
        check_box.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self.video_model.appendRow([
            check_box,
            QStandardItem(video_config.get("name")),
            QStandardItem("0.0 FPS"),
            QStandardItem("0.00 kb/s"),
        ])

        # Handle connecting to playback after current signal has been handled because
        # playback source hasn't been created yet.
        QTimer.singleShot(0, lambda: self.__video_config_added_playback(index))

    def __video_config_added_playback(self, index):
        source = self._playback.video_source(index)
        source.fps.connect(lambda fps, i=index: self._fps_updated(i, fps))
        source.bitrate.connect(lambda bitrate, i=index: self._video_bitrate_updated(i, bitrate))

    def _video_config_changed(self, index, video_config):
        item = self.video_model.item(index, 1)
        item.setText(video_config.get("name"))

    def _video_config_removed(self, index):
        self.video_model.removeRow(index)

    def _add_video_button_clicked(self, clicked):
        dialog = VideoSettingsDialog(self._settings, self, -1)
        dialog.exec()

    def _remove_video_button_clicked(self, clicked):
        index = self.video_table.selectionModel().currentIndex().row()
        self._settings.remove_video_config(index)

    def _edit_video_button_clicked(self, clicked):
        index = self.video_table.selectionModel().currentIndex().row()
        dialog = VideoSettingsDialog(self._settings, self, index)
        dialog.exec()

    def _audio_config_added(self, index, config):
        # Populate Model
        check_box = QStandardItem()
        check_box.setEditable(True)
        check_box.setCheckable(True)
        check_box.setCheckState(Qt.CheckState.Checked)
        check_box.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self.audio_model.appendRow([
            check_box,
            QStandardItem(config.get("name")),
            QStandardItem("0.0 kb/s"),
        ])

        # Handle connecting to playback after current signal has been handled because
        # playback source hasn't been created yet.
        QTimer.singleShot(0, lambda: self.__audio_config_added_playback(index))

    def __audio_config_added_playback(self, index):
        source = self._playback.audio_source(index)
        source.bitrate.connect(lambda bitrate, i=index: self._audio_bitrate_updated(i, bitrate))

    def _audio_config_changed(self, index, config):
        item = self.audio_model.item(index, 1)
        item.setText(config.get("name"))

    def _audio_config_removed(self, index):
        self.audio_model.removeRow(index)

    def _add_audio_button_clicked(self, clicked):
        dialog = AudioSettingsDialog(self._settings, self, -1)
        dialog.exec()

    def _remove_audio_button_clicked(self, clicked):
        index = self.audio_table.selectionModel().currentIndex().row()
        self._settings.remove_audio_config(index)

    def _edit_audio_button_clicked(self, clicked):
        index = self.audio_table.selectionModel().currentIndex().row()
        dialog = AudioSettingsDialog(self._settings, self, index)
        dialog.exec()

    def _fps_updated(self, index, fps):
        item = self.video_model.item(index, 2)
        item.setText(str(fps)+" FPS")

    def _video_bitrate_updated(self, index, bitrate):
        item = self.video_model.item(index, 3)
        item.setText(str(bitrate)+" kb/s")

    def _audio_bitrate_updated(self, index, bitrate):
        item = self.audio_model.item(index, 3)
        item.setText(str(bitrate)+" kb/s")

    def _settings_button_clicked(self, clicked):
        dialog = VideoSettingsDialog(self._settings, self)
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