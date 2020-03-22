#!/usr/bin/env bash
set -e
dirname () { python -c "import os; print(os.path.dirname(os.path.realpath('$0')))"; }
cd "$(dirname "$0")"

rm -f "/tmp/macos-mojave.cdr.dmg"
hdiutil create -o "/tmp/macos-mojave.cdr" -size 8g -layout SPUD -fs HFS+J

hdiutil attach "/tmp/macos-mojave.cdr.dmg" -mountpoint "/Volumes/macos-mojave-installmedia"
sudo "/Applications/Install macOS Mojave.app/Contents/Resources/createinstallmedia" --volume "/Volumes/macos-mojave-installmedia" --nointeraction

hdiutil detach "/Volumes/Install macOS Mojave"
hdiutil convert "/tmp/macos-mojave.cdr.dmg" -format UDTO -o "/tmp/macos-mojave.iso"
mv "/tmp/macos-mojave.iso.cdr" "/tmp/macos-mojave.iso"
