# Corporate provisioning pipeline

> **Two phases, two clocks.**
>
> **Phase 1 — imaging:** PXE → JOS → FOG multicast → image written → post-download injection. The default
> JOS entry auto-joins a multicast session that is still in its join window. This is the phase with the
> 100-laptops-in-under-5-minutes target.
>
> **Phase 2 — provisioning:** Windows first boot → drivers → hostname → **handoff** → corporate resume →
> domain join → Entra hybrid join → AD groups → BitLocker → escrow verified → `COMPLETE`. This is a
> resumable state machine and is **not** part of the 5-minute imaging claim.

This document describes phase 2 and how the Haar appliance hands off to it. The default design is
**air-gapped**: imaging and driver installation finish on the isolated Haar network, then the device waits in
`AWAITING_CORPORATE` until it reaches the corporate network.

---

## 1. The pipeline at a glance

```text
                         PHASE 1 (Haar/JOS + FOG)
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │ PXE → shim → GRUB → signed kernel → JOS initrd                              │
 │      → FOG multicast / unicast deploy                                      │
 │      → image written to disk                                               │
 │      → post-download script mounts Windows partition                       │
 │      → copies C:\ProgramData\JOG\* + C:\Windows\Setup\Scripts\SetupComplete │
 └─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼  first Windows boot / OOBE
                         PHASE 2a (Haar Provisioner, SYSTEM)
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │ SetupComplete.cmd → Start-JOGProvisioning.ps1                               │
 │                                                                             │
 │  1. INITIALISE      ACLs, logs, state file, scheduled task                  │
 │  2. DRIVERS         manifest.json → VMD base pack + model pack → pnputil    │
 │  3. HOSTNAME        site + serial/model pattern → Rename-Computer           │
 │  4. HANDOFF         note + desktop shortcut + registry state                │
 │                     clears driver/join passwords from the config            │
 │                     → AWAITING_CORPORATE (AirGapped mode)                   │
 └─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼  device reaches Corporate
                         PHASE 2b (resume on corporate LAN)
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │ Resume-JOGCorporateEnrollment.ps1                                           │
 │      → checks DNS / DC / Entra endpoints                                   │
 │      → prompts for a delegated join account (Credential mode)               │
 │      → switches the config to Connected                                    │
 │      → Start-JOGProvisioning.ps1 -Resume                                   │
 │                                                                             │
 │  5. DOMAIN_JOIN     delegated credential or offline djoin blob              │
 │  6. HYBRID_JOIN     dsregcmd /status: AzureAdJoined + DomainJoined          │
 │  7. GROUPS          delegated net group / server-side Add-ADGroupMember     │
 │  8. BITLOCKER       TPM-only (default) or TPM+PIN                           │
 │  9. ESCROW          recovery password → AD and/or Entra ID, then verify     │
 │ 10. CLEANUP         remove secrets, unregister task, COMPLETE               │
 └─────────────────────────────────────────────────────────────────────────────┘
```

The device can reboot between stages. Every stage is idempotent and recorded in
`C:\ProgramData\JOG\Provisioning.json`.

---

## 2. State machine

```text
IMAGE_APPLIED
    ↓
DRIVERS_INSTALLED
    ↓
HOSTNAME_ASSIGNED
    ↓
AWAITING_CORPORATE          ← air-gapped default stops here
    ↓  (Resume-JOGCorporateEnrollment.ps1 on the corporate LAN)
DIRECTORY_JOINED
    ↓
HYBRID_JOINED
    ↓
GROUPS_ASSIGNED
    ↓
BITLOCKER_CONFIGURED
    ↓
ESCROW_VERIFIED
    ↓
COMPLETE
```

`Connected` mode skips `AWAITING_CORPORATE` and runs the corporate stages immediately. Use it only for a
device that can reach a domain controller and Entra during first boot, such as a lab VM.

Failure states are explicit and retryable:

