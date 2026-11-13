# BitLocker, AD, and the "6-digit PIN" question

> **Short answer:** Active Directory stores the **48-digit BitLocker recovery password**, not the
> six-digit startup PIN. The recovery password is displayed as eight groups of six digits, which is
> probably where the "6-digit PIN" wording comes from. AD has no supported attribute for a BitLocker
> startup PIN, and storing one there would be a security anti-pattern.

This document explains exactly what AD stores, where it lives, how JOG escrows it, and what to do if the
organisation insists on a TPM + PIN design.

---

## 1. What AD actually stores

When BitLocker recovery information is backed up to Active Directory, Windows creates an
`msFVE-RecoveryInformation` object **under the computer object**:

```text
CN=LT-SITE01-ABC1234,OU=Workstations,OU=JOG,DC=corp,DC=example,DC=com
└── CN={GUID},CN=LT-SITE01-ABC1234,...
    ├── msFVE-RecoveryPassword   ← the 48-digit recovery password
    ├── msFVE-RecoveryGuid       ← identifies the key protector
    ├── msFVE-VolumeGuid         ← identifies the encrypted volume
    └── msFVE-KeyPackage         ← the recovery key package
```

| Attribute | What it is | Sensitive? |
|---|---|---|
| `msFVE-RecoveryPassword` | 48-digit numerical recovery password, shown as `xxxxxx-xxxxxx-...` | Yes — treat as a secret |
| `msFVE-RecoveryGuid` | GUID of the recovery-password protector | No |
| `msFVE-VolumeGuid` | GUID of the BitLocker volume | No |
| `msFVE-KeyPackage` | Encrypted key package used by recovery tools | Yes |
| `msFVE-StartupPIN` | **Does not exist** | — |

The schema is part of Windows Server 2008 and later; you do **not** need to extend the schema for normal
BitLocker recovery escrow. The computer object must be in a domain where the BitLocker schema is present,
and the account doing the backup needs write access to the computer object (or the GPO does it as SYSTEM).

### Why the "6-digit" confusion happens

The recovery password is 48 digits, grouped for readability:

```text
123456-234567-345678-456789-567890-678901-789012-890123
```

That is **eight groups of six digits**, not a six-digit PIN. If someone says "the 6-digit BitLocker PIN",
ask which of these they mean:

1. **The startup PIN** — a pre-boot secret the user types. 6–20 digits (numeric) or 4–20 characters
   (enhanced). It is not stored by BitLocker and is not escrowed to AD.
2. **The recovery password** — 48 digits, displayed in six-digit groups. This is what AD stores in
   `msFVE-RecoveryPassword`.

The two are different protectors and serve different purposes. Only the second is recoverable by IT.

---

## 2. The recommended JOG design

JOG defaults to **TPM-only BitLocker** for corporate laptops:

```text
TPM protector
+ recovery-password protector
+ recovery password escrowed to AD (and optionally Entra ID)
+ escrow verified before COMPLETE
```

Why TPM-only:

- No pre-boot PIN to distribute, forget, or leak.
- The user experience is a normal Windows boot.
- The recovery password is the break-glass path for helpdesk.
- It works with hybrid Entra join and with Intune/GPO policy.
- It avoids putting a reusable secret in AD.

The provisioner implements this in `Enable-JOGBitLocker.ps1`:

```text
Mode = TpmOnly          # default
Escrow = AD | Entra | Both
PinStorage = None       # default
```

The device only reaches `ESCROW_VERIFIED` / `COMPLETE` after the recovery password is confirmed in the
directory.

### If the organisation requires TPM + PIN

Use TPM + PIN, but treat the PIN as a **user-held secret**:

- Generate it per device at provisioning time (six digits is allowed, but longer is better).
- Show it to the user/technician once, or set it to a user-chosen PIN via policy.
- Escrow only the **recovery password** to AD/Entra ID.
- Do not write the PIN to AD.

