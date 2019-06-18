#!/usr/bin/env bash
set -e
dirname () { python -c "import os; print(os.path.dirname(os.path.realpath('$0')))"; }
cd "$(dirname "$0")"

# from https://github.com/AlexanderWillner/runMacOSinVirtualBox/blob/master/runMacOSVirtualbox.sh

VBoxManage createhd --filename "macos-mojave.vdi" --variant Standard --size 61440  # brew cask install virtualbox

EFI_DEVICE=$(vdmutil attach "macos-mojave.vdi" | grep "/dev"| head -n 1)  # brew cask install paragon-vmdk-mounter

diskutil partitionDisk "${EFI_DEVICE}" 1 APFS "macos-mojave" R

diskutil mount "${EFI_DEVICE}s1"

mkdir -p "/Volumes/EFI/EFI/drivers" >/dev/null 2>&1||true
cp "/usr/standalone/i386/apfs.efi" "/Volumes/EFI/EFI/drivers/"

cat <<EOT > /Volumes/EFI/startup.nsh
@echo -off
load "fs0:\EFI\drivers\apfs.efi"
#fixme bcfg driver add 0 "fs0:\\EFI\\drivers\\apfs.efi" "APFS Filesystem Driver"
map -r
echo "Trying to find bootable device..."
for %p in "System\Library\CoreServices" "macOS Install Data\Locked Files\Boot Files" "macOS Install Data" ".IABootFiles" "OS X Install Data" "Mac OS X Install Data"
    for %d in fs1 fs2 fs3 fs4 fs5 fs6
        if exist "%d:\%p\boot.efi" then
            #fixme: bcfg boot add 0 "%d:\\%p\\boot.efi" "macOS"
            "%d:\%p\boot.efi"
        endif
    endfor
endfor
echo "Failed."
EOT

diskutil unmount "${EFI_DEVICE}s1"
diskutil eject "${EFI_DEVICE}"
