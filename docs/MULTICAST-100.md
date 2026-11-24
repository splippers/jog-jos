# 100 laptops, one multicast stream, under five minutes

> **Scope:** this is the **multicast imaging time only** — the transfer of the image to 100 clients plus
> the post-download injection. It does **not** include Windows first boot, drivers, domain join, Entra
> hybrid join, AD groups, or BitLocker. Those are a separate provisioning phase.
>
> **This is a reference design, not a promise.** The arithmetic below shows what the target requires.
> Measure the actual room before quoting a time to a customer.

---

## 1. The arithmetic

The current Windows 11 image (`WIN11-NOV26-18`) is:

| Measure | Value |
|---|---|
| Compressed image (`d1p3.img`, zstd) | 25,368,500,372 bytes ≈ **25.37 GB** (23.63 GiB) |
| Deployed Windows partition (used) | ≈ **37.9 GB** |
| Target imaging time for 100 clients | **300 s** (imaging phase only) |

### Network

```text
25.37 GB ÷ 300 s = 84.6 MB/s per client = 676.5 Mbps per client
```

A 1 GbE client link can carry that (usable throughput is ~940 Mbps), but there is very little headroom.
A 2.5 GbE or 10 GbE client link gives the headroom needed for retransmissions, FEC, and other traffic.

The server sends **one** copy. The switch replicates it to every client:

```text
server 10/25 GbE ── one 676 Mbps stream ──▶ access switch ──▶ 100 × 1 GbE ports
```

The server uplink therefore carries ~0.68 Gbps, not 68 Gbps. The **edge switch fabric** must replicate
the stream to 100 ports, and the interswitch links carry one copy per switch/VLAN, not one copy per client.
That is why a 10/25/40 GbE uplink and IGMP snooping matter more than a bigger server NIC.

### Disk

```text
37.9 GB ÷ 300 s = 126 MB/s per client
```

NVMe and SATA SSDs handle this comfortably. Spinning disks and slow eMMC do not. A client that cannot
write at ~126 MB/s will stretch the session; the multicast sender waits for the slowest receiver.

### Bitrate

| `udp-sender --max-bitrate` | 25.37 GB transfer | Verdict |
|---|---|---|
| 600 Mbps | 338 s (5.6 min) | Misses the target |
| 700 Mbps | 290 s (4.8 min) | Barely makes it |
| **800 Mbps** | **254 s (4.2 min)** | Recommended default for 1 GbE clients |
| 900 Mbps | 226 s (3.8 min) | Good for 2.5 GbE clients |
| 1 Gbps | 203 s (3.4 min) | Needs clean 1 GbE+ and low overhead |

The image size is the biggest lever. A 15 GB compressed image at 800 Mbps takes ~150 s (2.5 min) and
leaves room for the multicast join window. Remove pagefile/hiberfil, run `UsedSpaceOnly` capture, and
keep the Windows partition lean.

---

## 2. The FOG settings that matter

The live appliance was found with a **10-client cap** and a **10-minute join wait**. Both are wrong for
this target. The package ships `mist-multicast-tune.sh` to set them deliberately.

| Setting | Where | Before | Applied / target | Why |
|---|---|---|---|---|
| `ngmMaxClients` | `nfsGroupMembers` | **10** | **100** | The storage node will not accept more than this many clients |
| `ngmMaxBitrate` | `nfsGroupMembers` | empty | **`800m`** | Caps `udp-sender --max-bitrate`; 800 Mbps fits the 5-min math |
| `ngmInterface` | `nfsGroupMembers` | `enp2s0` | the imaging NIC | `udp-sender --interface` |
| `FOG_UDPCAST_MAXWAIT` | `globalSettings` | **10** (minutes) | **3** (minutes) | How long the sender waits for the 100th client before starting |
| `FOG_MULTICAST_MAX_SESSIONS` | `globalSettings` | 64 | 64 | Concurrent sessions, **not** clients; 64 is fine |
| `FOG_MULTICAST_DUPLEX` | `globalSettings` | `--full-duplex` | `--full-duplex` | Keep |
| `FOG_UDPCAST_INTERFACE` | `globalSettings` | `enp2s0` | the imaging NIC | Keep in sync with the storage node |
| `FOG_MULTICAST_RENDEZVOUS` | `globalSettings` | empty | **`10.99.0.1`** | Must match the imaging interface address used by `$storageip` |
| `FOG_MULTICAST_ADDRESS` | `globalSettings` | empty | optional `239.x.x.x` | Use a dedicated group if the network has multiple multicast apps |