JOG supports `Mode = TpmPin` with `PinStorage = None` or `PinStorage = LocalDPAPI`. The PIN can be written
to a DPAPI-protected local file for the provisioning window, then removed. It is never sent to the
appliance.

### If helpdesk insists on a recoverable six-digit code

Do not weaken BitLocker by storing the startup PIN in AD. Use one of these instead:

| Option | What it gives you | Trade-off |
|---|---|---|
| **Recovery password in AD/Entra** | A 48-digit break-glass key, auditable, supported | Longer to read over the phone; can be read in six-digit groups |
| **MBAM** | BitLocker recovery-key management, helpdesk portal, audit | Another server/role to run; still does not store the startup PIN |
| **A secrets manager** (Vault, Key Vault, etc.) | A six-digit PIN can be stored with access control and audit | More infrastructure; the PIN is still a reusable secret |
| **Windows LAPS** | Local admin password rotation, not BitLocker | Solves a different problem |
| **A custom AD attribute** | Literally "in AD" | **Not recommended**; see below |

---

## 3. If you really must write the PIN to AD

There is no built-in `msFVE-StartupPIN` attribute. The only ways to put a PIN on the computer object are:

1. A custom schema attribute (for example `msFVE-StartupPIN`), or
2. An existing free string attribute such as `extensionAttribute15`.

Both store the PIN in **cleartext** in the directory (AD does not encrypt arbitrary attributes). Anyone
with read access to the computer object can read it. Replication, backups, and monitoring tools copy it.
This is a real security risk, not a theoretical one.

JOG therefore gates this behind an explicit switch:

```json
"BitLocker": {
  "Mode": "TpmPin",
  "PinStorage": "ADCustomAttribute",
  "AllowAdPinStorage": false,
  "AdPinAttribute": "extensionAttribute15"
}
```

`AllowAdPinStorage` must be `true` before the provisioner will write the PIN. The script logs a warning and
writes an audit event. The default is `false`.

If you enable it, the write is a normal AD attribute update on the computer object:

```powershell
# NOT RECOMMENDED — cleartext PIN in AD
Set-ADComputer -Identity $env:COMPUTERNAME `
  -Add @{ extensionAttribute15 = $pin } `
  -Credential $domainCredential `
  -Server $domainController
```

To read it back:

```powershell
Get-ADComputer -Identity LT-SITE01-ABC1234 `
  -Properties extensionAttribute15 |
  Select-Object Name, extensionAttribute15
```

The recommended alternatives are the recovery password (AD/Entra), MBAM, or a secrets manager.

---

## 4. Exact escrow commands

### 4.1 AD escrow with `manage-bde`

After the recovery-password protector exists:

```powershell
$vol = Get-BitLockerVolume -MountPoint 'C:'
$rp  = $vol.KeyProtector | Where-Object KeyProtectorType -eq 'RecoveryPassword'

manage-bde.exe -protectors -adbackup C: -id $rp.KeyProtectorId

# Verify the protector and its backup state
manage-bde.exe -protectors -get C:
```

`manage-bde -protectors -get C:` shows the recovery password and an `AD Backed up` indicator. The command
returns 0 when the backup succeeds; a non-zero exit code means the computer object could not be updated
(permissions, schema, or connectivity).

### 4.2 Verify the AD object

On a domain-joined management host with RSAT:

```powershell
$computer = Get-ADComputer -Identity $env:COMPUTERNAME -Properties msFVE-RecoveryInformation
$computer.'msFVE-RecoveryInformation'

Get-ADObject -SearchBase $computer.DistinguishedName -Filter * `
  -Properties msFVE-RecoveryPassword, msFVE-RecoveryGuid, msFVE-VolumeGuid |
  Select-Object Name, msFVE-RecoveryPassword, msFVE-RecoveryGuid, msFVE-VolumeGuid
