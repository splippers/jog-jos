#!/usr/bin/env python3
"""Finalise the Haar rename on an installed rig: internal names back to jog-*.

Public name stays Haar (descriptions, docs, UI). Internal identifiers stay jog-* so a future
rename touches only brand/brand.env. See REBRAND.md.

Dry run by default. `--apply` makes changes (run as root). Anything removed is MOVED to
/var/backups/rename-removed-<ts>/, never deleted.
"""
import os, re, sys, shutil, subprocess, time

APPLY = '--apply' in sys.argv
TS = time.strftime('%Y%m%d-%H%M%S')
RM = f'/var/backups/rename-removed-{TS}'
UNIT = '/etc/systemd/system'
DIRS = [UNIT, '/usr/local/sbin', '/usr/local/bin']
STACK = '/home/jog/snap/copilot-cli/common/jog-stack'
PFX = re.compile(r'^(jog|mist|haar)-')
METRY = re.compile(r'(haarmetry|mistmetry|jogometry)')
SUBS = [
    (METRY, 'jogemetry'),
    (re.compile(r'\b(haar|mist)-'), 'jog-'),
    (re.compile(r'/etc/(haar|mist)\b'), '/etc/jog'),
    (re.compile(r'/var/lib/mist\b'), '/var/lib/jog'),
    (re.compile(r'\b(haar|mist)\.env\b'), 'jog.env'),
    (re.compile(r'\b(HAAR|MIST|BRUME)_'), 'JOG_'),
    (re.compile(r'\b(haar|mist)_'), 'jog_'),
    (re.compile(r'(?<=/)(haar|mist)(?=[/"\'\s)\]]|$)', re.M), 'jog'),
]
warn = []


def say(*a):
    print(('APPLY ' if APPLY else 'PLAN  ') + ' '.join(str(x) for x in a))


def sh(cmd, check=False):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and r.returncode:
        raise SystemExit(f'FAILED: {cmd}\n{r.stderr}')
    return r.stdout.strip()


def canon(n):
    m = PFX.match(n)
    return 'jog-' + METRY.sub('jogemetry', n[m.end():]) if m else None


def transform(text):
    for rx, rep in SUBS:
        text = rx.sub(rep, text)
    return text


def is_text(b):
    return b'\0' not in b[:4096]


def stash(path):
    """Move a file or symlink out of the way into the backup tree."""
    dest = RM + '/' + path.strip('/').replace('/', '__')
    say('move away', path, '->', dest)
    if APPLY:
        os.makedirs(RM, exist_ok=True)
        while os.path.lexists(dest):
            dest += '_'
        shutil.move(path, dest)


def repo_original(canon_name, kind):
    for repo, sub in (('jog', 'scripts' if kind != 'unit' else 'systemd'), ('jogemetry', 'server')):
        out = sh(f'git -C {STACK}/{repo} show origin/main:{sub}/{canon_name} 2>/dev/null')
        if out:
            return out
    return None


def nlines_diff(a, b):
    import difflib
    return sum(1 for l in difflib.ndiff(a.splitlines(), b.splitlines()) if l[:1] in '+-')


# ---------------------------------------------------------------- 1. units and scripts
groups = {}
for d in DIRS:
    for n in sorted(os.listdir(d)):
        c = canon(n)
        p = os.path.join(d, n)
        if not c or c == 'jog-cli' or '.bak' in n or os.path.isdir(p) and not os.path.islink(p):
            continue
        if d == UNIT and not n.endswith(('.service', '.timer')):
            continue
        groups.setdefault((d, c), []).append(n)

BACKUP = next((a.split('=', 1)[1] for a in sys.argv if a.startswith('--enabled-from=')), None)
backup_enabled = set()
if BACKUP:
    for line in sh(f'tar tzf {BACKUP}').splitlines():
        m = re.search(r'etc/systemd/system/[^/]+\.wants/([^/]+)$', line)
        if m and canon(m.group(1)):
            backup_enabled.add(canon(m.group(1)))
unit_state = {}
for (d, c), names in groups.items():
    if d != UNIT:
        continue
    en = any(sh(f'systemctl is-enabled {n} 2>/dev/null') in ('enabled', 'alias', 'indirect') and
             not os.path.islink(os.path.join(d, n)) for n in names)
    en = en or any(os.path.exists(f'{UNIT}/multi-user.target.wants/{n}') or
                   os.path.exists(f'{UNIT}/timers.target.wants/{n}') for n in names)
    ac = any(sh(f'systemctl is-active {n} 2>/dev/null') in ('active', 'activating') for n in names)
    if BACKUP:
        en = c in backup_enabled
        ac = en
    unit_state[c] = (en, ac)

