#!/bin/bash
set -euo pipefail
exec 2>>/tmp/jog_error.log
# Stage this Ubuntu install's own signed kernel into /tftpboot/ubuntu-signed/,
# alongside the shim/grub/grub.cfg staged by
# jog-copy-signed-ubuntu-efi-to-tftpboot.sh. Requires root.
#
# Uses the currently running kernel (uname -r), not a hardcoded package name:
# whatever this JOG laptop actually booted is, by definition, a kernel whose
# signature its own installed shim/grub already trust - that's the entire
# point of this chain (see fogproject docs/adr/0045). JOS's own initrd is
# staged separately by jos-client/build/build-initrd.sh; this script only
# handles the kernel half.
#
# KNOWN GAP, stated plainly rather than buried: this does not stage kernel
# modules. A Secure-Boot-enforcing boot runs in lockdown, which refuses to
# load any module not signed by a key the kernel already trusts - Ubuntu's
# own linux-modules/linux-modules-extra packages are signed and fine, but
# JOS's initrd does not currently load from them at all. Hardware needing a
# module beyond what's built into this kernel will not get it from this
# script. Until that's wired up in jos-client's own init, the documented
# fallback for such hardware is disabling Secure Boot for that one host.

log() { echo "[jog-copy-signed-kernel] $*"; }

[[ "$(id -u)" -eq 0 ]] || {
  echo "Run as root: sudo $0" >&2
  exit 1
}

KVER="$(uname -r)"
SRC="/boot/vmlinuz-${KVER}"

[[ -f "$SRC" ]] || {
  log "no kernel at $SRC (uname -r says ${KVER}) - nothing to stage"
  exit 1
}

DEST="${JOG_UBUNTU_EFI_STAGE:-/tftpboot/ubuntu-signed}"
install -d "$DEST"
install -m 0644 "$SRC" "$DEST/vmlinuz"

SUM="$(sha256sum "$SRC" | cut -d ' ' -f1)"

MAN="$DEST/README.txt"
{
  echo ""
  echo "Kernel staged by jog-copy-signed-ubuntu-kernel-to-tftpboot.sh"
  echo "Time: $(date -Iseconds)"
  echo "Source: $SRC (running kernel, uname -r = ${KVER})"
  echo "sha256: $SUM"
  echo "Modules: NOT staged - see this script's own header comment."
} >>"$MAN"

log "staged $SRC -> $DEST/vmlinuz (sha256 ${SUM})"
