#!/bin/sh

# MagicMirror
curl -sL https://deb.nodesource.com/setup_16.x | sudo -E bash -
sudo pacman -Syu nodejs
cp utils/config/config.json MagicMirror/config/
cp -r utils/modules/ MagicMirror/modules/
bash -c MagicMirror/modules/MMM-Remote-Control/installer.sh
cd MagicMirror/
npm run install-mm
cd ..

# Mycroft
cd mycroft-core
bash dev_setup.sh
cd ..

# MagiMirror-skill
cp -r magic-mirror-voice-control-skill /opt/mycroft/skills/
