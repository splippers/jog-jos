# JOS — a Secure Boot-compatible replacement for FOS

Type: Infrastructure | Intent: Pillar | Audience: Sysadmins

**JOS** replaces **FOS**, the client environment FOG PXE-boots to image machines. It does not replace FOG:
the FOG server (web UI, database, storage nodes, scheduler) is used as-is. The goal is that JOS does everything
FOS does, so FOG cannot tell the difference, while booting on machines with Secure Boot enabled and no
per-machine key enrolment.

## Terms

| Name | What it is |
|------|------------|
| **FOG** | The imaging server. Unmodified upstream. |
| **FOS** | FOG's stock client OS: its own kernel plus a userland of `fog.*` scripts. Needs its signing key enrolled on each Secure Boot machine. |
| **JOS** | FOS's userland on a Canonical-signed kernel, booted via Microsoft-signed shim. Built by `jos/build/build-from-fos.sh`. This is the project. |
| **JOG** | Not a FOG replacement. Historic name for the optional helper that installs stock FOG on a laptop with DHCP/TFTP confined to a USB NIC. Everything outside `jos/` (plus `scripts/jog-stage-jos-boot.sh`, `jog-doctor.sh`, `test-secureboot-vm.sh`) is this helper. |

## Where things are

- `jos/` — JOS: build script, docs, FOS-parity checklist. `jos/initrd/` is the retired shell client, kept for reference.
- `scripts/jog-stage-jos-boot.sh` — puts the signed chain (shim, GRUB, kernel, JOS initrd, matching modules, a FOS-style boot menu) into the TFTP root.
- `scripts/jog-doctor.sh` — checks the staged chain. `scripts/test-secureboot-vm.sh` — boots it in QEMU with Secure Boot enforcing, with an unsigned-bootloader control.
- `docs/JOG-JOS-RESEARCH.md` — research, decisions, test results, remaining work.

---

# JOG (optional helper, not a FOG replacement)


A portable, isolated FOG imaging appliance designed for sensitive or regulated networks.

Type: Infrastructure / Appliance  
Intent: Pillar + Enabler  
Audience: Sysadmins, field technicians, IT operations

==================================================

OVERVIEW

JOG is a portable FOG server designed to run on a laptop or small machine and perform PXE imaging without interfering with a corporate or restricted LAN.

It exposes DHCP, TFTP, and PXE services exclusively on a dedicated USB Ethernet interface, while all internet access, updates, and management traffic remain on a separate interface (typically Wi‑Fi).

JOG is commonly paired with JOS clients for zero‑touch imaging workflows.

This repo now also contains JOS (the client runtime) under `jos/`. Consolidated research, Secure Boot findings and the roll-out plan: `docs/JOG-JOS-RESEARCH.md`.

==================================================

WHY JOG EXISTS

Traditional PXE imaging setups are often banned or heavily restricted in corporate environments because they risk:

- rogue DHCP servers
- broadcast leakage
- accidental interference with production networks

JOG exists to provide a physically and logically isolated imaging solution that technicians can deploy safely, quickly, and repeatedly.

==================================================

CORE DESIGN PRINCIPLES

PHYSICAL ISOLATION  
DHCP and PXE services bind only to a USB Ethernet NIC. They never listen on onboard Ethernet or Wi‑Fi.

NETWORK SEPARATION  
Imaging traffic and client booting are confined to a private RFC1918 subnet. Updates and admin access use a different interface.

SECURE BOOT AWARE  
EFI staging uses signed Ubuntu boot assets suitable for modern UEFI systems.

ZERO‑TOUCH CLIENT FLOW  
Clients boot, discover the server via DHCP NEXT SERVER, chain into JOS, register, inventory, and image without prompts.

OPERATOR VISIBILITY  
A local kiosk surfaces FOG management and system status continuously during imaging sessions.

==================================================

TYPICAL TECHNICIAN WORKFLOW

1. Plug USB Ethernet adapter into the JOG laptop
2. Connect target machine to the USB imaging network
3. On target: press F12 and boot from IPv4
4. Walk away

JOG provides DHCP, chains iPXE, and hands off to JOS. JOS registers with FOG and executes imaging automatically.

==================================================

CORPORATE LAN SAFETY

JOG enforces safety through configuration, not policy:

- dnsmasq is bound to the USB imaging interface only
- no DHCP sockets on Wi‑Fi or onboard NICs
- optional nftables rules to block forwarding
- routing metrics ensure imaging traffic never becomes the default route

These constraints are explicit and auditable.

==================================================

INSTALLATION MODEL

JOG is installed using Ubuntu Server autoinstall images with a first‑boot wizard.

Two primary patterns are supported:
- Interactive wizard on first boot (recommended for laptops)
- Fully unattended single‑ISO installs (labs / VMs)

The wizard applies:
- network configuration
- EFI boot staging
- dnsmasq rendering
- native FOG installation
- optional kiosk setup

==================================================

FOG INTEGRATION

FOG is installed natively under /opt/fog using the official installer.

JOG does not containerise FOG.

JOG’s role is to:
- prepare the environment
- constrain where FOG listens
- automate safe defaults
- make the stack portable

==================================================

KIOSK MODE

Optional kiosk mode launches a maximised Chromium session on X11 showing:

- FOG management interface
- optional task or stats views
- a local status dashboard

This is designed for reliability on Intel laptops and avoids Wayland‑related instability.

==================================================

RELATIONSHIP TO OTHER PROJECTS

JOG pairs directly with JOS clients.

Together they form a portable imaging system that:
- avoids corporate LAN impact
- supports Secure Boot
- scales from single laptops to small field teams

JOG may also surface its UI through NerveCentre when deployed in a fixed location.

==================================================

STATUS

Active and operational.

JOG is a field‑tested design that prioritises safety, predictability, and operator confidence over convenience.

==================================================

FINAL NOTE

JOG exists so that doing the right thing is also the easiest thing.

If imaging feels boring, it is working.