The lab appliance was applied on 2026-11-13: `ngmMaxClients=100`, `ngmMaxBitrate=800m`,
`FOG_UDPCAST_MAXWAIT=3`, `FOG_MULTICAST_MAX_SESSIONS=64`, `FOG_MULTICAST_RENDEZVOUS=10.99.0.1`,
`FOG_UDPCAST_INTERFACE=enp2s0`. Its imaging NIC is **1 GbE**, not the 10/25 GbE reference uplink, so the
5-minute target is not expected on that hardware. The profile is the software half; the switch fabric is
the other half.

`FOG_UDPCAST_MAXWAIT` is in **minutes** in the FOG UI (`msMaxwait = value × 60`). The sender starts when
`--min-receivers` (the session client count) have joined or when `--max-wait` expires. A 3-minute wait plus
a 4.2-minute transfer is 7.2 minutes worst case; a warm room where all 100 laptops are already at the GRUB
menu joins in seconds and finishes near 4.5 minutes. For a cold room, either stage the laptops first or
accept a longer wall-clock time.

### Rendezvous address

FOG's `udp-sender` and `udp-receiver` must agree on the control address. On the lab appliance the imaging
interface is `enp2s0` at `10.99.0.1`; the USB/workstation interface is `192.168.254.1`. A transport test
with `udp-sender --mcast-rdv-address 10.99.0.1` and `udp-receiver --mcast-rdv-address 10.99.0.1` transferred
8 MiB byte-for-byte at ~107.67 Mbps. The same test with `192.168.254.1` did not start. The tune script
therefore derives `FOG_MULTICAST_RENDEZVOUS` from the imaging interface by default. It validates that an
explicit value is IPv4, but it cannot know whether that address belongs to the imaging NIC: set it
deliberately and confirm with `ip -4 addr show`.

When a session starts, FOG builds the command from the session and global settings:

```text
udp-sender --max-bitrate '800m' --interface 'enp2s0' --min-receivers 1   --max-wait 180 --mcast-rdv-address 10.99.0.1 --portbase 63100   --full-duplex --ttl 32 --nokbd --nopointopoint --file '/images/WIN11-NOV26-18/d1p1.img'
```

The first partition uses the session `maxwait`; later partitions use FOG's built-in 600 s wait. A session
created before the tune keeps the old values, so delete and recreate it after applying the profile.

### Client-side watchdog

The **legacy JOS shell client** (`jos/initrd/scripts/jos-udpcast-receiver.sh`) has a weak-link watchdog:
it samples `udp-receiver` throughput every 10 s and reboots a client that stays below a threshold. The
current default JOS is the **stock FOS userland**, which uses FOG's receiver; the legacy watchdog is not in
that path. Validate the weak-link behaviour in the lab and choose one of:

- Keep the FOS receiver and rely on the FOG session timeout / manual re-image of the slow client.
- Use the legacy JOS shell path for multicast rooms where the watchdog is mandatory.
- Add a FOS-compatible wrapper in a future JOS change (roadmap item).

If you use the legacy watchdog, the tunables are:

```text
JOS_UDPCAST_MIN_MB_S=80      # 80 MB/s ≈ 640 Mbps; below this a 5-min finish is unlikely
JOS_UDPCAST_STRIKES=2        # consecutive 10 s samples below the threshold
JOS_UDPCAST_GRACE_CHECKS=6   # 60 s startup grace
```

The defaults in the script are more forgiving (`30 MB/s`, 3 strikes); tighten them only after measuring
the room.

---

## 3. Network reference design

```text
                         ┌──────────────────────────────┐
                         │ Brume appliance                │
                         │ Ubuntu + FOG + JOS staging   │
                         │ NVMe image store             │
                         │ 10/25 GbE uplink             │
                         └──────────────┬───────────────┘
                                        │ one multicast stream
                         ┌──────────────▼───────────────┐
                         │ core / distribution switch   │
                         │ IGMP snooping + querier      │
                         │ 40/100 GbE uplinks           │
                         └───────┬──────────────┬───────┘
                                 │              │
                    ┌────────────▼───┐   ┌──────▼─────────┐
                    │ access switch  │   │ access switch  │
                    │ 48 × 1/2.5 GbE │   │ 48 × 1/2.5 GbE │
                    └───────┬────────┘   └───────┬────────┘
                            │                    │
                     48 laptops             48 laptops + 4
```