| State | Meaning | Recovery |
|---|---|---|
| `DRIVERS_PENDING` | Driver share unreachable, `manifest.json` missing, or model pack absent | Fix the share / run the driver sync; the scheduled task retries at next boot |
| `HOSTNAME_PENDING` | Rename failed or a reboot is required | Let the scheduled task resume after the reboot |
| `AWAITING_CORPORATE` | Air-gapped handoff complete; no corporate stage has run | Connect to Corporate and run `Resume-JOGCorporateEnrollment.ps1` |
| `DOMAIN_JOIN_PENDING` | No line of sight, bad blob/credential, or OU permissions | Fix the dependency; run the resume script again |
| `HYBRID_JOIN_PENDING` | Domain joined but Entra ID registration not complete | Check `dsregcmd /status`, SCP, DNS, and line of sight; the task retries |
| `GROUPS_PENDING` | Delegation or group name problem | Fix the delegation; re-run the groups stage |
| `BITLOCKER_PENDING` | TPM not ready, policy blocks encryption, or escrow failed | Fix the policy/TPM; re-run the BitLocker stage |
| `FAILED` | Attempt limit reached | Technician inspects the log and re-runs with `-Force` |

**Ordering rule:** BitLocker is only enabled after a successful directory join, so the recovery password can
be escrowed as part of the same step. The device never reaches `BITLOCKER_CONFIGURED` before
`DIRECTORY_JOINED`.

**Air-gap rule:** a device in `AWAITING_CORPORATE` is not domain joined and is not BitLocker-encrypted. It is
safe to image and stage in a room, but it must not be treated as a finished corporate asset until the resume
phase has reached `COMPLETE`.

---

## 3. The payload

The FOG post-download script installs this directory on the Windows partition:

```text
C:\ProgramData\JOG\
├── Start-JOGProvisioning.ps1          # orchestrator / state machine
├── Write-JOGHandoff.ps1               # AWAITING_CORPORATE note, shortcut, sanitised config
├── Resume-JOGCorporateEnrollment.ps1  # corporate-LAN resume + join credential prompt
├── Install-JOGDrivers.ps1             # SMB driver pull, manifest, pnputil
├── Install-JOGDriverPack.ps1          # manual one-model handoff helper
├── Join-JOGDomain.ps1                 # credential/offline join, hybrid wait, groups
├── Enable-JOGBitLocker.ps1            # TPM-only/TPM+PIN + escrow + verify
├── Get-JOGProvisioningStatus.ps1      # technician status view
├── Sync-FOGDriverPacks.ps1            # workstation-side model API + catalog sync
├── jog-provisioning.json              # rendered configuration
├── Provisioning.json                  # live state (created at first run)
└── logs\                              # transcript + stage logs
```

`C:\Windows\Setup\Scripts\SetupComplete.cmd` calls the orchestrator once, during OOBE. The orchestrator
registers a `JOGProvisioning` scheduled task that runs at every startup until `AWAITING_CORPORATE` or
`COMPLETE`, so reboots resume the pipeline.

The scripts are PowerShell 5.1 compatible. They run as **SYSTEM**; there is no autologon and no stored
interactive user session.

---

## 4. Configuration

The appliance renders `/etc/jog/provisioning.env` into
`/images/postdownloadscripts/jog-provisioner/jog-provisioning.json`. The template is
`jog/config/jog-provisioning.env.example`.

