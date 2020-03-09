#!/bin/bash
set -e

osascript -e 'quit app "VirtualBox"'

cd "$HOME/Downloads/"
sudo rm -rf "FDP-out"

wormhole receive --accept-file

sudo "FDP-out/VirtualBox/loadall.sh"

"/usr/local/bin/python3" -m pip install --upgrade FDP-out/PyFDP-*.whl

sudo "/Library/Developer/CommandLineTools/usr/bin/python3" -m pip install --upgrade FDP-out/PyFDP-*.whl -t "/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.7/lib/python3.7/site-packages/"

open "FDP-out/VirtualBox/VirtualBox.app"
