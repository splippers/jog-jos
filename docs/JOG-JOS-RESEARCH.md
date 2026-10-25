# JOG + JOS — consolidated research (the future of FOG imaging)

Merged 2026-10-25 from: `JOG` (server appliance), `JOS` (client runtime, formerly the `jos-client` submodule and a separate `jos` repo), plus references in `fog-ambulance`, `JONOTRON_CONTEXT.md` and `craic/`.

## 1. What each piece is

| Piece | Role | Where now |
|-------|------|-----------|
| **JOG** — Jonathan's OpenSource Ghost | Portable FOG server (Ubuntu 26.04, native FOG under `/opt/fog`). dnsmasq DHCP/TFTP bound only to a USB Ethernet NIC so it can't leak onto a corporate LAN. Autoinstall ISOs, first-boot wizard, Chromium kiosk, edge/primary cluster roles. | repo root |
| **JOS** — Jonathan's OS | Replacement for FOG's FOS client. BusyBox initramfs on a signed Ubuntu kernel: DHCP `siaddr` → FOG server, REST register/inventory, task runner, partclone unicast, udpcast multicast with a weak-link watchdog, destructive writes gated by `JOS_IMAGING_ALLOW_DISK_WRITE`. | `jos/` |
| **FOG-Ambulance** | Separate live-USB AI rescue for FOG-deployed machines. Related, not merged. | `Projects/fog-ambulance` |

`jurassic-os` is **unrelated** (a Jurassic Park web toy); it only shares the initials.

## 2. Merge notes

- JOS history is subtree-merged into `jos/` on branch `unify-jos`; the `jos-client` submodule is removed. The submodule was an older snapshot (Apr 27); the standalone `jos` repo had everything newer (unicast imaging, FOG task runner, parity docs), so `jos/` is the canonical copy.
- Old checkouts at `Projects/jos` and `Projects/jog` are untouched. Nothing was pushed. GitHub `splippers/JOS` still exists separately until you decide to archive it.
- Vendored binaries (`jos/initrd/bin`, `jos/build/tmp`, `jos/build/out/initrd.img`) are gitignored and live only in the old `Projects/jos` checkout; rebuild with `jos/build/build-initrd.sh`.

## 3. Secure Boot: findings and status

Fleet is pure Dell (Latitude/Precision), all UEFI. The design intent was right (vendor-signed shim, GRUB and kernel; only the unsigned initramfs is ours) but the repo didn't implement it end to end. Status as of 2026-10-25:

| # | Finding | Status |
|---|---------|--------|
| 1 | Default bootfile `snponly.efi` is unsigned, so Secure Boot firmware refuses it | **Fixed**: default is `ubuntu-signed/shimx64.efi` in env example, wizard, first-boot and dnsmasq render |
| 2 | Docs put iPXE before shim; unsigned iPXE can't be the first stage | **Fixed**: docs and rules now say firmware PXE → shim → grubnetx64 → signed kernel → JOS. iPXE is Secure Boot-off only |
| 3 | `boot.ipxe` loads the kernel directly | **Marked** Secure Boot-off only |
| 4 | No `grub.cfg` or kernel/initrd staging | **Fixed**: `scripts/jog-stage-jos-boot.sh`, run by `jog-provision-stack.sh` |
| 5 | Kernel lockdown rejects unsigned modules, so NIC/storage drivers must match the signed kernel | **Fixed**: `modules.img` is built from the same kernel package (28 modules, 3 MB incl. USB3 NICs, VMD, NVMe, AHCI, NFS) and loaded by `jos-modules.sh` |
| 6 | Shim cert expiry (Microsoft 2011 CA) | **Open**: staging prefers the dual-signed shim; needs a test on your oldest Latitudes |
| 7 | MOK enrolment | **Avoided**: nothing needs it |

Also fixed: `jos-net.sh` counted `lo` as a NIC, so it never waited for USB NICs to enumerate (it now waits for a real interface). `grubx64.efi` next to shim was the on-disk GRUB, which has no network prefix; it is now the net build.

**Verified in QEMU/OVMF with Secure Boot enforcing and Microsoft keys** (`scripts/test-secureboot-vm.sh`): PXE → shim → grubnet → signed 7.0.0-38 kernel → JOS `/init` → modules loaded → DHCP → FOG registration attempt (no FOG server in the test). The control passes too: an unsigned bootloader (the class `snponly.efi` belongs to) is rejected with "Access Denied". Not yet tested on real Dell hardware or against a live FOG server.

## 4. Roll-out plan (remaining)

1. **Live FOG test:** point the VM test at a real JOG, confirm register → inventory → task poll → unicast deploy of a small image. Needs `/etc/fog/jos.conf` (API tokens) delivered into the initrd; that delivery path is the main open design item.
2. **One physical Dell**, Secure Boot on, USB3 dock NIC, with VMD on and off. Confirm the NIC enumerates and the disk is seen.
3. **Oldest-firmware Latitude** for the shim CA question (finding 6).
4. **FOS parity phases 0–3**, then multicast watchdog acceptance (3 × 10 s under 30 MB/s).
5. **Kernel-upgrade hook:** `modules.img` is pinned to the kernel it was staged from. Restage (`jog-stage-jos-boot.sh`) after each kernel update; `jog-doctor.sh` flags a mismatch. A dpkg post-invoke hook would automate it.
6. **Pilot:** one JOG per imaging table (`docs/CLUSTER.md`, pattern 1).

## 5. Decisions made

- Fleet is pure Dell; no other vendors' firmware quirks are in scope.
- WENDY/CLINIC (LLM diagnosis gate) was a joke and is excluded from this repo.
- JOS lives in `jos/`; the standalone `splippers/JOS` repo is superseded once this branch is pushed.

## 6. Source trail

`jog/README.md`, `jog/docs/{CLUSTER,ISO-BUILD}.md`, `jos/docs/{architecture,fos-fork-refactor-plan,fos-fog-parity-checklist}.md`, `jos/.cursor/rules/jos-unified.mdc` (the authoritative JOS rules), `JONOTRON_CONTEXT.md` (ODIN/JOG flagged "sellable today; WDS is dying"), `UNIVERSE_UNDERSTANDING.md`.
