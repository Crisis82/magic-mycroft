#!/bin/sh

git submodule init
git submodule update

# MagicMirror
sudo pacman -Syu nodejs
cd MagicMirror/
npm run install-mm
cp ../utils/config/config.json ./config/
cp -r ../utils/modules/ ./modules/
bash -c ./modules/MMM-Remote-Control/installer.sh
cd ..

# Mycroft
cd mycroft-core
bash dev_setup.sh
cd ..

# MagiMirror-skill
cp -r ./magic-mirror-voice-control-skill/ /opt/mycroft/skills/
