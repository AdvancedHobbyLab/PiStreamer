
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QProcess, QSettings, QTimer
import re
from urllib.parse import urlparse

import gi, time
gi.require_version('Gst', '1.0')
from gi.repository import Gst

Gst.init(None)

class VideoPlaybackSource(QObject):

    # Signals
    state_change = pyqtSignal(bool)
    frame = pyqtSignal(int)
    fps = pyqtSignal(float)
    bitrate = pyqtSignal(float)

    def __init__(self, data):
        super().__init__()

        self.__process = QProcess(self)
        self.__process.readyReadStandardOutput.connect(self.__handle_output)
        self.__process.readyReadStandardError.connect(self.__handle_error)
        self.__process.stateChanged.connect(self.__state_changed)
        self.__process.finished.connect(self.__clean_up)

        self.set_config(data)

    def set_config(self, data):
        self.data = data

    def state(self):
        return self.__process.state()

    def start_playback(self):
        print("Starting Source:", self.data.get("name", "Unknown"))
        # Check process state
        if self.__process.state() != QProcess.ProcessState.NotRunning:
            return

        # Input options
        device = self.data["device"]
        format = self.data["format"]
        resolution = str(self.data["width"]) + "x" + \
                     str(self.data["height"])
        framerate = str(self.data["framerate"])
        input_options = [
            "-f", "v4l2",
            "-input_format", format,
            "-video_size", resolution,
            "-framerate", framerate,
            "-i", device,
            "-r", framerate,
        ]

        # Encoder Options
        encoder_options = []
        encoder = self.data["encoder"]
        encoder_options += ["-c:v", encoder]
        if encoder == "libx264":
            encoder_options += [
                "-preset", "ultrafast",
                "-tune", "zerolatency",
                "-crf", str(self.data["crf"]),
                "-pix_fmt", "yuv420p",
            ]

        # Output Options
        output_address = self.data["address"]

        muxer = "mpegts"
        if format == "mjpeg" and encoder == "copy":
            muxer = "mjpeg"

        output_options = [
            "-f",
            muxer,
            output_address
        ]

        command = ["ffmpeg"] + input_options + encoder_options + output_options
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

class AudioPlaybackSource(QObject):

    # Signals
    state_change = pyqtSignal(bool)
    bitrate = pyqtSignal(float)

    def __init__(self, data):
        super().__init__()

        self.total_bytes = 0
        self.last_time = time.time()

        self.pipeline = None
        self.timer = QTimer()

        self.set_config(data)


    def set_config(self, data):
        self.data = data

        self.pipeline = Gst.parse_launch(self.__build_pipeline_string())

        self.identity = self.pipeline.get_by_name("probe")
        self.identity.connect("handoff", self.__on_handoff)
        self.bus = self.pipeline.get_bus()

        # Poll GStreamer bus via Qt
        self.timer = QTimer()
        self.timer.timeout.connect(self.__poll_bus)
        self.timer.start(50)

    def state(self):
        return self.__process.state()

    def start_playback(self):
        print("Starting Source:", self.data.get("name", "Unknown"))
        self.pipeline.set_state(Gst.State.PLAYING)
        print("Running: gst-launch-1.0 -v", self.__build_pipeline_string())

    def stop_playback(self):
        self.pipeline.set_state(Gst.State.NULL)

        self.bitrate.emit(0)

    def __build_pipeline_string(self):
        device = self.data["device"]
        format = self.data["format"]
        channels = self.data["channels"]
        encoder = self.data["encoder"]  # must be opus

        parsed = urlparse(self.data["address"])
        protocal = parsed.scheme  # Must be UDP
        host = parsed.hostname
        port = parsed.port

        out = ( "alsasrc device=" + str(device) + " "
                "! audio/x-raw,format=" + str(format) + ",rate=48000,channels=" + str(channels) + " "
                "! opusenc bitrate=64000 "
                "! identity name=probe signal-handoffs=true "
                "! mpegtsmux "
                "! udpsink host=" + str(host) + " port=" + str(port))

        return out

    def __on_handoff(self, identity, buffer, pad=None):
        self.total_bytes += buffer.get_size()
        now = time.time()
        if now - self.last_time >= 1.0:
            kbps = (self.total_bytes * 8) / 1000
            self.bitrate.emit(kbps)
            self.total_bytes = 0
            self.last_time = now

    def __poll_bus(self):
        msg = self.bus.pop()
        if not msg:
            return

        if msg.type == Gst.MessageType.ERROR:
            err, dbg = msg.parse_error()
            print("GStreamer error:", err, dbg)

        elif msg.type == Gst.MessageType.EOS:
            print("End of stream")

class PlaybackController(QObject):
    
    # Signals
    state_change = pyqtSignal(bool)
    bitrate = pyqtSignal(float)
    
    def __init__(self, settings):
        super().__init__()
        
        self.__settings = settings
        self.__settings.video_config_added.connect(self.__video_config_added)
        self.__settings.video_config_changed.connect(self.__video_config_changed)
        self.__settings.video_config_removed.connect(self.__video_config_removed)
        self.__settings.audio_config_added.connect(self.__audio_config_added)
        self.__settings.audio_config_changed.connect(self.__audio_config_changed)
        self.__settings.audio_config_removed.connect(self.__audio_config_removed)
        
        self.__video_sources = []
        self.__audio_sources = []

        self.__state = False

        # Add Video Sources
        for i in range(self.__settings.num_video_configs()):
            config = self.__settings.get_video_config(i)
            self.__video_config_added(i, config)

        # Add Audio Sources
        for i in range(self.__settings.num_audio_configs()):
            config = self.__settings.get_audio_config(i)
            self.__audio_config_added(i, config)

    def num_video_sources(self):
        return len(self.__video_sources)

    def video_source(self, index):
        return self.__video_sources[index]

    def num_audio_sources(self):
        return len(self.__audio_sources)

    def audio_source(self, index):
        return self.__audio_sources[index]
        
    @pyqtSlot()
    def start_playback(self):
        print()
        print("Start Playback...")
        self.state_change.emit(True)
        for source in self.__video_sources + self.__audio_sources:
            print()
            source.start_playback()
    
    @pyqtSlot()
    def stop_playback(self):
        print("Stop Playback...")
        for source in self.__video_sources + self.__audio_sources:
            source.stop_playback()
        
    # Return True if running else False
    def state(self):
        return self.__state
        
    def __state_changed(self, new_state):
        # Get State
        final_state = False
        for source in self.__video_sources:
            state = source.state()
            if state != QProcess.ProcessState.NotRunning:
                final_state = True

        # TODO - add audio sources

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

    def __video_config_added(self, index, config):
        source = VideoPlaybackSource(config)
        self.__video_sources.append(source)
        source.state_change.connect(self.__state_changed)

    def __video_config_changed(self, index, config):
        source = self.__video_sources[index]
        source.set_config(config)

    def __video_config_removed(self, index):
        self.__video_sources.pop(index)

    def __audio_config_added(self, index, config):
        source = AudioPlaybackSource(config)
        self.__audio_sources.append(source)
        source.state_change.connect(self.__state_changed)

    def __audio_config_changed(self, index, config):
        source = self.__audio_sources[index]
        source.set_config(config)

    def __audio_config_removed(self, index):
        self.__audio_sources.pop(index)
        