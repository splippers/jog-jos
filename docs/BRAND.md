# Brand guide — HAAR + JOS

## 1. Brand architecture

| Name | What it is | Expansion |
|---|---|---|
| **HAAR** | The portable imaging appliance: Ubuntu + FOG + the HAAR tooling | **Mobile Imaging System Toolkit** |
| **JOS** | The client runtime that boots on the machine being imaged | **HAAR OS** |
| **HAAR + JOS** | The combined product / project | — |

Use **HAAR** for the appliance, the server, the kiosk, the driver share, and the provisioning payload.
Use **JOS** for the Secure Boot chain, the initrd, the GRUB menu, and the client-side boot experience.
Use **HAAR + JOS** when talking about the whole solution.

Do not call the appliance "JOS" or the runtime "HAAR". The two names are the product's vocabulary.

## 2. Taglines

Primary:

> **Corporate reimaging, without the licence bill.**

Supporting:

- *Free, portable, Secure Boot imaging for corporate devices.*
- *One appliance. One stream. A room of laptops.*
- *From blank disk to domain-joined, encrypted asset.*

The five-minute claim is **imaging only** and must always be scoped that way. Never imply that the full
hybrid-join pipeline finishes in five minutes.

## 3. Voice

- Direct, technical, and honest.
- Prefer "reference design target" over "guaranteed".
- Say what is proven and what is new. The status table exists for a reason.
- No exclamation marks in product copy. No "revolutionary", "game-changing", or "effortless".
- British spelling in prose (`licence`, `organisation`, `normalise`); keep code identifiers and API names
  in their native spelling.

## 4. Palette

| Token | Hex | Use |
|---|---|---|
| Graphite | `#0B1220` | Backgrounds, lockup |
| Slate | `#1E293B` | Panels, borders |
| Muted | `#64748B` | Secondary text, dividers |
| Light | `#F8FAFC` | Primary text on dark |
| Cyan | `#22D3EE` | Primary accent, HAAR wordmark, links |
| Sky | `#0EA5E9` | Secondary accent, FOG references |
| Green | `#22C55E` | Success, `COMPLETE`, imaging target |
| Amber | `#F59E0B` | Warnings, pending states |
| Red | `#EF4444` | Failures, destructive actions |
| Ubuntu orange | `#E95420` | Only when referring to Ubuntu itself |

Use cyan as the single dominant accent. Do not put cyan text on white; use graphite or slate for light
backgrounds.

## 5. Typography

- Wordmark: bold sans-serif, generous letter spacing (`HAAR`, `JOS`).
- Headings: system sans (`Segoe UI`, `DejaVu Sans`, `Arial`).
- Console / code: monospace (`DejaVu Sans Mono`, `Consolas`, `monospace`).
- ASCII menus and serial output: **ASCII only**. No Unicode box drawing, arrows, or emoji in GRUB, the
  initrd, or the FOG console.

## 6. Assets

| Asset | Path | Use |
|---|---|---|
| Product lockup (SVG) | `jog-jos/branding/jog-jos-lockup.svg` | README header, slides, docs |
| JOS ASCII wordmark | `jos/branding/jos-logo.txt` | GRUB banner, initrd console |
| HAAR console tag | `[HAAR]` | Appliance scripts and logs |
| JOS console tag | `[JOS]` | Client runtime scripts and logs |

## 7. Lockup rules

- Keep clear space equal to the height of the "J" on all sides.
- Do not stretch, rotate, recolour, or add effects.
- Do not place the lockup on a busy photograph.
- The mark (laptop + multicast waves) may be used alone at small sizes; the wordmark may be used without
  the mark in inline text.
- Minimum width for the full lockup: 320 px.

## 8. Naming in code and docs

- Repository names: `haar`, `jos`, `jog-jos` (lowercase).
- Script prefixes: `haar-` for appliance scripts, `jos-` for client scripts.
- Environment variables: `JOG_*` and `JOS_*`.
- Log tags: `[haar-<script>]` and `[jos-<script>]`, with `[HAAR]`/`[JOS]` for user-facing banners.
- Windows payload: `JOGProvisioner`, `JOGProvisioning`, `C:\ProgramData\HAAR`.

## 9. What not to do

- Do not call the 5-minute figure an end-to-end deployment time.
- Do not claim 100-client imaging is proven until it has been measured on the target switch fabric.
- Do not put real domain names, passwords, or customer identifiers in examples. Use `corp.example.com`,
  `SITE01`, `LT-SITE01-ABC1234`.
- Do not store a BitLocker PIN in AD and present it as a supported design. The supported design is the
  recovery password in `msFVE-RecoveryPassword`.
