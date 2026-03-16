from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QGroupBox, QLabel, QSizePolicy, QTableView, QTreeView, QToolButton, QHeaderView, QStyledItemDelegate, QStyleOptionButton, QStyle, QMenu
from PyQt6.QtCore import Qt, QSettings, QRect, QTimer
from PyQt6.QtGui import QIcon, QStandardItemModel, QStandardItem

from core.SettingsManager import SettingsManager
from core.PlaybackController import PlaybackController
from gui.StreamSettingsDialog import StreamSettingsDialog
from gui.VideoSettingsDialog import VideoSettingsDialog
from gui.AudioSettingsDialog import AudioSettingsDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self._settings = SettingsManager()
        self._settings.stream_config_added.connect(self._stream_config_added)
        self._settings.stream_config_changed.connect(self._stream_config_changed)
        self._settings.stream_config_removed.connect(self._stream_config_removed)
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
        self._settings.load_settings()

    def _build_stream_table(self):
        # Build Model
        self.stream_model = QStandardItemModel()
        self.stream_model.setHorizontalHeaderLabels(["Name", "Type", "Frame Rate", "Bit Rate"])

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
        new_stream = menu.addAction("New Stream...")
        new_stream.triggered.connect(self._add_stream_button_clicked)

        if index.isValid():
            index = index.siblingAtColumn(1)
            item = self.stream_model.itemFromIndex(index)

            index = index.siblingAtColumn(0)
            data_index = self.stream_model.itemFromIndex(index).data(Qt.ItemDataRole.UserRole)

            if item.text() == "Stream":
                edit_stream = menu.addAction("Edit Stream...")
                remove_stream = menu.addAction("Remove Stream")
                menu.addSeparator()
                new_video = menu.addAction("New Video Source...")
                new_audio = menu.addAction("New Audio Source...")

                edit_stream.triggered.connect(lambda clicked: self._edit_stream_button_clicked(data_index, clicked))
                remove_stream.triggered.connect(lambda clicked: self._remove_stream_button_clicked(data_index, clicked))
                new_video.triggered.connect(lambda clicked: self._add_video_button_clicked(data_index, clicked))
                new_audio.triggered.connect(lambda clicked: self._add_audio_button_clicked(data_index, clicked))
            if item.text() == "Video":
                menu.addSeparator()
                edit = menu.addAction("Edit Video Source...")
                remove = menu.addAction("Remove Video Source")

                edit.triggered.connect(lambda clicked: self._edit_video_button_clicked(data_index, clicked))
                remove.triggered.connect(lambda clicked: self._remove_video_button_clicked(data_index, clicked))
            if item.text() == "Audio":
                menu.addSeparator()
                edit = menu.addAction("Edit Audio Source...")
                remove = menu.addAction("Remove Audio Source")

                edit.triggered.connect(lambda clicked: self._edit_audio_button_clicked(data_index, clicked))
                remove.triggered.connect(lambda clicked: self._remove_audio_button_clicked(data_index, clicked))
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

    def __create_base_row(self, name, type, enabled = True):
        # Populate Model
        row = [
            QStandardItem(name),
            QStandardItem(type)
        ]
        row[0].setCheckable(True)
        row[0].setCheckState(Qt.CheckState.Checked if enabled else Qt.CheckState.Unchecked)

        return row

    def _stream_config_added(self, index, config):
        # Build Row
        row = self.__create_base_row(config["name"], "Stream", config["enabled"])
        row.append(QStandardItem("0.0 FPS"))
        row.append(QStandardItem("0.00 kb/s"))

        # Populate Model
        self.stream_model.appendRow(row)

        # Store for use by video/audio sources
        config["display_item"] = row[0]
        row[0].setData(config["index"], Qt.ItemDataRole.UserRole)

        return row

    def _stream_config_changed(self, index, config):
        item = config["display_item"]
        item.setText(config.get("name"))

    def _stream_config_removed(self, index, config):
        self.stream_model.removeRow(config["display_item"].row())

    def _add_stream_button_clicked(self, clicked):
        dialog = StreamSettingsDialog(self._settings, self, -1)
        dialog.exec()

    def _remove_stream_button_clicked(self, index, clicked):
        self._settings.remove_stream_config(index)

    def _edit_stream_button_clicked(self, index, clicked):
        dialog = StreamSettingsDialog(self._settings, self, index)
        dialog.exec()

    def _video_config_added(self, index, config):
        # Build Row
        row = self.__create_base_row(config["name"], "Video", config["enabled"])

        # Populate Model
        stream_item = config["stream"]["display_item"]
        item = stream_item.appendRow(row)
        row_index = self.stream_model.indexFromItem(stream_item)
        self.stream_table.expand(row_index)

        # Store for use by streams
        config["display_item"] = row[0]
        row[0].setData(config["index"], Qt.ItemDataRole.UserRole)

        # Handle connecting to playback after current signal has been handled because
        # playback source hasn't been created yet.
        QTimer.singleShot(0, lambda: self.__video_config_added_playback(index))

    def __video_config_added_playback(self, index):
        source = self._playback.video_source(index)
        source.fps.connect(lambda fps, i=index: self._fps_updated(i, fps))
        source.bitrate.connect(lambda bitrate, i=index: self._video_bitrate_updated(i, bitrate))

    def _video_config_changed(self, index, video_config):
        item = video_config["display_item"]
        item.setText(video_config.get("name"))

    def _video_config_removed(self, index, config):
        config["stream"]["display_item"].removeRow(config["display_item"].row())

    def _add_video_button_clicked(self, stream_index, clicked):
        dialog = VideoSettingsDialog(self._settings, self, self._settings.get_stream_config(stream_index))
        dialog.exec()

    def _remove_video_button_clicked(self, index, clicked):
        self._settings.remove_video_config(index)

    def _edit_video_button_clicked(self, index, clicked):
        dialog = VideoSettingsDialog(self._settings, self, index)
        dialog.exec()

    def _audio_config_added(self, index, config):
        # Build Row
        row = self.__create_base_row(config["name"], "Audio", config["enabled"])

        # Populate Model
        stream_item = config["stream"]["display_item"]
        item = stream_item.appendRow(row)
        row_index = self.stream_model.indexFromItem(stream_item)
        self.stream_table.expand(row_index)

        # Store for use by streams
        config["display_item"] = row[0]
        row[0].setData(config["index"], Qt.ItemDataRole.UserRole)

        # Handle connecting to playback after current signal has been handled because
        # playback source hasn't been created yet.
        QTimer.singleShot(0, lambda: self.__audio_config_added_playback(index))

    def __audio_config_added_playback(self, index):
        source = self._playback.audio_source(index)
        source.bitrate.connect(lambda bitrate, i=index: self._audio_bitrate_updated(i, bitrate))

    def _audio_config_changed(self, index, config):
        item = config["display_item"]
        item.setText(config.get("name"))

    def _audio_config_removed(self, index, config):
        config["stream"]["display_item"].removeRow(config["display_item"].row())

    def _add_audio_button_clicked(self, stream_index, clicked):
        dialog = AudioSettingsDialog(self._settings, self, self._settings.get_stream_config(stream_index))
        dialog.exec()

    def _remove_audio_button_clicked(self, index, clicked):
        self._settings.remove_audio_config(index)

    def _edit_audio_button_clicked(self, index, clicked):
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