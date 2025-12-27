from PyQt6.QtWidgets import QApplication, QWidget, QComboBox, QVBoxLayout
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt

import subprocess
import glob
import re

import gi
gi.require_version("Gst", "1.0")
from gi.repository import Gst

Gst.init(None)

class PlaybackOptions():
    def __init__(self):
        pass

    def GetDevices(self):
        model = QStandardItemModel()

        found = []
        devices = glob.glob("/dev/video*")
        for device in devices:
            try:
                result = subprocess.run(
                    ["v4l2-ctl", "--device="+device, "-D"],
                    capture_output=True,
                    text=True,
                    timeout=1
                )

                if result.stdout.count("Video Capture\n") > 1:
                    match = re.search(r"Card type\s*:\s*(.+)", result.stdout)
                    name = match.group(1) if match else None
                    found.append( (name+" ("+device+")", device) )

            except subprocess.TimeoutExpired:
                print("The subprocess timed out!")

        for text, value in found:
            item = QStandardItem(text)
            item.setData(value, Qt.ItemDataRole.UserRole)  # store value
            model.appendRow(item)

        return model

    def GetFormats(self, device):
        # Create the model
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(["Compressed", "Simple Name", "Full Name", "Resolutions"])

        try:
            result = subprocess.run(
                ["ffmpeg", "-f", "v4l2", "-list_formats", "all", "-i", device],
                capture_output=True,
                text=True,
                timeout=1
            )

            # Regex to parse each line
            line_re = re.compile(r"\] (\w+)\s*:\s*(\w+)\s*:\s*(.+?)\s*:\s*(.+)")

            for line in result.stderr.splitlines():
                match = line_re.search(line)
                if match:
                    compressed, simple_name, full_name, res_str = match.groups()
                    resolutions = res_str.split()

                    if simple_name == "Unsupported":
                        continue

                    compressed = compressed == "Compressed"

                    # Create items
                    items = [
                        QStandardItem(compressed),
                        QStandardItem(simple_name),
                        QStandardItem(full_name),
                        QStandardItem(", ".join(resolutions))  # store as string for display
                    ]
                    model.appendRow(items)

        except subprocess.TimeoutExpired:
            print("The subprocess timed out!")

        return model

    def GetAudioDevices(self):
        model = QStandardItemModel()
        devices = []

        try:
            result = subprocess.run(
                ["arecord", "-l"],
                capture_output=True,
                text=True,
                timeout=1
            )

            card_re = re.compile(
                r"card\s+(?P<card>\d+):\s+(?P<card_name>[^\s]+)\s+\[(?P<card_hr>[^\]]+)\],\s+device\s+(?P<device>\d+):"
            )

            device_hr_re = re.compile(r"\[(?P<device_hr>[^\]]+)\]")

            lines = result.stdout.splitlines()
            i = 0

            while i < len(lines):
                line = lines[i]
                card_match = card_re.search(line)
                if card_match:
                    card = card_match.group("card")
                    device = card_match.group("device")
                    card_name = card_match.group("card_name")

                    # Look ahead for the first [human readable device name]
                    device_hr = None
                    for j in range(i + 1, min(i + 4, len(lines))):
                        m = device_hr_re.search(lines[j])
                        if m:
                            device_hr = m.group("device_hr")
                            break

                    devices.append({
                        "hw": f"hw:{card},{device}",
                        "card_index": int(card),
                        "device_index": int(device),
                        "card_name": card_name,
                        "device_name": device_hr,
                    })

                i += 1
        except subprocess.TimeoutExpired:
            print("The subprocess timed out!")

        for device in devices:
            item = QStandardItem(str(device["card_name"]) + ", " + str(device["device_name"]) + " ("+str(device["hw"])+")")
            item.setData(device["hw"], Qt.ItemDataRole.UserRole)  # store value
            model.appendRow(item)

        return model

    def GetAudioFormats(self, device):
        model = QStandardItemModel()

        item = QStandardItem("S16LE")
        item.setData("S16LE", Qt.ItemDataRole.UserRole)
        model.appendRow(item)

        return model