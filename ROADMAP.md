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

# Core Components

## JOS

A Secure Boot-compatible replacement for an imaging platform's traditional boot environment.

Responsibilities:

- Microsoft-compatible Secure Boot chain
- Signed Linux boot path
- Imaging platform compatibility
- Hardware support
- Secure Boot operation

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
BITLOCKER_CONFIGURED
    ↓
ENTERPRISE_READY
    ↓
DIRECTORY_JOINED
    ↓
GROUPS_ASSIGNED
    ↓
POLICIES_APPLIED
    ↓
ESCROW_VERIFIED
    ↓
COMPLETE
```

Each transition should be auditable.

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

    join_account:
        username: svc_join
        password: encrypted

    target_container:
        Provisioning
```

JOG should support deferred joining where directory services are unavailable.

---

# Supported Provisioning Modes

## Isolated Provisioning

Workflow:

```text
Image
Drivers
Hostname
BitLocker
Shutdown
```

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
