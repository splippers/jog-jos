#!/bin/sh
# Install the Haar Plymouth theme on a Haar/JOS base system. Run as root on the target.
set -eu
d=/usr/share/plymouth/themes/haar
here=$(dirname "$0")
install -d "$d"
install -m 644 "$here"/haar.plymouth "$here"/haar.script "$here"/background.png "$here"/bar.png "$d"/
[ -f "$here/logo.png" ] && install -m 644 "$here/logo.png" "$d"/
update-alternatives --install /usr/share/plymouth/themes/default.plymouth default.plymouth "$d/haar.plymouth" 200
update-alternatives --set default.plymouth "$d/haar.plymouth"
update-initramfs -u
echo "Haar Plymouth theme installed. Reboot to see it."