```json
{
  "Version": 1,
  "Site": "SITE01",
  "Organization": "Example Corporation",
  "DeviceNamePattern": "LT-{Site}-{Serial}",
  "ProvisioningMode": "AirGapped",
  "Domain": "corp.example.com",
  "DomainNetbios": "CORP",
  "DomainJoin": {
    "Mode": "Credential",
    "BlobPath": "C:\\ProgramData\\JOG\\domainjoin.blob",
    "User": "",
    "Password": "",
    "OUPath": "OU=Workstations,OU=JOG,DC=corp,DC=example,DC=com"
  },
  "HybridJoin": {
    "Enabled": true,
    "TimeoutMinutes": 30
  },
  "Groups": [
    "JOG-Workstations",
    "EndpointProtection",
    "DeviceEncryption"
  ],
  "BitLocker": {
    "Enabled": true,
    "Mode": "TpmOnly",
    "PinLength": 6,
    "Escrow": "AD",
    "PinStorage": "None",
    "AllowAdPinStorage": false,
    "AdPinAttribute": "extensionAttribute15"
  },
  "DriverShare": {
    "Unc": "\\\\10.99.0.1\\Drivers",
    "ReadUser": "drivers",
    "ReadPassword": "CHANGE_ME",
    "ModelMap": {},
    "Fallback": "Default",
    "BasePacks": ["VMD"],
    "Manifest": "manifest.json"
  },
  "RebootBetweenStages": true,
  "DeleteConfigOnComplete": true,
  "ShutdownOnComplete": false,
  "MaxAttempts": 5
}
```

`ProvisioningMode` is `AirGapped` or `Connected`. If it is absent, the provisioner defaults to `AirGapped`.
`jog-corporate-setup.sh` and `jog-install-provisioner.sh` also default to `AirGapped`.

### Credentials

| Credential | Where it lives | Recommendation |
|---|---|---|
| Driver-share read account | `jog-provisioning.json` (ACL: SYSTEM/Administrators) | Read-only; removed by the handoff stage; rotate after provisioning |
| Domain join account | Prompted by the resume script; written to the ACL-protected config only for the join | Use a delegated, time-limited account; removed at `CLEANUP` |
| Offline join blob | `C:\ProgramData\JOG\domainjoin.blob` | One blob per computer account; suitable for a single device or per-device blobs |
| BitLocker PIN | Never in the config by default | User-held, DPAPI-sealed locally, or a secrets manager |
| AD write account for groups | Not on the device in offline mode | Run `Add-JOGComputerGroups.ps1` from a management host |

The provisioner ACLs `C:\ProgramData\JOG` to `SYSTEM` and `Administrators` at first run. The `HANDOFF` stage
removes the driver-share and domain-join passwords from the config before the device leaves the imaging
network. The resume script writes a join password back only for the duration of the corporate join, and
`CLEANUP` removes it again.

### Credential join vs offline join

**Credential join (default for a fleet):**

```powershell
Add-Computer -DomainName corp.example.com `
  -OUPath "OU=Workstations,OU=JOG,DC=corp,DC=example,DC=com" `
  -Credential $credential -Force -Options JoinWithNewName,AccountCreate
```

One `djoin` blob is tied to one computer account. A single blob therefore cannot be reused across a room of
laptops, which is why the default is a delegated credential. The resume script prompts for it on the
corporate network and does not leave it on the air-gapped device.

**Offline join (single device or per-device blob):**

```powershell
djoin.exe /requestODJ /loadfile C:\ProgramData\JOG\domainjoin.blob `
  /windowspath C:\Windows /localos
```

The computer account is pre-created by a domain administrator. No domain credential is stored on the
device. Group assignment is done server-side with `Add-JOGComputerGroups.ps1` (RSAT) or the join broker
described in `ROADMAP.md`. Use this mode only when the blob is unique to the device.

---

## 5. Stage details

### 5.1 Drivers

The appliance publishes driver packs from the FOG model inventory. On a Windows workstation with internet
access:

```powershell
.\Sync-FOGDriverPacks.ps1 -PlanOnly
.\Sync-FOGDriverPacks.ps1
```

`Sync-FOGDriverPacks.ps1`:

1. Queries the read-only Haar model API on the appliance (`http://192.168.254.1:8089/api/models`).
2. Resolves the latest Dell/HP driver-pack catalog entry for each registered model and target OS.
3. Downloads the vendor pack, verifies it, and extracts the INF tree.
4. Publishes it to `\\192.168.254.1\Drivers\<model-slug>` using the `driveradmin` account.
5. Writes `manifest.json` with the model, vendor, catalog ID, pack version, and install folders.

On the device, `Install-JOGDrivers.ps1`:

