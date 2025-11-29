#!/usr/bin/python

import sys
from PyQt6.QtWidgets import QApplication
from gui.MainWindow import MainWindow

def main():
    # Create the Qt Application
    app = QApplication(sys.argv)
    app.setOrganizationDomain("com")
    app.setOrganizationName("ahl")
    app.setApplicationName("PiStreamer")
    app.setDesktopFileName("pistreamer")
    app.setDesktopSettingsAware(True)

    # Set global style (touch-friendly)
    app.setStyleSheet("""
        * {
            font-size: 18px;
        }
        QPushButton {
            font-size: 18px;
            min-width: 60px;
            min-height: 60px;
        }
    """)
    
    # Create and show the main window
    window = MainWindow()
    window.show()

    # Run the main Qt loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