planned = {}
for (d, c), names in sorted(groups.items()):
    order = {'haar': 0, 'mist': 1, 'jog': 2}
    real = [n for n in names if os.path.isfile(os.path.join(d, n)) and not os.path.islink(os.path.join(d, n))]
    real.sort(key=lambda n: order[PFX.match(n).group(1)])
    src = os.path.join(d, real[0]) if real else None
    if not src:
        for n in names:
            rp = os.path.realpath(os.path.join(d, n))
            if os.path.isfile(rp):
                src = rp
                break
    if not src:
        warn.append(f'{d}/{c}: no real source file (all links dangle); not creating')
        for n in names:
            if os.path.islink(os.path.join(d, n)) and n != c:
                planned.setdefault(d, []).append(('stash', os.path.join(d, n)))
        continue
    raw = open(src, 'rb').read()
    tgt = os.path.join(d, c)
    if is_text(raw):
        new = transform(raw.decode('utf-8', 'replace')).encode()
        kind = 'unit' if d == UNIT else 'script'
        orig = repo_original(c, kind)
        note = ''
        if orig is not None:
            note = f' (differs from repo origin/main by {nlines_diff(orig, new.decode())} lines)'
        if new != raw:
            note += f' [renamed text in {nlines_diff(raw.decode("utf-8", "replace"), new.decode())} lines]'
    else:
        new, note = raw, ' [binary, copied]'
    planned.setdefault(d, []).append(('write', tgt, new, os.stat(src).st_mode & 0o7777, os.path.basename(src), note))
    for n in names:
        if n != c:
            planned.setdefault(d, []).append(('stash', os.path.join(d, n)))
    if n == c and os.path.islink(tgt):
        pass

# dangling-script check for units
all_targets = {a[1] for acts in planned.values() for a in acts if a[0] == 'write'}
dangling = set()
for acts in planned.values():
    for a in acts:
        if a[0] == 'write' and a[1].startswith(UNIT):
            for m in re.finditer(r'^Exec\w+=-?(/\S+)', a[2].decode(), re.M):
                p = m.group(1)
                if not os.path.exists(p) and p not in all_targets:
                    dangling.add(os.path.basename(a[1]))
                    warn.append(f'{os.path.basename(a[1])}: ExecStart target {p} does not exist anywhere; unit will stay disabled')

# ---------------------------------------------------------------- report
for d, acts in planned.items():
    for a in acts:
        if a[0] == 'write':
            say('write', a[1], f'from {a[4]}', a[5])

live = sorted(c for c, (en, ac) in unit_state.items() if ac)
enab = sorted(c for c, (en, ac) in unit_state.items() if en and c not in dangling)
say('units to stop first:', ' '.join(live))
say('units to enable after:', ' '.join(enab))
say('units left disabled (missing script):', ' '.join(sorted(dangling)) or 'none')

if not APPLY:
    for w in warn:
        print('WARN ', w)
    print('\nDirectory moves that --apply will do:')
    print('  /etc/jog (link->/etc/haar) becomes the real dir; /etc/mist link stashed; haarmetry-* conf renamed jogemetry-*')
    print('  /var/lib/jog (link->/var/lib/mist) becomes the real dir')
    print('  /usr/local/lib/jogemetry (links ->mistmetry->haarmetry) becomes the real dir; link files stashed')
    print('  /usr/local/bin/mist, mist-cli stashed; /etc/hosts 127.0.1.1 line set to the real hostname')
    print('  udev rules whose RUN script is missing are stashed')
    print('  /usr/local/share/haar -> jog; /var/lib/haar, /var/log/mist, 99-haar/mist-imaging.conf stashed; sysctl file renamed; DHCP guard restored from /opt/jog/scripts')
    sys.exit(0)

if os.geteuid() != 0:
    raise SystemExit('run --apply as root')

# ---------------------------------------------------------------- apply
say('stopping live units')
for c in live:
    for n in {c} | {x for (dd, cc), ns in groups.items() if cc == c for x in ns}:
        sh(f'systemctl stop {n} 2>/dev/null')

for d, acts in planned.items():
    for a in acts:
        if a[0] == 'stash' and os.path.lexists(a[1]):
            stash(a[1])
for d, acts in planned.items():
    for a in acts:
        if a[0] == 'write':
            if os.path.lexists(a[1]):
                if os.path.islink(a[1]):
                    stash(a[1])
            tmp = a[1] + '.new'
            open(tmp, 'wb').write(a[2])
            os.chmod(tmp, a[3])
            os.replace(tmp, a[1])
# stale wants links
for w in os.listdir(UNIT):
    wd = os.path.join(UNIT, w)
    if w.endswith('.wants') and os.path.isdir(wd):
        for n in os.listdir(wd):
            if PFX.match(n) and not os.path.exists(os.path.join(wd, n)):
                os.unlink(os.path.join(wd, n))
            elif PFX.match(n) and canon(n) != n and os.path.lexists(os.path.join(wd, n)):
                os.unlink(os.path.join(wd, n))


def dirswap(link, real_candidates, final):
    if os.path.islink(link):
        stash(link)
    for rc in real_candidates:
        if os.path.isdir(rc) and not os.path.islink(rc) and not os.path.exists(final):
            say('rename dir', rc, '->', final)
            os.rename(rc, final)


