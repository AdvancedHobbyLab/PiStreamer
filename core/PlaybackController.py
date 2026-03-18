
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QProcess, QSettings, QTimer
import re
from urllib.parse import urlparse

class PlaybackStream(QObject):
    # Signals
    state_change = pyqtSignal(bool)
    frame = pyqtSignal(int)
    fps = pyqtSignal(float)
    bitrate = pyqtSignal(float)

    def __init__(self, config):
        super().__init__()

        self.__process = QProcess(self)
        self.__process.readyReadStandardOutput.connect(self.__handle_output)
        self.__process.readyReadStandardError.connect(self.__handle_error)
        self.__process.stateChanged.connect(self.__state_changed)
        self.__process.finished.connect(self.__clean_up)

        self.__config = config

    def state(self):
        return self.__process.state()

    def start_playback(self):
        print("Starting Stream:", self.__config.get("name", "Unknown"))

        # Don't start if not enabled
        if not self.__config["enabled"]:
            print("Stream disabled")
            self.state_change.emit(False)
            return

        # Check process state
        if self.__process.state() != QProcess.ProcessState.NotRunning:
            print("Process already running")
            self.state_change.emit(False)
            return

        command = ["ffmpeg"] + self.__build_command_string()

        print("Running: " + " ".join(command))
        self.__process.start(command[0], command[1:])

    def stop_playback(self):
        # Check process state
        if self.__process.state() == QProcess.ProcessState.NotRunning:
            return

        # Works for streaming since files don't need to be finalized
        self.__process.terminate()

    def __state_changed(self, new_state):
        if new_state == QProcess.ProcessState.NotRunning:
            self.state_change.emit(False)
        else:
            self.state_change.emit(True)

    @pyqtSlot()
    def __handle_output(self):
        data = self.__process.readAllStandardOutput().data().decode("utf-8")

    @pyqtSlot()
    def __handle_error(self):
        data = self.__process.readAllStandardError().data().decode("utf-8")

        # Use regex to extract FPS, frame count, bitrate
        fps_match = re.search(r'fps=\s*([\d\.]+)', data)
        frame_match = re.search(r'frame=\s*(\d+)', data)
        bitrate_match = re.search(r'bitrate=\s*([\d\.]+\w+)', data)

        if fps_match:
            self.fps.emit(float(fps_match.group(1)))
        if frame_match:
            self.frame.emit(int(frame_match.group(1)))
        if bitrate_match:
            clean = re.sub(r"[^0-9.]+$", "", bitrate_match.group(1))
            self.bitrate.emit(float(clean))

    def __clean_up(self):
        self.frame.emit(0)
        self.fps.emit(0)
        self.bitrate.emit(0)

    def __build_command_string(self):
        cmd = []
        for audio in self.__config["audio_configs"]:
            if audio["enabled"]:
                cmd += self.__build_audio_source_string(audio)

        for video in self.__config["video_configs"]:
            if video["enabled"]:
                cmd += self.__build_video_source_string(video)

        for audio in self.__config["audio_configs"]:
            if audio["enabled"]:
                cmd += self.__build_audio_encoder_string(audio)

        for video in self.__config["video_configs"]:
            if video["enabled"]:
                cmd += self.__build_video_encoder_string(video)

        # Output Options
        output_address = self.__config["address"]

        # TODO - add controls for settings the muxer
        muxer = "mpegts"
        #if format == "mjpeg" and encoder == "copy":
        #    muxer = "mjpeg"

        output_options = [
            "-f",
            muxer,
            output_address
        ]
        cmd += output_options

        return cmd

    def __build_video_source_string(self, config):
        # Input options
        device = config["device"]
        format = config["format"]
        resolution = str(config["width"]) + "x" + \
                     str(config["height"])
        framerate = str(config["framerate"])
        input_options = [
            "-thread_queue_size", "512",
            "-f", "v4l2",
            "-input_format", format,
            "-video_size", resolution,
            "-framerate", framerate,
            "-i", device,
            "-r", framerate,
        ]
        return input_options

    def __build_video_encoder_string(self, config):
        # Encoder Options
        encoder = config["encoder"]
        encoder_options = ["-c:v", encoder]
        if encoder == "libx264":
            encoder_options += [
                "-preset", "superfast",
                "-tune", "zerolatency",
                "-crf", str(config["crf"]),
                "-pix_fmt", "yuv420p"
            ]
        return encoder_options

    def __build_audio_source_string(self, config):
        audio_options = [
            "-thread_queue_size", "512",
            "-f", "alsa",
            "-ac", config["channels"],
            "-ar", "48000",
            "-i", "plug"+config["device"],
        ]
        return audio_options

    def __build_audio_encoder_string(self, config):
        audio_options = [
            "-c:a", "libopus",
            "-b:a", "128k",
            "-application", "audio",
            "-frame_duration", "20",
            "-async", "1"
        ]
        return audio_options


class PlaybackController(QObject):
    
    # Signals
    state_change = pyqtSignal(bool)
    bitrate = pyqtSignal(float)
    
    def __init__(self, settings):
        super().__init__()
        
        self.__settings = settings
        self.__settings.stream_config_added.connect(self.__stream_config_added)
        self.__settings.stream_config_changed.connect(self.__stream_config_changed)
        self.__settings.stream_config_removed.connect(self.__stream_config_removed)
        
        self.__streams = []

        self.__state = False

    def num_streams(self):
        return len(self.__streams)

    def get_stream(self, index):
        return self.__streams[index]
        
    @pyqtSlot()
    def start_playback(self):
        print()
        print("Start Playback...")
        self.__state = True
        self.state_change.emit(True)
        for stream in self.__streams:
            print()
            stream.start_playback()
    
    @pyqtSlot()
    def stop_playback(self):
        print("Stop Playback...")
        for stream in self.__streams:
            stream.stop_playback()
        
    # Return True if running else False
    def state(self):
        return self.__state
        
    def __state_changed(self, new_state):
        # Get State
        final_state = False
        for stream in self.__streams:
            state = stream.state()
            if state != QProcess.ProcessState.NotRunning:
                final_state = True

        # Update State
        if final_state != self.__state:
            self.__state = final_state
            self.state_change.emit(self.__state)
        
    @pyqtSlot()
    def __handle_output(self):
        data = self.__process.readAllStandardOutput().data().decode("utf-8")
        
    @pyqtSlot()
    def __handle_error(self):
        data = self.__process.readAllStandardError().data().decode("utf-8")

        # Use regex to extract FPS, frame count, bitrate
        fps_match = re.search(r'fps=\s*([\d\.]+)', data)
        frame_match = re.search(r'frame=\s*(\d+)', data)
        bitrate_match = re.search(r'bitrate=\s*([\d\.]+\w+)', data)

        if fps_match:
            self.fps.emit(float(fps_match.group(1)))
        if frame_match:
            self.frame.emit(int(frame_match.group(1)))
        if bitrate_match:
            clean = re.sub(r"[^0-9.]+$", "", bitrate_match.group(1))
            self.bitrate.emit(float(clean))

    def __stream_config_added(self, index, config):
        stream = PlaybackStream(config)
        self.__streams.append(stream)
        stream.state_change.connect(self.__state_changed)

    def __stream_config_changed(self, index, config):
        pass

    def __stream_config_removed(self, index):
        self.__streams.pop(index)
        