1. Reads `Win32_ComputerSystem` (manufacturer, model) and `Win32_BaseBoard` (product).
2. Normalises the model string, looks it up in `ModelMap`, and falls back to `Default`.
3. Maps `\\10.99.0.1\Drivers` with the read-only account.
4. Reads `manifest.json` and resolves the model pack.
5. Installs the `BasePacks` (default `VMD`, for `iaStorVD`) and the model pack.
6. `pnputil.exe /add-driver <dir>\*.inf /subdirs /install`.
7. Logs the INF names and exit codes, unmaps the share, and deletes the staging directory.

The share is the Samba `[Drivers]` share configured by `jog-driver-share.sh`. It is read-only for the
`drivers` account and writable only by `driveradmin`. Guest access can be enabled for legacy clients, but
Windows 11 24H2 blocks insecure guest SMB by default; use the `drivers` credentials.

If the share is unreachable or the manifest/model pack is missing, the stage sets `DRIVERS_PENDING` and the
scheduled task retries. The pipeline does not join the domain before drivers are installed, because a
missing storage/network driver can make the join unreachable.

### 5.2 Hostname

The default pattern is `LT-{Site}-{Serial}`. The serial is taken from `Win32_BIOS.SerialNumber` and
sanitised to 15 characters (the NetBIOS limit). `Rename-Computer` requires a reboot; the orchestrator
registers the resume task before restarting.

### 5.3 Handoff (air-gapped default)

`Write-JOGHandoff.ps1` runs after hostname and driver installation when `ProvisioningMode` is `AirGapped`:

- Writes `AWAITING-CORPORATE.txt` with the device name, model, serial, domain, and instructions.
- Puts `Haar - Awaiting Corporate.txt` and `Complete Corporate Enrollment.lnk` on the public desktop.
- Records `HKLM\SOFTWARE\JOG\State = AWAITING_CORPORATE`.
- Removes the driver-share and domain-join passwords from the config.
- Leaves `Provisioning.json` and the logs in place for the resume phase.

The device is now safe to move to Corporate. It has not joined the domain, has not been added to AD groups,
and is not BitLocker-encrypted.

### 5.4 Corporate resume

`Resume-JOGCorporateEnrollment.ps1` is the only supported way to finish an air-gapped device:

1. Self-elevates through UAC.
2. Resolves the configured domain and checks that a domain controller responds (`nltest /dsgetdc`).
3. Warns if the Entra hybrid-join endpoints are unreachable.
4. Prompts for the delegated join account in `Credential` mode (no prompt in `Offline` mode).
5. Switches `ProvisioningMode` to `Connected`.
6. Runs `Start-JOGProvisioning.ps1 -Resume`.

If the device restarts during the corporate stages, the `JOGProvisioning` startup task resumes from
`Provisioning.json` in `Connected` mode.

### 5.5 Domain join

`Join-JOGDomain.ps1` supports:

- `Mode = Credential`: `Add-Computer` with the delegated account.
- `Mode = Offline`: `djoin /requestODJ` from the injected blob.

After the join, the script verifies `dsregcmd /status` reports `DomainJoined : YES`.

### 5.6 Entra hybrid join

Hybrid join is not a separate installer. After the on-prem join and reboot:

1. The device must reach `enterpriseregistration.windows.net`, `login.microsoftonline.com`, and the
   configured SCP.
2. The `Automatic-Device-Join` scheduled task (or `dsregcmd /join`) performs the registration.
3. The provisioner polls `dsregcmd /status` until it sees:

```text
AzureAdJoined : YES
DomainJoined  : YES
DeviceAuthStatus : SUCCESS
```

If the timeout is reached, the state becomes `HYBRID_JOIN_PENDING` and the task retries at the next boot.
The device is not encrypted while it is waiting.

### 5.7 AD groups

For credential join, the provisioner runs `net group "<group>" "<computer>$" /add /domain` as the
delegated domain account (via `Start-Process -Credential`). For offline join, use the management-host
helper:

