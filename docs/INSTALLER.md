# Single-download installer: design

**Goal:** one small download from you that fetches every third-party component from its official upstream
on the customer's own machine. You never redistribute Ubuntu, FOG, FOS or any GPL binary, so you take on
no redistribution obligations beyond your own MIT code.

## Principles

1. **Ship only your code.** The installer contains JOG/JOS scripts, config templates and the notices file.
   Nothing from Canonical, the FOG Project or Microsoft.
2. **Fetch at install time, from upstream, pinned and verified.** Every download has a version pin and a
   checksum (and a signature where upstream publishes one). A failed check stops the install. It never
   warns and continues.
3. **Show what is being fetched and under which licence.** An accept-to-continue step lists each component
   with its licence before downloading. The result is stored in `/etc/jog/third-party.json` and
   regenerated notices are written from the installed packages' own copyright files.
4. **Use unmodified signed boot components.** Shim, GRUB and the kernel come from the Ubuntu archive and are
   never repacked.
5. **Never touch Windows media.** Customers supply their own images and licences.

## Flow

```
jog-installer (your download, MIT)
  1. Show component list + licences  →  user accepts
  2. Fetch Ubuntu Server ISO from releases.ubuntu.com, verify SHA256SUMS signature + checksum
  3. Build the autoinstall seed (cloud-init, your config only) for the target
  4. On the target, first boot:
       apt: dnsmasq, apache2, mariadb, php, memtest86+, shim/grub/kernel (Ubuntu archive)
       FOG: fetch pinned release tag, verify, run upstream installer
       FOS: fetch pinned init.xz, verify sha256, build JOS initrd locally
  5. Write third-party.json + regenerate THIRD_PARTY_NOTICES for what was installed
  6. jog-doctor.sh verifies the staged boot chain
```

## What already exists

- `installer/fetch-ubuntu-live-server-iso.sh`: downloads the Ubuntu ISO and checks it against `SHA256SUMS`.
- `jos/build/build-from-fos.sh`: downloads a pinned FOS `init.xz` and verifies its `.sha256`.
- `install/fog-native-install.sh`: clones FOG and runs its official installer.
- A cloud-init seed ISO and Hyper-V single-ISO builder for hands-off installs.

## Gaps to close (in priority order)

1. **Fail closed on checksums.** `fetch-ubuntu-live-server-iso.sh` prints a warning and continues if
   `SHA256SUMS` cannot be fetched. It should abort.
2. **Verify the signature, not just the checksum.** `SHA256SUMS` comes from the same server as the ISO. Verify
   `SHA256SUMS.gpg` against Ubuntu's published signing key.
3. **Pin FOG.** `fog-native-install.sh` clones a branch (`FOG_GIT_REF`), which moves. Pin a release tag and a
   commit hash, and bump it deliberately after the VM test.
4. **Pin JOG itself.** Autoinstall does `git clone` of the default branch. Install a tagged release with a
   checksum instead, so a customer's install is reproducible.
5. **Licence acceptance and notices step.** Does not exist yet (step 1 and 5 above).
6. **Retire the legacy static-binary fetchers** (`fetch-curl/hwinfo/lshw`), which pull from individual
   third-party GitHub accounts without a pinned checksum.

## Open decisions

- **Form of the single download.** A shell script is simplest. A small Go or Rust binary is friendlier for
  technicians on Windows (the Hyper-V path) and can carry a licence-accept UI. Recommended: shell first, binary
  when there is a customer asking.
- **Remastered ISO or not.** Staying with stock Ubuntu plus autoinstall means no Canonical trademark issue. A
  remastered "JOG OS" ISO needs its own name, no Ubuntu marks, and a per-package licence review. Defer it.
- **Appliance bundle for sale.** If you later sell pre-built laptops or images, the GPL source offer and
  trademark terms in `THIRD_PARTY_NOTICES.md` apply to what you ship. Get that reviewed before the first sale.
