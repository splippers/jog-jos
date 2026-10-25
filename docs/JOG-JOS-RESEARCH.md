# JOG + JOS — consolidated research (the future of FOG imaging)

Merged 2026-10-25 from: `JOG` (server appliance), `JOS` (client runtime, formerly the `jos-client` submodule and a separate `jos` repo), plus references in `fog-ambulance`, `martin/ROADMAP.md` (WENDY/CLINIC), `JONOTRON_CONTEXT.md` and `craic/`.

## 1. What each piece is

| Piece | Role | Where now |
|-------|------|-----------|
| **JOG** — Jonathan's OpenSource Ghost | Portable FOG server (Ubuntu 26.04, native FOG under `/opt/fog`). dnsmasq DHCP/TFTP bound only to a USB Ethernet NIC so it can't leak onto a corporate LAN. Autoinstall ISOs, first-boot wizard, Chromium kiosk, edge/primary cluster roles. | repo root |
| **JOS** — Jonathan's OS | Replacement for FOG's FOS client. BusyBox initramfs on a signed Ubuntu kernel: DHCP `siaddr` → FOG server, REST register/inventory, task runner, partclone unicast, udpcast multicast with a weak-link watchdog, destructive writes gated by `JOS_IMAGING_ALLOW_DISK_WRITE`. | `jos/` |
| **WENDY / CLINIC** (planned) | JOS collects logs, a local LLM proposes fix/nuke/escalate, a human signs a "death certificate" before any wipe. | `martin/ROADMAP.md` (not merged) |
| **FOG-Ambulance** | Separate live-USB AI rescue for FOG-deployed machines. Related, not merged. | `Projects/fog-ambulance` |

`jurassic-os` is **unrelated** (a Jurassic Park web toy); it only shares the initials.

## 2. Merge notes

- JOS history is subtree-merged into `jos/` on branch `unify-jos`; the `jos-client` submodule is removed. The submodule was an older snapshot (Apr 27); the standalone `jos` repo had everything newer (unicast imaging, FOG task runner, parity docs), so `jos/` is the canonical copy.
- Old checkouts at `Projects/jos` and `Projects/jog` are untouched. Nothing was pushed. GitHub `splippers/JOS` still exists separately until you decide to archive it.
- Vendored binaries (`jos/initrd/bin`, `jos/build/tmp`, `jos/build/out/initrd.img`) are gitignored and live only in the old `Projects/jos` checkout; rebuild with `jos/build/build-initrd.sh`.

## 3. Secure Boot: current state versus what rollout needs

The design intent is right: keep shim, GRUB and the kernel vendor-signed, and change only the unsigned initramfs. But **the repo does not yet implement that end to end**. Findings, most important first:

1. **The default PXE boot file is not Secure Boot-safe.** `jog.env.example`, the wizard (`installer/jog-install-wizard.sh:162`) and the unattended first-boot (`scripts/jog-first-boot-unattended.sh:44`) all default `JOG_DHCP_BOOTFILE=snponly.efi`. FOG's iPXE binaries are unsigned, so firmware with Secure Boot on refuses them. `ubuntu-signed/shimx64.efi` is staged but is opt-in.
2. **`iPXE → shim` cannot work with Secure Boot on.** The docs (`jos/docs/architecture.md`, `jos/config/ipxe/jos.ipxe.example`) put iPXE first in the chain and describe it as outside the measured chain. Firmware must verify whichever binary it loads first, and unsigned iPXE fails that check. The workable chain is `firmware PXE → shimx64.efi → grubnetx64/grubx64 → signed vmlinuz + JOS initrd`. iPXE stays for Secure Boot-off machines only.
3. **`jog/ipxe/boot.ipxe` loads `vmlinuz` and `initrd.img` directly from iPXE.** That can't pass verification either. It should be marked legacy/Secure-Boot-off.
4. **There is no GRUB config or staging for the signed path.** Nothing writes `grub/grub.cfg` into the TFTP root or copies the signed `vmlinuz` and `jos/initrd.img` where GRUB can fetch them. `jog-copy-signed-ubuntu-efi-to-tftpboot.sh` stages the EFI binaries only.
5. **Kernel and initramfs must match.** Under Secure Boot the kernel's lockdown blocks unsigned modules, so the initramfs must carry the Canonical-signed modules for the exact kernel version it boots: USB3 NIC drivers (r8152, ax88179, cdc_ncm), Intel VMD and NVMe, plus firmware blobs. `build-initrd.sh` should pin the kernel version and bundle the matching modules.
6. **Shim certificate expiry.** The Microsoft UEFI CA 2011 reached end of life in mid-2026, and newer shims may be signed only by the 2023 CA. The staging script already prefers `shimx64.efi.dualsigned`, which is the right call. Test on your oldest Latitudes, whose db may lack the 2023 CA. This needs checking on real hardware; I haven't verified it here.
7. **Avoid MOK enrolment on clients.** Keeping everything vendor-signed is what makes zero-touch possible. Any per-machine key enrolment defeats it.

## 4. Roll-out plan (proposed order)

1. **Boot-chain PoC in a VM** (OVMF with Secure Boot enabled): DHCP bootfile = `ubuntu-signed/shimx64.efi`, a `grub.cfg` that loads the signed kernel plus the JOS initrd, and confirm `/init` runs and logs the registration. Done when a Secure Boot-on VM reaches `jos-register.sh`.
2. **Fix defaults:** switch the wizard and first-boot to shim for UEFI, keep `snponly.efi` as an explicit legacy choice, and auto-render `grub.cfg`. Add a `jog-doctor` check that fails loudly if the bootfile isn't a signed binary.
3. **Kernel/module pinning** in the initrd build (finding 5), then test on the target fleet: Dell Latitude (VMD on/off, USB3 NIC).
4. **FOS parity phases 0–3** (`jos/docs/fos-fog-parity-checklist.md`). All boxes are still unchecked, but the code for registration, inventory, the task runner and unicast already exists, so this is mostly verification against a real FOG server.
5. **Multicast watchdog** acceptance test (the 3 × 10 s under 30 MB/s kill-switch).
6. **Pilot** with one JOG per imaging table (`docs/CLUSTER.md`, pattern 1), then decide about WENDY/CLINIC as a separate phase.

## 5. Open questions for Jon

- Is the target fleet Dell-only (Latitude/Precision), and what is the oldest firmware date? That decides how much finding 6 matters.
- Should the standalone GitHub `splippers/JOS` be archived once `unify-jos` is merged to `main` and pushed?
- Does WENDY/CLINIC belong in this repo (`wendy/`) or stay in M.A.R.T.I.N.?

## 6. Source trail

`jog/README.md`, `jog/docs/{CLUSTER,ISO-BUILD}.md`, `jos/docs/{architecture,fos-fork-refactor-plan,fos-fog-parity-checklist}.md`, `jos/.cursor/rules/jos-unified.mdc` (the authoritative JOS rules), `martin/ROADMAP.md`, `JONOTRON_CONTEXT.md` (ODIN/JOG flagged "sellable today; WDS is dying"), `UNIVERSE_UNDERSTANDING.md`.
