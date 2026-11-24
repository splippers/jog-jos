# Third-party notices

Brume and JOS are MIT-licensed (see `LICENSE`). They **use** the third-party software below but this repository
does **not** contain or redistribute it. Each component is downloaded from its upstream source on the
machine that builds or installs Brume, and stays under its own licence.

> This table is a working list, not legal advice. The authoritative licence text for each Ubuntu package is
> its `/usr/share/doc/<package>/copyright` file; for pinned upstream releases it is the licence file in the
> upstream release. Rows marked **verify** have not been checked against the exact pinned version.

## Core stack

| Component | Role | Licence | Obtained from |
|---|---|---|---|
| FOG Project (server) | Imaging server, web UI, scheduler | GPL-3.0 | github.com/FOGProject/fogproject, installed at setup time |
| FOS (FOG Operating System) | Client userland that JOS repackages | GPL-3.0 | github.com/FOGProject/fos releases, pinned by tag + sha256 |
| Ubuntu Server | Base OS of the appliance | Mixed; per-package licences | releases.ubuntu.com, sha256-verified |
| Linux kernel (Canonical-signed) | Boot kernel under Secure Boot | GPL-2.0 (syscall exception) | Ubuntu archive; used unmodified so the signature stays valid |
| shim (Canonical-signed) | Secure Boot first stage | BSD-2-Clause | Ubuntu archive; used unmodified |
| GRUB (network build, signed) | Boot menu | GPL-3.0-or-later | Ubuntu archive; used unmodified |
| dnsmasq | DHCP/TFTP on the imaging NIC | GPL-2.0 or GPL-3.0 | Ubuntu archive |
| Apache HTTP Server | FOG web UI | Apache-2.0 | Ubuntu archive |
| MariaDB | FOG database | GPL-2.0 | Ubuntu archive |
| PHP | FOG web UI | PHP-3.01 | Ubuntu archive |
| Memtest86+ | Optional memory test menu entry | GPL-2.0 | Ubuntu archive (`memtest86+`) |

## Inside the FOS/JOS client image

These ship inside the upstream FOS image or are fetched by `jos/build/fetch-*.sh` (the legacy shell client).

| Component | Licence | Notes |
|---|---|---|
| partclone | GPL-2.0-or-later | Disk imaging engine |
| udpcast | GPL-2.0 | Multicast; **verify** |
| BusyBox | GPL-2.0 | |
| dmidecode | GPL-2.0-or-later | |
| lshw | GPL-2.0 | **verify** |
| hwinfo | GPL-2.0 | **verify** |
| jq | MIT | |
| curl | curl licence (MIT-style) | |
| nfs-utils (`mount.nfs`) | GPL-2.0 | **verify** |
| util-linux (`sfdisk`) | GPL-2.0-or-later | **verify** |

**Supply-chain note.** The legacy `fetch-curl.sh`, `fetch-hwinfo.sh` and `fetch-lshw.sh` scripts download
static binaries from individual third-party GitHub accounts. The default FOS-based build does not use them.
Do not ship a product that does until each binary is pinned by checksum or replaced by a distro package.

## Not included, and not licensed to you by this project

- **Windows.** Brume images machines; it does not supply, activate or license Windows. Customers must hold
  valid licences for every image they deploy (for example volume licensing with KMS or MAK activation).
  OEM licences are normally tied to the device they shipped with. Never distribute Windows images or keys.
- **Drivers.** Vendor driver packs (for example Dell) carry the vendor's terms. Brume syncs them on the
  customer's own appliance and does not redistribute them.

## Trademarks

Ubuntu and Canonical are trademarks of Canonical Ltd. FOG is a project of the FOG Project. Microsoft, Windows,
BitLocker and Entra are trademarks of Microsoft. Brume and JOS are independent and are not affiliated with or
endorsed by any of them. "Based on Ubuntu" is a factual description, not a claim of endorsement.

## Source offer

For any GPL component that Brume installs or packages, the corresponding source is available from the upstream
location listed above (pinned to the exact version used). If you receive a Brume-built image and cannot obtain
the source from upstream, contact the maintainer.
