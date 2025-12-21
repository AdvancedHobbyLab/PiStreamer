# Overview

Raspberry Pis do not have a lot of power for encoding videos or running streaming software such as OBS. This application overcomes that by performing minimal encoding on the Pi then streaming it to another machine that can do heavier processing. This gives you more flexibility in where you want to setup your streaming setup.

# Installation.

This needs Python 3, PyQt6, ffmpeg and v4l2-ctl. To do this on a Raspberry Pi, run:

```bash
$ sudo apt install python3-pyqt6 pyqt6-dev pyqt6-dev-tools ffmpeg v4l-utils -y
```

An installation script is provided. It is not needed, but adds convenience by installing a *.desktop file on your system that points to the location where you cloned this repository.