```

If `msFVE-RecoveryInformation` is empty, the backup did not happen. Check:

- The GPO "Store BitLocker recovery information in Active Directory Domain Services" is applied.
- The computer object is not protected from accidental deletion in a way that blocks child creation.
- The account running the backup has write access to the computer object.
- The domain controller is reachable and the schema includes the BitLocker attributes.

### 4.3 Entra ID escrow

For a hybrid-joined or Entra-joined device:

```powershell
$vol = Get-BitLockerVolume -MountPoint 'C:'
$rp  = $vol.KeyProtector | Where-Object KeyProtectorType -eq 'RecoveryPassword'

BackupToAAD-BitLockerKeyProtector -MountPoint 'C:' -KeyProtectorId $rp.KeyProtectorId
```

This requires the device to be registered/joined to Entra ID and the BitLocker key-backup policy to allow
it. Verify in the Entra admin centre under **Devices > All devices > <device> > BitLocker keys**, or with
the Graph API.

For hybrid join, choose one escrow target as the source of truth, or use both deliberately. If you use
both, verify both before `COMPLETE`; a key that exists in AD but not Entra ID (or vice versa) is a support
incident waiting to happen.

---

## 5. GPO / policy prerequisites

At minimum, the following Computer Configuration policies should be set (names vary slightly by Windows
version):

| Policy | Setting |
|---|---|
| Store BitLocker recovery information in Active Directory Domain Services | Enabled |
| Choose how BitLocker-protected operating system drives can be recovered | Enable recovery-password backup; allow recovery password |
| Do not enable BitLocker until recovery information is stored in AD DS | Enabled (if you want a hard guarantee) |
| Choose drive encryption method and cipher strength | XTS-AES 256 (or the organisation standard) |
| Require additional authentication at startup | Allow TPM; require TPM+PIN only if the organisation mandates it |
| Configure use of hardware-based encryption | Per hardware/vendor guidance |

The provisioner does not deploy GPOs. It assumes the device will receive them from the domain (or Intune)
and that the recovery-password protector is allowed.

---

## 6. Hybrid join notes

BitLocker runs **after** `DIRECTORY_JOINED` and, for the hybrid workflow, after the device reports:

```text
AzureAdJoined : YES
DomainJoined  : YES
DeviceAuthStatus : SUCCESS
```

Use `dsregcmd /status` to verify. If the device is domain-joined but not yet hybrid-joined, the provisioner
waits and retries; it does not enable BitLocker early. The state file records `ENTERPRISE_READY` while it
waits, so a device that never reaches the corporate network is not silently encrypted without escrow.

For offline domain join, the computer account is pre-created and the device has no reusable credential.
Group membership and any AD-side escrow verification should be performed by a management host (see
`Add-JOGComputerGroups.ps1`) or by the join broker described in `ROADMAP.md`.

---

## 7. Troubleshooting

| Symptom | Likely cause | Check |
|---|---|---|
| `manage-bde -adbackup` returns non-zero | No write access to the computer object, or schema missing | `Get-ADComputer` ACLs; `Get-ADObject` on the computer; domain controller connectivity |
| `msFVE-RecoveryInformation` empty | GPO not applied, or backup not attempted | `gpresult /h`; `manage-bde -protectors -get C:`; event log `Microsoft-Windows-BitLocker/BitLocker Management` |
| `BackupToAAD-BitLockerKeyProtector` fails | Device not Entra joined, or policy blocks backup | `dsregcmd /status`; Entra device record; Intune/GPO key-backup policy |
| PIN prompt but no PIN known | TPM+PIN was enabled without a delivery path | Recovery password in AD/Entra; re-provision the protector |
| Recovery key visible in AD but not Entra | Only one escrow target was configured | Run the second backup command; decide on a source of truth |

---

## 8. The one-line answer to take to the architecture meeting

> **AD stores the 48-digit BitLocker recovery password in `msFVE-RecoveryPassword` under the computer
> object. It does not store the six-digit startup PIN; the six-digit groups are just how the 48-digit
> recovery password is displayed. Use TPM-only BitLocker and escrow the recovery password. If you need a
> PIN, keep it out of AD and use a secrets manager or a user-held PIN.**