Checklist:

- [ ] Dedicated imaging VLAN; no corporate DHCP/router on it.
- [ ] IGMP snooping enabled on every switch; a multicast querier exists on the VLAN.
- [ ] No Wi-Fi, no unmanaged daisy-chained switches, no powerline adapters.
- [ ] Server on 10/25 GbE; access switches on 10/25/40 GbE uplinks.
- [ ] 1 GbE access is enough per client (0.68 Gbps), but 2.5 GbE gives headroom.
- [ ] All clients wired, UEFI, Secure Boot on, JOS staged.
- [ ] Client disks are NVMe/SATA SSD; no HDD/eMMC.
- [ ] `ngmMaxClients=100`, `ngmMaxBitrate=800m`, `FOG_UDPCAST_MAXWAIT=3`.
- [ ] `mist-autojoin-setup.sh --apply` installed and `JOG_AUTOJOIN_ALLOW_NET` covers the client subnet.
- [ ] `FOG_MULTICAST_RENDEZVOUS` is the imaging interface address, not the USB/workstation address.
- [ ] Image is as small as practical; `UsedSpaceOnly`; pagefile/hiberfil removed.
- [ ] The FOG storage node is on the same L2 segment or has a multicast route.

---

## 4. Benchmark method

Do not quote a number from this document. Measure it:

1. Stage the same image and the same 100 (or 10/25/50/100) clients.
2. Create the multicast session, then PXE boot every client. The default JOS entry auto-joins a session
   that is still in its join window; entry 8 remains available for a manual choice.
3. Record the time from `udp-sender` start to the last client reporting complete.
4. Capture:
   - `/opt/fog/log/multicast.log`
   - `udp-sender` output (rate, retransmits)
   - per-client `udp-receiver` rate
   - per-client disk write rate (`iostat`, `nvme smart-log`, or the FOG task timer)
5. Run at 10, 25, 50, and 100 clients. The curve tells you whether the switch or the slowest client is the
   limit.
6. Repeat with the image at its real production size, not a lab image.

The Operations Centre (`mist/scripts/mist-imaging-api.py`) shows per-device progress and rate; use it as the
live view during the benchmark.

### What "under 5 minutes" really means

This is an **imaging-phase** number. It starts when the multicast session starts and ends when the last
client has received the image and the post-download injection has finished. It does not include the
provisioning phase that follows.

For the current 25.37 GB image, the floor is ~4.2 minutes at 800 Mbps **before** the join window, retries,
and disk flush. A realistic 100-client imaging result on a clean 1 GbE access layer is **5–7 minutes**. On
2.5/10 GbE access with an NVMe image store and a warm room, **3–5 minutes** is achievable. Shrinking the
image is the cheapest way to make the claim true.

---

## 5. Apply it

```bash
# Inspect the current FOG settings and the link speed
sudo mist-multicast-tune.sh --check

# Back up the FOG tables, then apply the 100-client profile
sudo mist-multicast-tune.sh --apply
```

The script updates `nfsGroupMembers` and `globalSettings`, backs up the affected tables, and prints the
resulting values. Re-create any existing multicast session after changing the settings; the session stores
its own `maxwait` at creation time.

For a manual test, create a named session for the image, then PXE boot the client. The default JOS entry
now asks the appliance for a joinable session before the normal FOG handshake:

- exactly one session in its join window → JOS creates the same per-host multicast association as entry 8
  and starts imaging automatically;
- an existing FOG task → JOS leaves it alone and starts it;
- no session/task → JOS boots the local disk instead of erroring;
- several named sessions → JOS refuses to guess; use entry **8. Join Multicast Session** to pick one.

The server-side endpoint is `/fog/service/mist-autojoin.php`, installed by
`sudo mist-autojoin-setup.sh --apply` (or `JOG_AUTOJOIN_ENABLE=1` via `mist-post-fog-setup.sh`). It is
restricted to the imaging subnet by default (`JOG_AUTOJOIN_ALLOW_NET=10.99.0.0/24`). A session with
`msSessClients=1` and no task associations is enough to validate transport with one client; a production
session should have one FOG multicast task per host so the server can track completion and enforce the
receiver count. Delete the test session when finished so it does not hold a `udp-sender` port.

The join window is the session's `msMaxwait` (FOG stores `FOG_UDPCAST_MAXWAIT` minutes as seconds). If the
session has already started transmitting, auto-join correctly refuses it; create a fresh session for the
next group.
