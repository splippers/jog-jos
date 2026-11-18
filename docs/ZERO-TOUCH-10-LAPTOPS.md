# Zero-touch: 10 Dell Latitudes from box to imaged

**Result:** unbox → plug into the 16-port switch → `F12` → **Network Boot**.
No FOG login, no MAC entry, no image selection, no menu keystrokes. Each
machine registers itself, joins one multicast stream, and images.

---

## The flow

```
F12 > Network Boot
  └─ dnsmasq on enp2s0 (10.99.0.1) hands out 10.99.0.x + PXE boot file
      └─ signed shim -> GRUB -> default "JOS Image Deploy/Capture"
          └─ S96jos-taskcheck calls /fog/service/jog-autojoin.php with its MAC
              ├─ unknown MAC  -> creates a FOG host (JOG-<mac>) with default modules
              ├─ existing task -> "OK TASK", run it
              └─ one joinable multicast session -> creates a MULTICAST task
                    └─ S99fog / hostinfo sees the task -> udp-receiver joins 10.99.0.1
```

The appliance-side pieces are already installed:

| Piece | File / state |
|---|---|
| Auto-join endpoint | `/var/www/html/fog/service/jog-autojoin.php` (now also auto-registers) |
| Network allow-list | `/etc/jog/autojoin.env` → `10.99.0.0/24` |
| Client gate | `S96jos-taskcheck` inside `/tftpboot/jos/initrd.img` |
| DHCP + PXE | `/etc/dnsmasq.d/99-jog-imaging.conf`, `enp2s0` |
| Multicast tunables | `ngmMaxClients=100`, `ngmMaxBitrate=800m`, rendezvous `10.99.0.1` |
| Arming helper | `sudo jog-zero-touch-arm` |

---

## Imaging day

1. **Cable the switch.** Connect the 16-port switch to the appliance's imaging
   NIC (`enp2s0`, `10.99.0.1`). Plug the 10 laptops into ports 1–10. Do **not**
   connect that switch to the building network or another DHCP server.

2. **Confirm link and DHCP scope are live:**

   ```bash
   ip -br link show enp2s0          # state UNKNOWN (carrier), not DOWN
   ip -br addr show enp2s0          # 10.99.0.1/24
   systemctl is-active dnsmasq      # active
   ```

   If `enp2s0` still shows `state DOWN`, the cable/switch port is bad or the
   switch is off. Nothing else will work until carrier is present.

3. **Arm the multicast job** (this starts `udp-sender` waiting for 10 receivers):

   ```bash
   sudo jog-zero-touch-arm
   ```

   Expected output includes `armed session N: 'JOG-DELL-ZERO', image
   'WIN11-NOV26-18' (id 21), 10 clients, port 63100`.

   Confirm the sender is up:

   ```bash
   sudo tail -8 /opt/fog/log/multicast.log
   pgrep -x udp-sender -a
   ```

   You should see `10 clients found`, `sending on base port 63100`, and a
   `udp-sender ... --min-receivers 10 --max-wait 180 ...` process.

4. **Boot the laptops.** On each: `F12` → **Network Boot** (or PXE / LAN).
   Press nothing after that. The GRUB menu's default entry fires after 5 s.

5. **Watch it land:**

   ```bash
   sudo mysql -D fog -e "
     SELECT h.hostName, t.taskName, t.taskStateID
       FROM tasks t JOIN hosts h ON h.hostID=t.taskHostID
      WHERE t.taskTypeID=8 AND t.taskStateID IN (1,2,3);"
   sudo tail -30 /opt/fog/log/multicast.log
   ```

   Ten hosts named `JOG-<mac>` should appear with task `JOG-DELL-ZERO`.
   `udp-sender` transmits as soon as the tenth receiver joins; with ten
   machines already at the menu that is seconds, not the 180 s fallback.

6. **Read the queue screen.** While a client waits for the session to fill it
   shows a full-screen navy console view instead of FOG's repeating
   `Attempting to check in ... Failed` lines. Panels:

   | Panel | Contents |
   | --- | --- |
   | `JOB` | hostname, assigned image, task name |
   | `LINK` | interface, negotiated speed and duplex, RX/TX errors |
   | `QUEUE` | session name/image, clients joined vs required, check-in reason, wait elapsed/max, progress bar |
   | `SURROUNDING SYSTEMS` | appliance host and imaging IP, FOG multicast/DHCP/NFS, mobile/imaging/model API health |

   The screen refreshes every 3 s and is replaced by Partclone's own progress
   display as soon as check-in succeeds. If it shows `Check-in: waiting for
   server` the appliance feed is unreachable; if `Joined` never reaches the
   required count, the remaining laptops have not booted into the session.

---

## After the run

The session finishes on its own. Verify with:

```bash
sudo mysql -D fog -e "SELECT msID,msName,msState,msPercent FROM multicastSessions WHERE msName='JOG-DELL-ZERO';"
```

`msState=4` means complete. The host records remain in FOG with their images
assigned — subsequent boots of those machines will simply re-image if a task
is queued, or boot local disk when no session is armed. To re-image another
batch, run `sudo jog-zero-touch-arm` again; it retires the old session and
creates a fresh one.

---

## Troubleshooting

| Symptom | Check |
|---|---|
| Laptop boots Windows, not PXE | Firmware boot order / F12 menu selection; Secure Boot is fine (signed shim). |
| `No DHCP` / no 10.99.0.x address | `ip -br link show enp2s0` must show carrier; `systemctl status dnsmasq`. |
| Stuck at GRUB menu | Default entry is 1 with 5 s timeout. A manual choice means the keyboard was touched. |
| Console says `AMBIGUOUS ...` | More than one joinable multicast session. Run `sudo jog-zero-touch-arm` to retire stale ones. |
| Console says `NONE` | No armed session. Run `sudo jog-zero-touch-arm`. |
| Console says `ERROR host not registered` | Endpoint file is stale. Reinstall: `sudo jog-autojoin-setup --apply`. |
| `Interface not ready, waiting...` in multicast.log | `FOG_WEB_HOST` must be `10.99.0.1` and `ip -4 addr` must list it. Restart `FOGMulticastManager.service`. |
| Sender dies immediately with `execute() on false` | Transient fork/DB race. `sudo systemctl restart FOGMulticastManager.service`, then re-arm. |
| Transfer stalls | Slowest disk decides. Check `nginx`/NFS, switch IGMP snooping, and that no client is on a 10 Mb/s port. |

Health check for the endpoint alone (side-effect free):

```bash
sudo jog-autojoin-setup --check
```

That POSTs `probe=1` and expects `OK ALIVE`. It never supplies a MAC, so it
cannot register a host or join a session.

To verify the full registration + join path, use a throwaway MAC and then
remove the record it creates:

```bash
curl -s -X POST --data 'mac=00:11:22:33:44:55' \
  http://127.0.0.1/fog/service/jog-autojoin.php
sudo mysql -D fog -e "DELETE FROM hosts WHERE hostName='JOG-22334455';"
```

`OK JOIN JOG-DELL-ZERO` means both halves work. Re-arm afterwards so the
throwaway client's task association does not consume a slot in the session.

---

## Why this is safe

* The endpoint is unauthenticated like FOG's own PXE service endpoints, but it
  only acts on the MAC the client sends and only joins sessions FOG itself
  calls joinable.
* It is restricted to `10.99.0.0/24` plus localhost (`/etc/jog/autojoin.env`).
* No FOG credential is stored on the client or in the initrd.
* Image assignment comes from the armed session, so there is exactly one
  source of truth for what gets deployed.
