# JOG (Jonathan's Opensource Ghost) JOS (Jonathan's OS)

> A Secure Boot-compatible replacement for FOS that preserves FOG workflows while eliminating the need for per-device key enrolment.

**Type:** Infrastructure  
**Intent:** Pillar  
**Audience:** Sysadmins, Desktop Engineers, Field Technicians

---

# Overview

JOS is a drop-in replacement for the FOG Operating System (FOS).

It does **not** replace FOG itself.

The objective of JOS is simple:

> Provide complete FOS behavioural compatibility while booting on Secure Boot-enabled hardware using the standard Microsoft → Canonical trust chain.

The existing FOG server remains untouched:

- Web UI
- Database
- Storage nodes
- Scheduler
- Imaging workflows
- Task management

From FOG's perspective, JOS should behave exactly like FOS.

The only difference is that JOS boots through a modern Secure Boot-compatible chain rather than relying on custom key enrolment.

---

# Why JOS Exists

FOG remains one of the most effective imaging platforms available, but modern hardware increasingly enforces Secure Boot.

Traditional FOS deployments typically require:

- Secure Boot to be disabled, or
- Custom key enrolment on every machine

Neither approach scales well in enterprise environments.

JOS removes this operational burden by leveraging:

```text
Microsoft-signed shim
        ↓
Canonical-signed GRUB
        ↓
Canonical-signed Linux kernel
        ↓
JOS runtime
        ↓
Existing FOG workflows
```

The result is a FOG-compatible imaging client that works on Secure Boot systems without requiring machine-by-machine trust configuration.

---

# Design Philosophy

JOS is deliberately conservative.

Rather than creating a new imaging platform, it focuses on preserving the existing FOG ecosystem and solving a single problem extremely well.

Core principles:

- Preserve FOG compatibility
- Minimise divergence from upstream FOG
- Maintain simple rollback paths
- Eliminate custom Secure Boot key management
- Remain auditable and predictable
- Reduce technician effort

Success is measured by invisibility.

If technicians cannot tell the difference between FOS and JOS, the project has succeeded.

---

# Terminology

| Name | Description |
|--------|------------|
| **FOG** | The imaging server platform. Unmodified upstream. |
| **FOS** | FOG's client runtime consisting of its Linux kernel and fog.\* userland scripts. |
| **JOS** | The Secure Boot-compatible FOS replacement built around a Canonical-signed kernel and Microsoft-trusted boot chain. |
| **JOG** | The complete imaging appliance consisting of Ubuntu, FOG, and JOS running on portable hardware. |

---

# Architecture

```text
          +-------------------------+
          |         FOG Server      |
          |                         |
          |  Web UI                 |
          |  Database               |
          |  Scheduler              |
          |  Storage Nodes          |
          +------------+------------+
                       |
                       |
                       ▼
          +-------------------------+
          |          JOS            |
          |                         |
          |  FOS-compatible         |
          |  Userland               |
          |                         |
          |  Secure Boot Chain      |
          +------------+------------+
                       |
                       |
                       ▼
               Imaging Workflows
```

FOG remains unchanged.

JOS replaces only the client boot environment.

---

# Secure Boot Chain

JOS uses a standard trust path already recognised by modern enterprise hardware.

```text
UEFI Firmware
      ↓
Microsoft-Signed Shim
      ↓
Canonical-Signed GRUB
      ↓
Canonical-Signed Linux Kernel
      ↓
JOS Runtime
      ↓
FOG Imaging Operations
```

Benefits include:

- No BIOS changes
- No Secure Boot disablement
- No custom PKI deployment
- No MOK enrolment workflows
- No machine-by-machine configuration

---

# Repository Structure

This repo is the **integration point** for two separate repos, included as git submodules and pinned to known-good commits:

