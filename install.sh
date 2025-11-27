#!/bin/bash

if [[ $EUID -ne 0 ]]; then
    echo "Please run as root (e.g., sudo $0)"
    exit 1
fi

DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Installing Icons"
if command -v rsvg-convert >/dev/null 2>&1; then
    echo "Converting icon.svg to PNG"
    
    # Create some PNG icons in case the OS doesn't support SVG
    rsvg-convert -w 16 -h 16 icon.svg -o /usr/share/icons/hicolor/16x16/apps/com.ahl.pistreamer.png
    rsvg-convert -w 24 -h 24 icon.svg -o /usr/share/icons/hicolor/24x24/apps/com.ahl.pistreamer.png
    rsvg-convert -w 32 -h 32 icon.svg -o /usr/share/icons/hicolor/32x32/apps/com.ahl.pistreamer.png
    rsvg-convert -w 48 -h 48 icon.svg -o /usr/share/icons/hicolor/48x48/apps/com.ahl.pistreamer.png
    rsvg-convert -w 64 -h 64 icon.svg -o /usr/share/icons/hicolor/64x64/apps/com.ahl.pistreamer.png
else
    echo "Can't find rsvg-convert: falling back to using SVG icon"
fi

cp icon.svg /usr/share/icons/hicolor/scalable/apps/com.ahl.pistreamer.svg

# Update theme cache
gtk-update-icon-cache /usr/share/icons/hicolor

echo "Installing *.desktop file"

cat > "/usr/share/applications/PiStreamer.desktop" <<EOF
[Desktop Entry]
Name=PiStreamer
Exec=/usr/bin/python3 $DIR/main.py
Icon=com.ahl.pistreamer
Terminal=false
Type=Application
Categories=AudioVideo;Video;Audio;
EOF
chmod +x "/usr/share/applications/PiStreamer.desktop"

echo "Installation Finished"