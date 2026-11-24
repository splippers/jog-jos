# Single-download installer: design

**Goal:** one small download from you that fetches every third-party component from its official upstream
on the customer's own machine. You never redistribute Ubuntu, FOG, FOS or any GPL binary, so you take on
no redistribution obligations beyond your own MIT code.

## Principles

1. **Ship only your code.** The installer contains Haar/JOS scripts, config templates and the notices file.
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

## Status of the gaps

| # | Gap | Status |
|---|---|---|
| 1 | Fail closed on checksums | **Done.** `fetch-ubuntu-live-server-iso.sh` aborts if the signed checksums cannot be fetched or do not match. |
| 2 | Verify the signature, not just the checksum | **Done.** SHA256SUMS must be signed by the pinned Ubuntu CD signing key (fingerprint in the script). Tested with the real ISO, a bad file, and a wrong key. `--verify-only` checks an existing ISO. |
| 3 | Pin FOG | **Done.** Release tag `1.5.10.2518`, commit `c97e2050...` checked after the clone (verified against upstream). Move it by changing tag and commit together after the VM test. |
| 4 | Pin Haar itself | **Mechanism done, release tag still to cut.** Autoinstall clones `installer/JOG_REF`. It is `main` for now, and the renderer warns. Tag a release (for example `v0.1.0`), set `JOG_REF`, and installs become reproducible. |
| 5 | Licence acceptance and notices step | **To do.** |
| 6 | Retire the legacy static-binary fetchers (`fetch-curl/hwinfo/lshw`) | **To do.** The default FOS-based build does not use them. |
| 7 | Pin and verify FOS | Already done: `build-from-fos.sh` pins `FOS_TAG` and verifies the `.sha256`. Note this is a checksum from the same host as the file, so it detects corruption, not a compromised release. |

## Open decisions

- **Form of the single download.** A shell script is simplest. A small Go or Rust binary is friendlier for
  technicians on Windows (the Hyper-V path) and can carry a licence-accept UI. Recommended: shell first, binary
  when there is a customer asking.
- **Remastered ISO or not.** Staying with stock Ubuntu plus autoinstall means no Canonical trademark issue. A
  remastered "Haar OS" ISO needs its own name, no Ubuntu marks, and a per-package licence review. Defer it.
- **Appliance bundle for sale.** If you later sell pre-built laptops or images, the GPL source offer and
  trademark terms in `THIRD_PARTY_NOTICES.md` apply to what you ship. Get that reviewed before the first sale.
