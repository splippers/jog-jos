# ROADMAP.md

# JOG / JOS Roadmap

> A Secure Boot-capable, FOG-compatible deployment platform designed to transform a blank device into an enterprise-ready asset with minimal technician intervention, complete transparency, and strong operational safeguards.

---

# Design Note

All domains, hostnames, site codes, organisational units, group names, IP ranges, and other identifiers referenced in this document are examples only.

JOG is designed to be:

- Organisation agnostic
- Directory agnostic
- Location agnostic
- Environment configurable

Deployment-specific values should always be supplied through appliance configuration rather than hardcoded into scripts or workflows.

---

# Vision

JOG exists to make enterprise device deployment:

- Predictable
- Repeatable
- Observable
- Secure
- Low-touch

JOG is not intended to replace existing imaging platforms.

Instead it extends and modernises them by providing:

- Secure Boot compatibility
- Automated provisioning
- Enterprise integration
- Rich operational telemetry
- Safe network isolation

Success is measured by the technician workflow:

```text
Connect equipment.
Boot devices.
Walk away.
```

---

# Repositories and Ownership

The project is split across three repositories. Each roadmap item belongs to exactly one.

| Repo | Owns | Runs on |
|---|---|---|
| [`jos`](https://github.com/splippers/jos) | The client runtime: Secure Boot boot chain, initrd, GRUB menu, FOS parity, local-boot fallback, hardware (driver) support | the machine being imaged |
| [`jog`](https://github.com/splippers/jog) | The appliance: installer, FOG, DHCP/TFTP, network safety, Operations Centre, `jog-doctor`, configuration | the imaging laptop |
| [`jog-jos`](https://github.com/splippers/jog-jos) | Integration: pins `jog` and `jos`, end-to-end tests, this roadmap, research | n/a |
| *(proposed)* `jog-provisioner` | The Windows-side provisioning service and the directory join broker (see Provisioning Framework) | the imaged machine / corporate network |

---

# Status at a Glance

Legend: **Done** (built, not necessarily hardware-proven) · **Partial** · **Planned** · **Open** (design decision needed).

| Area | Status | Notes |
|---|---|---|
| Secure Boot chain (shim → signed GRUB → signed kernel → JOS) | Done | Validated in the QEMU Secure Boot VM test; real-hardware validation ongoing |
| FOS userland and FOG protocol compatibility | Done | JOS runs the unmodified FOS userland |
| FOS menu modes (register, inventory, debug, wipe, disk tests, PhotoRec, password reset) | Done | Staged by `jos/scripts/jos-stage-boot.sh` |
| Hardware-inventory image selection (Capone) | Done | Needs the Capone plugin and mappings on the FOG server |
| Boot from local disk when the firmware has no entry | Done | `jos-localboot.sh` creates UEFI entries from local ESPs |
| Local disk first in UEFI boot order after imaging | Done | Post-download script on the FOG server |
| Network isolation of imaging services (USB NIC, nftables) | Partial | Static isolation exists; active production-network detection is Planned |
| Kiosk and appliance installer | Partial | Wizard and autoinstall exist; `jog-setup` and `jog.yaml` are Planned |
| `jog-doctor` | Partial | Checks the staged TFTP boot chain only |
| Operations Centre | Partial | Live imaging view built (queued/imaging/complete/failed, per-device progress; needs FOG API tokens, verified with demo and mock data, not a live task). Remaining requirements below are not built |
| Provisioning framework, directory join, BitLocker, drivers, analytics | Planned | Nothing built |

---

# Roadmap Phases

**Now: JOS parity and hardening.** Everything here gates the rest.
- Full FOS/FOG feature parity, proven on hardware (see JOS below).
- Hardware coverage: signed-module support for the NICs and storage controllers in use.
- Align the existing appliance with this document (DHCP lease, doctor checks, configuration).

*Exit criteria:* every parity item passes on at least one Secure Boot machine per supported vendor, and a Secure Boot VM test runs in CI.

**Next: Appliance platform.**
- `jog.yaml` configuration and `jog-setup`, with `jog.env` migrated.
- Network Safety Framework: production-network detection, lockdown and recovery.
- Operations Centre: status header, storage, imaging metrics, audit log.
- Extended `jog-doctor`.

*Exit criteria:* a technician can install, configure and monitor an appliance without editing files.

**Later: Provisioning.**
- Provisioning service and state machine, naming, drivers.
- Directory join and group assignment via the join broker.
- BitLocker, escrow, fleet analytics.

*Exit criteria:* a device moves from blank disk to `COMPLETE` with no technician input beyond booting it.

---

# Core Components

## JOS

A Secure Boot-compatible replacement for an imaging platform's traditional boot environment.

Responsibilities:

- Microsoft-compatible Secure Boot chain
- Signed Linux boot path
- Imaging platform compatibility
- Hardware support
- Secure Boot operation

### Hard requirement: full FOS and FOG compatibility

Secure Boot support is the reason JOS exists. It must be the **only** difference from FOS. Anything FOS can do, JOS must do, and the FOG server must not need to know the difference. A parity gap is a bug, not a limitation.

JOS runs the unmodified FOS userland under a Canonical-signed kernel, so most parity comes from the userland. The remaining risk is the kernel: FOS builds its drivers into its own kernel, while JOS must supply signed modules for every device. Parity is tracked in `jos/docs/fos-fog-parity-checklist.md`.

| Capability | Status |
|---|---|
| Unicast deploy and capture (partclone, all filesystems partclone supports) | Done, hardware proof pending |
| Multicast deploy (udpcast) | Done, hardware proof pending |
| Host registration (full, quick) and inventory | Done |
| System information, debug mode, send/restore debug | Partial: debug mode done; send/restore debug menu entries Planned |
| Disk wipe (fast, normal, full), surface test, Test Disk, PhotoRec, Windows password reset | Done |
| Capone (image by hardware) | Done |
| Boot from local disk | Done |
| Secure Boot key enrolment (FOS kernel) | Not needed under JOS |
| Deploy image (login, choose image), join multicast session, update product key | Done: console clients calling the same `boot.php` endpoint; failure paths tested, success paths need a registered host and credentials on hardware |
| Quick host deletion, approve host | Not present in the FOG server version the appliance installs, so nothing to replicate; re-check on FOG upgrades |
| Memtest | Open: unsigned, so Secure Boot must be off |
| Wireless and GPU drivers | Not applicable to imaging |

Compatibility is verified against the FOG version the appliance installs, and re-verified whenever the FOS release pin is bumped.

---

## JOG

A deployment appliance consisting of:

```text
Linux Distribution
+
Imaging Platform
+
JOS
+
Provisioning Framework
+
Operations Centre
```

Responsibilities:

- PXE boot
- DHCP
- DNS
- TFTP
- Imaging
- Driver deployment
- Provisioning automation
- Enterprise integration
- Monitoring
- Safety controls

---

# Guiding Principles

## Infrastructure First

JOG should focus on infrastructure reliability rather than user-facing complexity.

---

## Minimal Technician Interaction

Technicians should only provide information that cannot be derived automatically.

---

## Complete Transparency

Every significant activity should be visible through the Operations Centre.

---

## Safe By Default

JOG should actively prevent misconfiguration and protect adjacent networks.

---

## State-Driven Provisioning

Every device should move through well-defined deployment stages rather than relying on one-off scripts.

---

# Deployment Lifecycle

Devices shall progress through the following state machine:

```text
BLANK_DISK
    ↓
IMAGE_APPLIED
    ↓
DRIVERS_INSTALLED
    ↓
HOSTNAME_ASSIGNED
    ↓
ENTERPRISE_READY
    ↓
DIRECTORY_JOINED
    ↓
GROUPS_ASSIGNED
    ↓
POLICIES_APPLIED
    ↓
BITLOCKER_CONFIGURED
    ↓
ESCROW_VERIFIED
    ↓
COMPLETE
```

Each transition should be auditable.

**Ordering rule:** BitLocker is enabled only after a successful directory join, so that recovery keys can be escrowed to the directory as part of the same step. `BITLOCKER_CONFIGURED` is never reached before `DIRECTORY_JOINED`. A device waiting in `ENTERPRISE_READY` is therefore not yet encrypted (see Open Questions).

---

# Provisioning Framework

## Overview

A dedicated provisioning service will replace:

- Login scripts
- Chained batch files
- Manual execution steps
- Repeated technician interaction

The service shall:

- Resume automatically after reboot
- Track progress
- Retry failed stages
- Continue processing when dependencies become available
- Remove itself when complete

---

# Provisioning State Storage

Example:

```json
{
  "Version": 1,
  "State": "ENTERPRISE_READY",
  "ComputerName": "LT-SITE01-ABC1234"
}
```

Stored at:

```text
C:\ProgramData\JOG\Provisioning.json
```

---

# Automatic Logon Strategy

A dedicated provisioning account shall be used.

Example:

```text
JOGProvisioner
```

Properties:

- Local administrator
- Automatic logon
- Hidden from login UI
- Not intended for user operation

The provisioning account remains active until:

```text
COMPLETE
```

Upon completion:

```text
Disable AutoLogon
Remove Provisioning Account
Archive Logs
Shutdown
```

Hardening requirements:

- The account password is random and unique per device, never a shared or fixed value.
- It must not be stored in plain text (for example the `DefaultPassword` registry value); use an LSA-secret-based mechanism.
- The account has a hard expiry, so a device that never reaches a corporate network does not keep an administrator autologon indefinitely. Devices that expire in `ENTERPRISE_READY` disable the account and require a technician to resume provisioning.

---

# Device Naming Framework

Device names shall be generated automatically.

Sources may include:

- Device type
- Site code
- Serial number
- Service tag
- Configuration profile

Example pattern:

```text
<DeviceType>-<SiteCode>-<SerialNumber>
```

Examples:

```text
LT-SITE01-ABC1234

DT-SITE02-XYZ5678
```

Naming formats shall be configurable.

---

# Site Profiles

Each JOG appliance maintains a configurable site profile.

Example:

```yaml
site:
    name: Main Office
    code: SITE01

organisation:
    name: Example Organisation
```

Changing deployment locations should require only configuration updates.

---

# Directory Services Integration

Configuration example:

```yaml
directory_services:
    domain: corp.example.local

    credential:
        method: broker          # broker | offline_join | stored
        reference: jog-join     # name of a sealed credential, never the secret itself

    target_container:
        Provisioning
```

JOG should support deferred joining where directory services are unavailable.

## Directory Credential Handling

The account that joins computers and adds them to groups is the most sensitive secret in the system. Rules:

- No privileged directory credential is ever placed in an image, in the FOG database, in `Provisioning.json`, in `jog.yaml`, in `jog.env`, or in version control.
- An imaged device never holds a reusable credential. Whatever it holds must be useless after the join.
- The account is delegated least-privilege: create computer objects in the target container only, and add members to the named groups only. It is never a domain admin.
- Use of the credential is audited.

Proposed methods, in order of preference:

1. **Join broker (recommended).** A small service on the corporate network (or on the appliance while it is connected) holds the delegated account. A device proves its identity with a one-time, per-device token issued at imaging time, and asks the broker to join it and add it to groups. The device never sees the credential. This is the only method that also covers group assignment without giving the device privilege.
2. **Offline domain join.** Computer accounts are pre-created and exported with `djoin /provision`; the blob contains only the machine account secret. No privileged credential reaches the device or the appliance, but device names must be known in advance.
3. **Stored credential (fallback).** The account is kept on the appliance, sealed to its TPM (for example with `systemd-creds`) or protected by a passphrase entered at boot, readable by root only, and delivered to the device over TLS at join time, then discarded. Weakest option; document the exposure if used.

Which method ships first is an open decision (see Open Questions).

---

# Supported Provisioning Modes

## Isolated Provisioning

Workflow:

```text
Image
Drivers
Hostname
Shutdown
```

BitLocker is deferred until the device has joined the directory.

Result:

```text
ENTERPRISE_READY
```

No dependency on:

- Directory services
- Internet connectivity
- External infrastructure

---

## Connected Provisioning

Workflow:

```text
Image
Drivers
Hostname
Directory Join
Groups
Policies
BitLocker
Escrow
Complete
```

BitLocker only runs once the directory join has succeeded.

Requires:

```text
Directory Services
DNS
Policy Infrastructure
```

---

# Enterprise Network Detection

The provisioning service shall continuously test for:

```text
DNS Resolution

Directory Services

Authentication Services

Required Network Endpoints
```

Possible methods:

```text
Directory Controller Discovery

DNS Suffix Detection

Connectivity Verification
```

---

# ENTERPRISE_READY State

If enterprise services are unavailable:

```text
Device has been successfully prepared.

Status:
Enterprise Ready

Waiting for corporate network connectivity.
```

Options:

```text
Store Device

Connect To Corporate Network

Diagnostics

Restart

Shutdown
```

---

# Driver Management

Initial implementation:

```text
Local Appliance Driver Repository
```

Examples:

```text
SMB

NFS

HTTPS Repository
```

Driver selection based on:

```text
Manufacturer

Model

Hardware Identifiers
```

---

# BitLocker Framework

Default configuration:

```text
TPM + PIN
```

BitLocker is enabled only after `DIRECTORY_JOINED`, and `COMPLETE` requires `ESCROW_VERIFIED`: the recovery key must be confirmed in the directory before the device is considered done.

Auto-generated PINs need a defined delivery path (to the device owner, not stored on the appliance). Until that is designed, `auto_generate` is a placeholder.

Capabilities:

```text
Automatic PIN Generation

Protector Creation

Recovery Key Management

Escrow Verification
```

Example:

```yaml
bitlocker:
    enabled: true

    mode: TPM_PIN

    pin:
        auto_generate: true
        length: 8
```

---

# Security Group Assignment

Provisioning policy may define default group memberships.

Example:

```yaml
groups:
  - StandardWorkstations
  - EndpointProtection
  - DeviceEncryption
```

Assignments occur automatically following directory integration.

---

# Configuration Platform

Primary configuration file:

```text
/etc/jog/jog.yaml
```

*Current state:* the appliance is configured through `/etc/jog/jog.env` and `installer/jog-install-wizard.sh`. `jog.yaml` and `jog-setup` are Planned in the Next phase. `jog.env` stays supported until a migration tool converts it, so existing appliances keep working.

Categories:

```text
Organisation

Site

Networking

Imaging

Directory Services

Provisioning

Drivers

BitLocker

Updates

Monitoring
```

---

# Initial Setup Wizard

Command:

```bash
jog-setup
```

Collects:

```text
Organisation Name

Site Name

Site Code

Directory Services Information

Provisioning Mode

BitLocker Settings

Storage Locations
```

Generates a complete appliance configuration.

---

# JOG Doctor

*Current state:* `jog-doctor` exists and checks the staged TFTP boot chain (shim, GRUB, signed kernel, initrd, modules, kernel/module match). The checks below are the Planned extension.

Command:

```bash
jog-doctor
```

Validates:

```text
Imaging Services

Database

Storage

Driver Repository

Provisioning Configuration

Network Configuration

Directory Services Connectivity

BitLocker Configuration
```

Results available via:

- Command line
- Dashboard
- Exportable reports

---

# Network Safety Framework

## Principles

JOG must actively prevent network disruption.

Protection should not rely solely on operator behaviour.

---

## Imaging Network

Permitted services:

```text
DHCP

DNS

TFTP

PXE
```

Bound exclusively to:

```text
Imaging Interface
```

---

## Corporate Network Monitoring

Detection is passive wherever possible. Active probes (for example a DHCP discover) can themselves disturb a production network and must be opt-in. The signals that trigger lockdown must be listed in the configuration, and the design must state how false positives and false negatives are handled.

JOG continuously evaluates:

```text
Existing DHCP Servers

Default Gateways

Known DNS Domains

Directory Services Availability

Corporate Address Ranges
```

---

## Safety Lockdown

If the imaging interface appears connected to a production network:

```text
Stop DHCP

Stop PXE

Stop TFTP

Display Critical Warning

Record Event
```

Immediately.

---

## Automatic Recovery

Following disconnection:

```text
Verify Isolation

Restart Services

Clear Warning State
```

Automatically.

---

# Safety Messaging

## Normal State

```text
SAFE ISOLATED MODE

Imaging services restricted to designated
deployment interfaces.
```

---

## Critical State

```text
CRITICAL WARNING

Imaging Interface Appears Connected
To A Production Network.

All Imaging Services Have Been Disabled.

Disconnect Immediately.
```

---

# Corporate Network Warning

Whenever the appliance is connected to a corporate network:

```text
WARNING

Do Not Connect This Appliance To A
Corporate Network Unless Authorised
By The Appropriate Network Administration Team.

Imaging Services Remain Restricted
To Deployment Interfaces.
```

---

# DHCP Standards

Default lease duration:

```text
5 Minutes
```

*Current state:* the appliance ships with a 12-hour lease (`JOG_DHCP_LEASE_HOURS=12`). Moving to 5 minutes is a Planned change in `jog`; the lease length becomes configurable and the default changes with the `jog.yaml` migration.

Example:

```ini
dhcp-range=10.10.10.100,10.10.10.200,5m
```

Benefits:

- Faster cleanup
- Reduced stale leases
- Better device tracking
- Lower operational risk

---

# Operations Centre

The appliance shall automatically log into:

```text
JOG Operations Centre
```

Displayed full-screen in kiosk mode.

No desktop interaction required.

---

# Operations Centre Requirements

## Global Status Header

Always visible.

Displays:

```text
Site

Date

Time

Uptime

Network Status

Update Status

Storage Status
```

---

# Storage Visibility

Monitor:

## System Storage

```text
Capacity

Used

Available

Health

Temperature
```

## Repository Storage

```text
Capacity

Used

Available

Image Count

Repository Health
```

---

# Update Visibility

Display:

```text
Security Updates

Recommended Updates

Held Updates

Reboot Required

Last Refresh
```

---

# Enterprise Connectivity

Display:

```text
Corporate Network Status

Directory Services Reachability

Internet Connectivity

DNS Status
```

---

# Imaging Metrics

Display:

```text
Queued Devices

Imaging Devices

Provisioning Devices

Completed Devices

Failed Devices
```

---

# Performance Metrics

Display:

```text
Disk Throughput

Network Throughput

Multicast Performance

CPU Usage

Memory Usage

Temperature
```

---

# Provisioning Metrics

Display:

```text
Awaiting Network

Enterprise Ready

Provisioning

Completed

Failed
```

---

# Device Pipeline View

Per-device status:

```text
Image Applied

Drivers Installed

Hostname Assigned

Directory Joined

Groups Applied

Policies Applied

Encryption Configured

Escrow Verified

Complete
```

---

# Audit Logging

Record:

```text
PXE Requests

Imaging Events

Provisioning Events

Encryption Events

Directory Events

Failures

Warnings

Safety Lockdowns

Connectivity Changes
```

Logs should be:

```text
Searchable

Exportable

Timestamped
```

---

# Future Enhancements

## Image Distribution

Investigate:

```text
Versioned Images

Image Catalogues

Delta Updates

Remote Replication
```

Large image transfers should be infrequent and deliberate.

---

## Driver Repository Management

Investigate:

```text
Automated Driver Updates

Vendor Integration

Repository Validation
```

---

## Fleet Analytics

Display:

```text
Devices Built Today

Devices Built This Week

Average Deployment Time

Average Provisioning Time

Estimated Technician Time Saved
```

---

# Open Questions

Decisions needed before the Later phase starts:

1. **Directory credential method:** which of broker, offline join or stored credential ships first, and who operates the broker.
2. **FOG Client overlap:** FOG's own client and snapins already handle hostname, directory join and post-image tasks. Decide whether the provisioner builds on them or replaces them, and how the two coexist so they do not fight over the hostname or the join.
3. **Devices at rest before join:** a device waiting in `ENTERPRISE_READY` is unencrypted and may hold an autologon account. Decide whether a TPM-only BitLocker interim state is acceptable, or whether such devices are kept physically controlled.
4. **BitLocker PIN delivery:** how an auto-generated PIN reaches the device owner without being stored on the appliance, and what happens in isolated mode where no escrow target exists.
5. **Recovery key storage in isolated mode:** if keys are ever held on the appliance, how that store is encrypted and who can read it.
6. **Where the provisioner lives:** a new `jog-provisioner` repo or a directory inside `jog`.
7. **Non-Windows images:** the provisioning section is Windows-specific. Decide whether Linux images are in scope.
8. **Hardware coverage policy:** which vendors and models JOS must support, and how new NIC and storage drivers are added and signed-module-verified.
9. **Testing:** the provisioner needs a test strategy (virtual machines with a lab directory) alongside the existing Secure Boot VM test.

---

# Long-Term Objective

A device should progress from:

```text
Blank Storage Device
```

to:

```text
Imaged

Configured

Correctly Named

Driver Complete

Encrypted

Directory Integrated

Policy Compliant

Deployment Ready
```

with minimal technician intervention and complete visibility throughout the process.

---

# Guiding Principle

> JOG exists so that doing the right thing is also the easiest thing.

If deployment feels boring, it is working.
