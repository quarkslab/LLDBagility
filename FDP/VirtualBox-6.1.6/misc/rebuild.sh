#!/usr/bin/env bash
set -e

SRCDIR="$HOME/Desktop/VMware Shared Folders/fusion-share/LLDBagility"
DSTDIR="$HOME/Desktop/FDP-out"
VBOXVERS="6.1.6"

rm -rf "$DSTDIR"
mkdir "$DSTDIR"

# Build FDP
rm -rf "/tmp/FDP"
cp -r "$SRCDIR/FDP" "/tmp/"
cd "/tmp/FDP"
make clean
make
# Collect files for distribution
cp "build/bin/testFDP" "$DSTDIR/"
cp "build/lib/libFDP.dylib" "$DSTDIR/"
cp "build/lib/libFDP.a" "$DSTDIR/"
cp PyFDP/dist/PyFDP-*.whl "$DSTDIR/"

# Build VirtualBox
export FDPINC="/tmp/FDP/FDP/include"
export FDPLIB="/tmp/FDP/build/lib"
cd "$HOME/Desktop/VirtualBox-$VBOXVERS/"
if [ ! -d "$HOME/Desktop/FDP-VirtualBox-build" ]; then
    # Build from scratch
    "$SRCDIR/FDP/VirtualBox-$VBOXVERS/build.py"
fi
# Re-create patch for clean VirtualBox sources
INITIALCOMMIT=$(git rev-list --max-parents=0 HEAD)
git diff "$INITIALCOMMIT" > "$SRCDIR/FDP/VirtualBox-$VBOXVERS/VirtualBox-$VBOXVERS-FDP-macOS.diff"
# Build new changes only
source "$HOME/Desktop/FDP-VirtualBox-build/env.sh"
kmk
# Pack VirtualBox
sudo rm -rf "$HOME/Desktop/FDP-VirtualBox"
"$SRCDIR/FDP/VirtualBox-$VBOXVERS/pack.py"
# Collect files for distribution
cp -r "$HOME/Desktop/FDP-VirtualBox" "$DSTDIR/VirtualBox"