```powershell
.\Add-JOGComputerGroups.ps1 -ComputerName LT-SITE01-ABC1234 `
  -Groups JOG-Workstations,EndpointProtection,DeviceEncryption `
  -Credential (Get-Credential) -Server dc01.corp.example.com
```

Group membership is verified with `net group "<group>" /domain` before the state advances.

### 5.8 BitLocker

`Enable-JOGBitLocker.ps1`:

- Verifies the TPM is ready.
- Enables BitLocker with XTS-AES 256 and `UsedSpaceOnly`.
- `Mode = TpmOnly` (default): TPM protector only.
- `Mode = TpmPin`: TPM + PIN; the PIN is generated locally and is **not** written to AD by default.
- Adds a recovery-password protector.
- Escrows the recovery password to AD (`manage-bde -protectors -adbackup`) and/or Entra ID
  (`BackupToAAD-BitLockerKeyProtector`).
- Verifies the escrow before setting `ESCROW_VERIFIED`.

The full AD/PIN analysis is in [`BITLOCKER-AD.md`](BITLOCKER-AD.md). The short version: AD stores the
48-digit recovery password, not the six-digit startup PIN.

### 5.9 Cleanup

At `COMPLETE` the orchestrator:

- Deletes the rendered config and any DPAPI-sealed PIN file (unless the policy explicitly keeps it).
- Removes the driver-share credential.
- Unregisters the `JOGProvisioning` scheduled task.
- Leaves `Provisioning.json` and the logs for audit.
- Optionally shuts down (`ShutdownOnComplete`).

---

## 6. Prerequisites

### Directory / Entra

- [ ] AD domain and a target OU for workstations.
- [ ] A delegated join account (credential mode) **or** a pre-created computer account + per-device `djoin`
      blob.
- [ ] AD groups created; the join account can add members.
- [ ] Azure AD Connect device sync / hybrid join configured (SCP, DNS, line of sight).
- [ ] BitLocker schema present; the computer object can receive `msFVE-RecoveryInformation`.
- [ ] GPO: recovery information to AD, encryption method, TPM policy.
- [ ] If using Entra escrow: device registration + BitLocker key-backup policy.

### Appliance

- [ ] FOG installed and the JOS boot chain staged.
- [ ] `[Drivers]` Samba share configured (`jog-driver-share.sh`).
- [ ] Model API installed and healthy (`jog-model-api-setup.sh --apply`; `jog-doctor.sh`).
- [ ] Driver packs synced from the FOG inventory (`Sync-FOGDriverPacks.ps1`).
- [ ] `jog-multicast-tune.sh` applied for the room, including the rendezvous address.
- [ ] `jog-autojoin-setup.sh --apply` installed; default PXE entry joins a waiting session (or entry 8 is
      used deliberately).
- [ ] `/etc/jog/provisioning.env` rendered with `jog-corporate-setup`.
- [ ] `jog-install-provisioner.sh` installed the payload and the post-download hook.

### Image

- [ ] Windows 11 image is Sysprep `/generalize`-prepared (OOBE runs).
- [ ] `SetupComplete.cmd` is allowed (not blocked by policy).
- [ ] The image has the storage/network drivers needed to reach the share (the VMD driver is already in
      `WIN11-NOV26-18`).
- [ ] BitLocker is off/suspended in the image.

---

## 7. Security model

- **No autologon.** The orchestrator runs as SYSTEM via `SetupComplete.cmd` and a startup task.
- **Least privilege.** The driver account is read-only; the join account is delegated to the target OU and
  the approved groups; the AD write account for offline groups lives on a management host.
- **Credential join by default.** A `djoin` blob is a one-time computer-account credential; one blob cannot
  cover a fleet. The delegated join password is prompted on the corporate LAN and exists only during the
  join.
- **Short-lived secrets.** The rendered config is ACL'd, the driver password is removed at handoff, the join
  password is written only for the resume, and the config is deleted at `COMPLETE`.
