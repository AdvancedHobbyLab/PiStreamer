
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QProcess, QSettings
import re

class PlaybackController(QObject):
    
    # Signals
    state_change = pyqtSignal(bool)
    frame = pyqtSignal(int)
    fps = pyqtSignal(float)
    bitrate = pyqtSignal(float)
    
    def __init__(self, settings):
        super().__init__()
        
        self.__settings = settings
        
        self.__process = QProcess(self)
        self.__process.readyReadStandardOutput.connect(self.__handle_output)
        self.__process.readyReadStandardError.connect(self.__handle_error)
        self.__process.stateChanged.connect(self.__state_changed)
        
        
    @pyqtSlot()
    def start_playback(self):
        # Check process state
        if self.__process.state() != QProcess.ProcessState.NotRunning:
            return

        self.__settings.beginGroup("Input")
        device = self.__settings.value("device", "/dev/video0")
        self.__settings.endGroup()

        self.__settings.beginGroup("Output")
        output_address = self.__settings.value("address", "127.0.0.1:5000")
        self.__settings.endGroup()
        
        command = [
            "ffmpeg",
            "-f", "v4l2",
            "-input_format", "rgb24",
            "-video_size", "1920x1080",
            "-i", device,
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-tune", "zerolatency",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-f", "mpegts", "udp://"+output_address
        ]
        self.__process.start(command[0], command[1:])
    
    @pyqtSlot()
    def stop_playback(self):
        # Check process state
        if self.__process.state() == QProcess.ProcessState.NotRunning:
            return
        
        # Works for streaming since files don't need to be finalized
        self.__process.terminate()
        
    # Return True if running else False
    def state(self):
        return self.__process.state() != QProcess.ProcessState.NotRunning
        
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
        
        