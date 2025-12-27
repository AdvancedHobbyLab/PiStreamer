from PyQt6.QtCore import QObject, pyqtSignal, QSettings

class SettingsManager(QObject):
    # Signals
    video_config_added = pyqtSignal(int, dict)      # index, data
    video_config_changed = pyqtSignal(int, dict)    # index, data
    video_config_removed = pyqtSignal(int)          # index

    audio_config_added = pyqtSignal(int, dict)  # index, data
    audio_config_changed = pyqtSignal(int, dict)  # index, data
    audio_config_removed = pyqtSignal(int)  # index

    def __init__(self):
        super().__init__()

        self._settings = QSettings("AHL", "PiStreamer")

        self.__video_configs = []
        self.__audio_configs = []

        self.__read_video_config()
        self.__read_audio_config()


    def num_video_configs(self):
        return len(self.__video_configs)

    def get_video_config(self, index):
        return self.__video_configs[index]

    def add_video_config(self, data):
        self.__video_configs.append(data)

        self.__save_video_configs()

        self.video_config_added.emit(len(self.__video_configs)-1, data)

    def remove_video_config(self, index):
        self.__video_configs.pop(index)

        self.__save_video_configs()

        self.video_config_removed.emit(index)

    def update_video_config(self, index, data):
        self.__video_configs[index] = data

        self.__save_video_configs()

        self.video_config_changed.emit(index, data)

    def num_audio_configs(self):
        return len(self.__audio_configs)

    def get_audio_config(self, index):
        return self.__audio_configs[index]

    def add_audio_config(self, data):
        self.__audio_configs.append(data)

        self.__save_audio_configs()

        self.audio_config_added.emit(len(self.__audio_configs)-1, data)

    def remove_audio_config(self, index):
        self.__audio_configs.pop(index)

        self.__save_audio_configs()

        self.audio_config_removed.emit(index)

    def update_audio_config(self, index, data):
        self.__audio_configs[index] = data

        self.__save_audio_configs()

        self.audio_config_changed.emit(index, data)

    def __read_video_config(self):
        size = self._settings.beginReadArray("VideoConfigs")

        self.__video_configs = []

        for i in range(size):
            config = {}
            self._settings.setArrayIndex(i)
            config["name"] = self._settings.value("name", "Default")
            config["device"] = self._settings.value("device", "/dev/video0")
            config["format"] = self._settings.value("format", "")
            config["width"] = self._settings.value("width", "1920")
            config["height"] = self._settings.value("height", "1080")
            config["framerate"] = self._settings.value("framerate", "60")
            config["encoder"] = self._settings.value("encoder", "copy")
            config["crf"] = self._settings.value("crf", "0")
            config["address"] = self._settings.value("address", "udp://127.0.0.1:5000")
            self.__video_configs.append(config)

        self._settings.endArray()

    def __save_video_configs(self):
        self._settings.beginWriteArray("VideoConfigs")

        for i, config in enumerate(self.__video_configs):
            self._settings.setArrayIndex(i)
            self._settings.setValue("name", config["name"])
            self._settings.setValue("device", config["device"])
            self._settings.setValue("format", config["format"])
            self._settings.setValue("width", config["width"])
            self._settings.setValue("height", config["height"])
            self._settings.setValue("framerate", config["framerate"])
            self._settings.setValue("encoder", config["encoder"])
            self._settings.setValue("crf", config.get("crf", "0"))
            self._settings.setValue("address", config["address"])

        self._settings.endArray()

    def __read_audio_config(self):
        size = self._settings.beginReadArray("AudioConfigs")

        self.__audio_configs = []

        for i in range(size):
            config = {}
            self._settings.setArrayIndex(i)
            config["name"] = self._settings.value("name", "Default")
            config["device"] = self._settings.value("device", "hw:1,0")
            config["format"] = self._settings.value("format", "")
            config["encoder"] = self._settings.value("encoder", "copy")
            config["address"] = self._settings.value("address", "udp://127.0.0.1:5000")
            self.__audio_configs.append(config)

        self._settings.endArray()

    def __save_audio_configs(self):
        self._settings.beginWriteArray("AudioConfigs")

        for i, config in enumerate(self.__audio_configs):
            self._settings.setArrayIndex(i)
            self._settings.setValue("name", config["name"])
            self._settings.setValue("device", config["device"])
            self._settings.setValue("format", config["format"])
            self._settings.setValue("encoder", config["encoder"])
            self._settings.setValue("address", config["address"])

        self._settings.endArray()