dirswap('/etc/jog', ['/etc/haar', '/etc/mist'], '/etc/jog')
for x in ('/etc/mist', '/etc/haar'):
    if os.path.lexists(x):
        stash(x)
for n in sorted(os.listdir('/etc/jog')):
    p = os.path.join('/etc/jog', n)
    if re.match(r'^(haar|mist)\.env$', n):
        stash(p) if os.path.islink(p) else None
    elif METRY.search(n):
        np_ = os.path.join('/etc/jog', METRY.sub('jogemetry', n))
        if not os.path.exists(np_):
            os.rename(p, np_)
            say('rename', p, '->', np_)
    p = os.path.join('/etc/jog', METRY.sub('jogemetry', n))
    if os.path.isfile(p) and n.endswith(('.conf', '.template')):
        t = open(p).read()
        t2 = transform(t)
        if t2 != t:
            say('rewrite', p)
            open(p, 'w').write(t2)

if os.path.islink('/var/lib/jog'):
    stash('/var/lib/jog')
    if os.path.isdir('/var/lib/mist') and not os.path.lexists('/var/lib/jog'):
        os.rename('/var/lib/mist', '/var/lib/jog')
        say('rename dir /var/lib/mist -> /var/lib/jog')

lib = '/usr/local/lib'
for x in ('jogemetry', 'mistmetry'):
    if os.path.islink(f'{lib}/{x}'):
        stash(f'{lib}/{x}')
if os.path.isdir(f'{lib}/haarmetry') and not os.path.lexists(f'{lib}/jogemetry'):
    os.rename(f'{lib}/haarmetry', f'{lib}/jogemetry')
    say('rename dir', f'{lib}/haarmetry', '->', f'{lib}/jogemetry')
for n in sorted(os.listdir(f'{lib}/jogemetry')):
    p = f'{lib}/jogemetry/{n}'
    if os.path.islink(p):
        stash(p)
    elif n.endswith('.py') and '.bak' not in n:
        t = open(p).read()
        t2 = transform(t)
        if t2 != t:
            say('rewrite', p)
            open(p, 'w').write(t2)

for n in ('mist', 'mist-cli'):
    if os.path.lexists(f'/usr/local/bin/{n}'):
        stash(f'/usr/local/bin/{n}')

# ---- extra rig-local leftovers
share = '/usr/local/share'
if os.path.islink(f'{share}/mist'):
    stash(f'{share}/mist')
if os.path.isdir(f'{share}/haar') and not os.path.lexists(f'{share}/jog'):
    os.rename(f'{share}/haar', f'{share}/jog')
    say('rename dir', f'{share}/haar', '->', f'{share}/jog')
for x in ('/var/lib/haar', '/var/log/mist', '/var/log/haar'):
    if os.path.lexists(x):
        stash(x)
for n in ('99-haar-imaging.conf', '99-mist-imaging.conf'):
    if os.path.lexists(f'/etc/dnsmasq.d/{n}'):
        stash(f'/etc/dnsmasq.d/{n}')
old, new = '/etc/sysctl.d/99-jog-jogometry.conf', '/etc/sysctl.d/99-jog-jogemetry.conf'
if os.path.exists(old) and not os.path.exists(new):
    os.rename(old, new)
    say('rename', old, '->', new)
guard_src, guard = '/opt/jog/scripts/jog-dhcp-guard.py', '/usr/local/bin/jog-dhcp-guard.py'
if os.path.exists(guard_src) and not os.path.exists(guard):
    shutil.copy2(guard_src, guard)
    say('restore DHCP guard', guard_src, '->', guard)

host = open('/etc/hostname').read().strip()
h = open('/etc/hosts').read()
h2 = re.sub(r'^(127\.0\.1\.1\s+)\S+', r'\g<1>' + host, h, flags=re.M)
if h2 != h:
    say('/etc/hosts 127.0.1.1 ->', host)
    open('/etc/hosts', 'w').write(h2)

rules = '/etc/udev/rules.d'
for n in sorted(os.listdir(rules)):
    p = os.path.join(rules, n)
    for m in re.finditer(r'RUN\+="(/\S+?)"', open(p).read()):
        if not os.path.exists(m.group(1)):
            warn.append(f'{n}: RUN script {m.group(1)} missing; rule stashed')
            stash(p)
            break

sh('systemctl daemon-reload')
sh('udevadm control --reload')
for c in enab:
    sh(f'systemctl enable {c} 2>&1')
for c in live:
    if c in enab:
        sh(f'systemctl start {c} 2>&1')

print('\nRESULT')
for c in sorted(unit_state):
    print(f'  {c:44s} enabled={sh(f"systemctl is-enabled {c} 2>/dev/null") or "-":9s} active={sh(f"systemctl is-active {c} 2>/dev/null")}')
for w in warn:
    print('WARN ', w)
print('removed items are in', RM)
