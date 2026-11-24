# Haar boot splash

- `haar-splash.png`: 1280x720, 128-colour PNG (54 KB) for GRUB `background_image`.
- `haar-splash-source-2048x1152.jpg`: Meta AI source. `alt-fog-heavy-2048x1152.jpg`: alternative.
- `grub-splash-snippet.cfg`: the lines that load it.

Tested 2026-11-24 in QEMU/OVMF with Secure Boot enforced: Ubuntu's signed shim plus signed
`grubx64.efi.signed` (2.14) displayed it, since png, gfxterm and all_video are built in.
An unsigned GRUB was rejected ("Security Violation"), so the splash does not weaken Secure Boot.
Not yet tested on the Latitude 3410. No logo is baked in; composite it from brand/brand.env.
