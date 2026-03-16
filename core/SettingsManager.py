from PyQt6.QtCore import QObject, pyqtSignal, QSettings

class SettingsManager(QObject):
    # Signals
    stream_config_added = pyqtSignal(int, dict)     # index, data
    stream_config_changed = pyqtSignal(int, dict)   # index, data
    stream_config_removed = pyqtSignal(int)         # index

    video_config_added = pyqtSignal(int, dict)      # index, data
    video_config_changed = pyqtSignal(int, dict)    # index, data
    video_config_removed = pyqtSignal(int, dict)    # index, data

    audio_config_added = pyqtSignal(int, dict)      # index, data
    audio_config_changed = pyqtSignal(int, dict)    # index, data
    audio_config_removed = pyqtSignal(int, dict)    # index, data

    def __init__(self):
        super().__init__()

        self._settings = QSettings("AHL", "PiStreamer")

        self.__stream_configs = []
        self.__video_configs = []
        self.__audio_configs = []

    def load_settings(self):
        # Load Configs From Disk
        self.__read_stream_configs()
        self.__read_video_configs()
        self.__read_audio_configs()

        # Notify UI about configs
        for i, stream in enumerate(self.__stream_configs):
            self.stream_config_added.emit(i, stream)
            for vi, video in enumerate(stream["video_configs"]):
                self.video_config_added.emit(vi, video)
            for ai, audio in enumerate(stream["audio_configs"]):
                self.audio_config_added.emit(ai, audio)

    def num_stream_configs(self):
        return len(self.__stream_configs)

    def get_stream_config(self, index):
        return self.__stream_configs[index]

    def add_stream_config(self, data):
        data["index"] = len(self.__stream_configs)
        self.__stream_configs.append(data)

        self.__save_stream_configs()

        self.stream_config_added.emit(len(self.__stream_configs)-1, data)

    def remove_stream_config(self, index):
        self.__stream_configs.pop(index)

        self.__save_stream_configs()

        self.stream_config_removed.emit(index)

    def update_stream_config(self, index, data):
        self.__stream_configs[index] = data

        self.__save_stream_configs()

        self.stream_config_changed.emit(index, data)

    def num_video_configs(self):
        return len(self.__video_configs)

    def get_video_config(self, index):
        return self.__video_configs[index]

    def add_video_config(self, data):
        data["index"] = len(self.__video_configs)
        self.__video_configs.append(data)

        self.__save_video_configs()

        self.video_config_added.emit(len(self.__video_configs)-1, data)

    def remove_video_config(self, index):
        config = self.get_video_config(index)
        self.__video_configs.pop(index)

        self.__save_video_configs()

        self.video_config_removed.emit(index, config)

    def update_video_config(self, index, data):
        self.__video_configs[index] = data

        self.__save_video_configs()

        self.video_config_changed.emit(index, data)

    def num_audio_configs(self):
        return len(self.__audio_configs)

    def get_audio_config(self, index):
        return self.__audio_configs[index]

    def add_audio_config(self, data):
        data["index"] = len(self.__audio_configs)
        self.__audio_configs.append(data)

        self.__save_audio_configs()

        self.audio_config_added.emit(len(self.__audio_configs)-1, data)

    def remove_audio_config(self, index):
        config = self.get_audio_config(index)
        self.__audio_configs.pop(index)

        self.__save_audio_configs()

        self.audio_config_removed.emit(index, config)

    def update_audio_config(self, index, data):
        self.__audio_configs[index] = data

        self.__save_audio_configs()

        self.audio_config_changed.emit(index, data)

    def __read_stream_configs(self):
        size = self._settings.beginReadArray("StreamConfigs")

        self.__stream_configs = []

        for i in range(size):
            config = {}
            self._settings.setArrayIndex(i)
            config["index"] = i
            config["enabled"] = int(self._settings.value("enabled", "1")) > 0
            config["name"] = self._settings.value("name", "Default")
            config["address"] = self._settings.value("address", "udpL//127.0.0.1:5000")
            config["video_configs"] = []
            config["audio_configs"] = []
            self.__stream_configs.append(config)

        self._settings.endArray()

    def __save_stream_configs(self):
        self._settings.beginWriteArray("StreamConfigs")

        for i, config in enumerate(self.__stream_configs):
            self._settings.setArrayIndex(i)
            self._settings.setValue("enabled", "1" if config["enabled"] else "0")
            self._settings.setValue("name", config["name"])
            self._settings.setValue("address", config["address"])

        self._settings.endArray()

    def __read_video_configs(self):
        size = self._settings.beginReadArray("VideoConfigs")

        self.__video_configs = []

        for i in range(size):
            config = {}
            self._settings.setArrayIndex(i)
            config["index"] = i
            config["enabled"] = int(self._settings.value("enabled", "1"))>0
            config["name"] = self._settings.value("name", "Default")
            config["device"] = self._settings.value("device", "/dev/video0")
            config["format"] = self._settings.value("format", "")
            config["width"] = self._settings.value("width", "1920")
            config["height"] = self._settings.value("height", "1080")
            config["framerate"] = self._settings.value("framerate", "60")
            config["encoder"] = self._settings.value("encoder", "copy")
            config["crf"] = self._settings.value("crf", "0")
            stream_index = int(self._settings.value("stream", "-1"))
            if stream_index >= 0 and stream_index < len(self.__stream_configs):
                stream = self.__stream_configs[stream_index]
                config["stream"] = stream
                stream["video_configs"].append(config)
                self.__video_configs.append(config)

        self._settings.endArray()

    def __save_video_configs(self):
        self._settings.beginWriteArray("VideoConfigs")

        for i, config in enumerate(self.__video_configs):
            self._settings.setArrayIndex(i)
            self._settings.setValue("enabled", "1" if config["enabled"] else "0")
            self._settings.setValue("name", config["name"])
            self._settings.setValue("device", config["device"])
            self._settings.setValue("format", config["format"])
            self._settings.setValue("width", config["width"])
            self._settings.setValue("height", config["height"])
            self._settings.setValue("framerate", config["framerate"])
            self._settings.setValue("encoder", config["encoder"])
            self._settings.setValue("crf", config.get("crf", "0"))
            self._settings.setValue("stream", self.__stream_configs.index(config["stream"]))

        self._settings.endArray()

    def __read_audio_configs(self):
        size = self._settings.beginReadArray("AudioConfigs")

        self.__audio_configs = []

        for i in range(size):
            config = {}
            self._settings.setArrayIndex(i)
            config["index"] = i
            config["enabled"] = int(self._settings.value("enabled", "1")) > 0
            config["name"] = self._settings.value("name", "Default")
            config["device"] = self._settings.value("device", "hw:1,0")
            config["format"] = self._settings.value("format", "")
            config["channels"] = self._settings.value("channels", "1")
            config["encoder"] = self._settings.value("encoder", "copy")
            stream_index = int(self._settings.value("stream", "-1"))
            if stream_index >= 0 and stream_index < len(self.__stream_configs):
                stream = self.__stream_configs[stream_index]
                config["stream"] = stream
                stream["audio_configs"].append(config)
                self.__audio_configs.append(config)

        self._settings.endArray()

    def __save_audio_configs(self):
        self._settings.beginWriteArray("AudioConfigs")

        for i, config in enumerate(self.__audio_configs):
            self._settings.setArrayIndex(i)
            self._settings.setValue("enabled", "1" if config["enabled"] else "0")
            self._settings.setValue("name", config["name"])
            self._settings.setValue("device", config["device"])
            self._settings.setValue("format", config["format"])
            self._settings.setValue("channels", config["channels"])
            self._settings.setValue("encoder", config["encoder"])
            self._settings.setValue("stream", self.__stream_configs.index(config["stream"]))

        self._settings.endArray()