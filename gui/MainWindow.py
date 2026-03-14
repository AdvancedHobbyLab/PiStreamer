from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QGroupBox, QLabel, QSizePolicy, QTableView, QTreeView, QToolButton, QHeaderView, QStyledItemDelegate, QStyleOptionButton, QStyle, QMenu
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

        layout.addWidget(self._build_stream_table())
        layout.addLayout(self._build_button_box())
        
        # Layout
        central_widget.setLayout(layout)

        # Initialize
        

    def __build_source_row(self, name, type):
        # Populate Model
        check_box = QStandardItem()
        check_box.setEditable(True)
        check_box.setCheckable(True)
        check_box.setCheckState(Qt.CheckState.Checked)
        check_box.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        row =[
            #check_box,
            QStandardItem(name),
            QStandardItem(type)
        ]
        row[0].setCheckable(True)
        row[0].setCheckState(Qt.CheckState.Checked)
        if type == "Stream":
            row.append(QStandardItem("0.0 FPS"))
            row.append(QStandardItem("0.00 kb/s"))

        return row

    def _build_stream_table(self):
        # Build Model
        self.stream_model = QStandardItemModel()
        self.stream_model.setHorizontalHeaderLabels(["Name", "Type", "Frame Rate", "Bit Rate"])

        stream1 = self.__build_source_row("HDMI Stream", "Stream")
        vid1 = self.__build_source_row("Camera", "Video")
        audio1 = self.__build_source_row("External Mic", "Audio")
        stream1[0].appendRow(vid1)
        stream1[0].appendRow(audio1)
        self.stream_model.appendRow(stream1)

        tree = QTreeView()
        tree.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        tree.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        tree.setEditTriggers(tree.EditTrigger.NoEditTriggers)
        tree.setModel(self.stream_model)
        tree.setMinimumWidth(600)
        self.stream_table = tree

        tree.setSelectionBehavior(tree.SelectionBehavior.SelectRows)
        tree.setSelectionMode(tree.SelectionMode.SingleSelection)
        tree.setAlternatingRowColors(True)

        # Set Header Column Behavior
        header = tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        tree.setColumnWidth(1, 100)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        tree.setColumnWidth(2, 120)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        tree.setColumnWidth(3, 150)
        header.setStretchLastSection(False)

        tree.expandAll()

        tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        tree.customContextMenuRequested.connect(self.__open_context_menu)

        return tree

    def __open_context_menu(self, position):
        index = self.stream_table.indexAt(position)

        menu = QMenu()
        menu.addAction("New Stream...")

        if index.isValid():
            index = index.siblingAtColumn(1)
            item = self.stream_model.itemFromIndex(index)

            if item.text() == "Stream":
                menu.addAction("Remove Stream")
                menu.addSeparator()
                menu.addAction("New Video Source...")
                menu.addAction("New Audio Source...")
            if item.text() == "Video":
                menu.addSeparator()
                menu.addAction("Edit Video Source...")
                menu.addAction("Remove Video Source")
            if item.text() == "Audio":
                menu.addSeparator()
                menu.addAction("Edit Audio Source...")
                menu.addAction("Remove Audio Source")
            menu.addSeparator()

        menu.exec(self.stream_table.viewport().mapToGlobal(position))

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
        item.setText(f"{float(bitrate):.1f} kb/s")

    def _audio_bitrate_updated(self, index, bitrate):
        item = self.audio_model.item(index, 2)
        item.setText(f"{float(bitrate):.2f} kb/s")

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