- **No PIN in AD by default.** The startup PIN is a user secret; AD stores the recovery password.
- **Audit.** Every stage writes a timestamped log and a state transition. The FOG task log and the Windows
  event log are the other two audit surfaces.

### Residual risks

| Risk | Mitigation |
|---|---|
| Driver-share password on the Windows disk during OOBE | ACL to SYSTEM/Administrators; remove at handoff; rotate the account |
| Credential join password in the config during resume | Use a time-limited delegated account; delete at `CLEANUP`; keep the device on a trusted network |
| Air-gapped device used before corporate enrollment | It is not domain joined or encrypted; treat `AWAITING_CORPORATE` as a staging state, not a finished asset |
| Payload tampering on the share | Restrict write access to `driveradmin`; sign the PowerShell scripts; verify hashes |
| A device that never reaches the corporate network | Stays in `AWAITING_CORPORATE`; no false `COMPLETE`, no unescrowed encryption |
| A custom AD PIN attribute | Disabled by default; explicit `AllowAdPinStorage`; documented as not recommended |

---

## 8. Test plan

### Lab

1. Build the payload with `jog-install-provisioner.sh` against a test config.
2. Deploy to one VM (or one laptop) with a test OU and a test group.
3. Verify the air-gapped handoff: `AWAITING_CORPORATE`, desktop shortcut, and no passwords in the config.
4. Connect the device to the corporate network and run `Resume-JOGCorporateEnrollment.ps1`.
5. Verify each state transition in `C:\ProgramData\JOG\Provisioning.json` and the logs.
6. Verify the driver manifest resolved the model and the base pack (`pnputil /enum-drivers`).
7. Verify `dsregcmd /status` shows hybrid join.
8. Verify `net group "<group>" /domain` contains the computer.
9. Verify `manage-bde -protectors -get C:` shows the recovery password and the AD backup.
10. Verify `Get-ADObject` under the computer shows `msFVE-RecoveryPassword`.
11. Reboot twice; confirm the pipeline resumes and reaches `COMPLETE` once.

### Failure injection

| Test | Expected |
|---|---|
| Driver share offline | `DRIVERS_PENDING`, retry at next boot, no domain join |
| Bad OU / no join rights | `DOMAIN_JOIN_PENDING`, clear error, no BitLocker |
| No Entra line of sight | `HYBRID_JOIN_PENDING`, retry, no BitLocker |
| TPM disabled | `BITLOCKER_PENDING`, no false `COMPLETE` |
| AD escrow denied | `BITLOCKER_PENDING` / `ESCROW_VERIFIED` not reached |
| Device stays air-gapped | `AWAITING_CORPORATE`, no join or encryption |

### Scale

The provisioning phase is per-device and does not share a multicast stream. For 100 devices, expect
concurrent Windows first boots and domain joins; ensure the domain controllers, DNS, and driver share can
handle the burst. Stagger the first boot if the DCs are small, or use a post-imaging delay per host.

---

## 9. Where the pieces live

| Piece | Repository / path |
|---|---|
| Windows orchestrator and stages | `jog/provisioner/windows/` |
| Driver share setup | `jog/scripts/jog-driver-share.sh` |
| Driver model API | `jog/scripts/jog-model-api.py`, `jog/scripts/jog-model-api-setup.sh` |
| Driver catalog sync | `jog/provisioner/windows/Sync-FOGDriverPacks.ps1` |
| Multicast profile | `jog/scripts/jog-multicast-tune.sh` |
| Default PXE auto-join | `jog/scripts/jog-autojoin.php`, `jog/scripts/jog-autojoin-setup.sh` |
| Corporate setup prompt | `jog/scripts/jog-corporate-setup.sh` |
| Payload installer | `jog/install/jog-install-provisioner.sh` |
| FOG post-download hook | `jog/install/postdownload/jog-inject-provisioner.sh` |
| Configuration template | `jog/config/jog-provisioning.env.example` |
| BitLocker/AD analysis | `docs/BITLOCKER-AD.md` |
| Imaging math | `docs/MULTICAST-100.md` |
