#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
cat > "$HOME/.local/share/applications/PiStreamer.desktop" <<EOF
[Desktop Entry]
Name=PiStreamer
Exec=/usr/bin/python3 $DIR/main.py
Icon=$DIR/icon.svg
Terminal=false
Type=Application
Categories=AudioVideo;Video;Audio;
EOF
chmod +x "$HOME/.local/share/applications/PiStreamer.desktop"