| Submodule | Repo | Role |
|---|---|---|
| `jog/` | [splippers/jog](https://github.com/splippers/jog) | **Server side.** The Ubuntu imaging laptop: autoinstall, FOG install, isolated DHCP/TFTP, kiosk, `jog-doctor.sh`. |
| `jos/` | [splippers/jos](https://github.com/splippers/jos) | **Client side.** The Secure Boot-compatible FOS replacement: `build/build-from-fos.sh`, GRUB menu and `scripts/jos-stage-boot.sh`, local-boot fallback, `scripts/test-secureboot-vm.sh`, FOS parity checklist. |
| `docs/JOG-JOS-RESEARCH.md` | this repo | Research and decision log: Secure Boot findings, design rationale, test results, roll-out plan. |

```text
jog-jos/
├── jog/     laptop: installs and configures FOG, dnsmasq/TFTP, kiosk
├── jos/     client: builds the initrd, stages the signed boot chain
└── docs/    cross-cutting research
```

**Which repo do I change?** If it installs or configures something on the laptop, it goes in `jog`. If it runs on, or builds for, the machine being imaged, it goes in `jos`. If it is about how the two fit together, it goes here.

**Typical flow**

```bash
git clone --recurse-submodules https://github.com/splippers/jog-jos.git && cd jog-jos
jos/build/build-from-fos.sh                          # build jos/build/out/initrd.img
sudo JOS_DIR=$PWD/jos jog/install/jog-install.sh     # install the laptop stack
sudo jog-stage-jos-boot.sh                           # stage shim, GRUB, signed kernel, initrd, modules, menu
jog/scripts/jog-doctor.sh                            # validate
```

**Updating a pin:** `git -C jos pull origin main && git add jos && git commit -m "Bump jos"` (same for `jog`).

The previous combined tree is preserved at tag `pre-split`.

---

# Compatibility Objective

JOS is not attempting to reimagine FOG.

The goal is complete functional parity.

| Capability | FOS | JOS Target |
|------------|-----|------------|
| Host Registration | ✅ | ✅ |
| Inventory Collection | ✅ | ✅ |
| Image Deployment | ✅ | ✅ |
| Image Capture | ✅ | ✅ |
| Tasking | ✅ | ✅ |
| Storage Communication | ✅ | ✅ |
| Multicast Imaging | ✅ | ✅ |
| Debug Shells | ✅ | ✅ |
| Secure Boot Operation | ❌ | ✅ |
| Zero-Touch Deployment | ✅ | ✅ |

---

# Engineering Risks

## Upstream FOS Drift

The largest long-term risk is behavioural divergence.

If FOG introduces:

- New fog.* scripts
- Additional environment variables
- Modified workflows
- New task types

JOS must maintain compatibility.

For this reason, parity testing remains a primary engineering concern.

---

## Hardware Compatibility

JOS inherits Ubuntu kernel support.

Potential edge cases include:

- RAID controllers
- Legacy storage adapters
- USB Ethernet devices
- Vendor-specific hardware

Any scenario where:

```text
Works in FOS
Fails in JOS
```

must be treated as a defect.

---

## Kernel Lifecycle Management

JOS is intentionally aligned with Canonical-supported kernels.

This provides:

- Strong hardware support
- Security updates
- Signed boot assets

However, each LTS and HWE transition requires validation and regression testing.

---

# Relationship To JOG

JOS forms the client-side runtime of the broader JOG ecosystem.

JOG provides:

- Portable Ubuntu appliance
- Native FOG installation
- Isolated PXE environment
- Secure Boot-aware staging
- Imaging workflow automation

JOS provides:

- Secure Boot-compatible client booting
- FOS-compatible execution environment

Together:

```text
JOG
 ├─ Ubuntu
 ├─ FOG
 └─ JOS

        +
Modern UEFI Hardware

        =
Zero-Touch Secure Boot Imaging
```

---

# Project Goals

The project is considered successful when:

- FOG cannot distinguish JOS from FOS
- Secure Boot remains enabled
- No custom keys are enrolled
- Technicians require no additional training
- Existing imaging workflows remain unchanged

The ideal deployment experience is:

```text
Enable PXE Boot
Press F12
Select Network Boot
Walk Away
```

---

# Vision

JOS is not a replacement for FOG.

It is a compatibility layer that allows FOG to operate naturally in modern Secure Boot environments.

The project prioritises:

- Predictability over novelty
- Compatibility over reinvention
- Operational simplicity over technical cleverness

The best compliment JOS can receive is:

> "Nobody noticed it was there."

Because if imaging feels boring, it is working.
