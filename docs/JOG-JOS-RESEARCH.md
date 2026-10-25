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

## 4. Don't reinvent FOS: JOS is FOS userland on a signed kernel

Reading the FOS source (`FOGProject/fos`, release 20261005-221112) showed the original JOS shell client duplicated what FOS already does, and invented a REST-token flow FOG doesn't use. FOS's real contract:

- iPXE `boot.php` builds a per-host kernel command line; the `fog` script then dispatches on `type=down|up` or `mode=...` into `fog.download`, `fog.upload`, `fog.auto.reg`, `fog.inventory` and so on (partclone, udpcast, NFS, resize logic, 4Kn/512 geometry checks, LVM; ADRs 0001–0008).
- **USB-boot mode** already removes the need for that command line. With only `web=http://<server>/fog/ boottype=usb`, FOS POSTs its MAC to `status/hostgetkey.php`, gets a per-host token, then POSTs to `service/hostinfo.php` and sources the returned variables (`type`, `imgid`, `storage`, ...). Errors go to `service/taskerror.php`.

JOS now reuses that wholesale. `jos/build/build-from-fos.sh` downloads the pinned FOS `init.xz` (checksum-verified), converts it to an initramfs, and adds a 6-line `/init` that mounts devtmpfs/proc/sys (FOS's kernel does that itself; the Canonical kernel doesn't for an initramfs). GRUB passes the same arguments as the stock FOS USB image. The Canonical kernel's modules come from `modules.img`; FOS's own udev and kmod load them.

**Verified in the Secure Boot VM** (stub FOG server): PXE → shim → grubnet → signed kernel → FOS userland → udev loads the NIC driver → `udhcpc` → `HEAD index.php` → `POST hostgetkey.php` (base64 MAC) → `POST hostinfo.php` → `POST taskerror.php`. That is the stock FOS↔FOG exchange, with no JOS-specific client code. Not yet tested against a real FOG server (which would return a token and a task).

This removes the open design item from the previous round (how to get FOG tokens into the initrd): there are none.

### What FOS upstream says about this approach (ADR 0012)

FOS maintainers describe this exact pattern (Canonical shim + Ubuntu kernel + unsigned network initrd, as in `abotzung/foguefi`) as a "precedent not to follow" **for FOG itself**, because a signed kernel handing control to a network-supplied initrd is close to what shim exists to prevent. Their own Secure Boot route is a FOG-signed kernel whose key each machine must trust (MOK enrolment, or Dell Command | Configure / iDRAC pushing keys into `db`), with a Microsoft-signed FOG shim as a multi-month long shot. For JOS the trade is deliberate: an isolated imaging network under your control, Ubuntu's kernel enforcing lockdown (so the initrd cannot patch the running kernel), and **no per-machine enrolment**. The fallback if you ever want FOS's own model on the Dell fleet is DCC-enrolling FOG's key; it needs a firmware visit per machine.

### Remaining work

1. **Live FOG test:** point the VM at a real JOG, register a host and run a small unicast deploy through `fog.download`. Then capture.
2. **One physical Dell** with Secure Boot on and a USB3 NIC: confirm udev loads the driver from `modules.img` and the disk is seen (VMD on and off).
3. **Microsoft 2023 CA:** FOS ADR 0019 documents Dell OptiPlex failures after the Windows db update, so test deployed targets still boot Windows with Secure Boot on. FOS ships the CA certs for this.
4. **Kernel upgrades:** `modules.img` is pinned to the staged kernel. Restage after updates; `jog-doctor.sh` flags a mismatch.
5. **Retire the legacy shell client** (`jos/initrd/scripts/jos-*.sh`) once 1–2 pass.
6. **Licence:** FOS is GPL-3. The built initrd contains it, so it is gitignored and not distributed from this repo; if JOG images ever ship it, comply with GPL source offers.
7. **Pilot:** one JOG per imaging table (`docs/CLUSTER.md`, pattern 1).

## 5. Decisions made

- Fleet is pure Dell; no other vendors' firmware quirks are in scope.
- WENDY/CLINIC (LLM diagnosis gate) was a joke and is excluded from this repo.
- JOS reuses FOS userland rather than reimplementing the FOG client (Jon: "don't reinvent the wheel").
- JOS lives in `jos/`; the standalone `splippers/JOS` repo is superseded once this branch is pushed.

## 6. Source trail

`jog/README.md`, `jog/docs/{CLUSTER,ISO-BUILD}.md`, `jos/docs/{architecture,fos-fork-refactor-plan,fos-fog-parity-checklist}.md`, `jos/.cursor/rules/jos-unified.mdc` (the authoritative JOS rules), `JONOTRON_CONTEXT.md` (ODIN/JOG flagged "sellable today; WDS is dying"), `UNIVERSE_UNDERSTANDING.md`.
