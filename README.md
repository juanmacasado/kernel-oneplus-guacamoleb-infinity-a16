# OnePlus 7 — Infinity X Android 16 kernel

Kernel sources for **OnePlus 7 (`guacamoleb`, tested on GM1901)** running
**Infinity X 3.12 Vanilla / Android 16**.

This fork merges Harish updates through the Android 17 `17-c` branch of
24 October 2026 into the Android 16 baseline, retaining the boot and vendor
interfaces required by the Android 16 ROM. It is not an Android 17 boot-image
replacement and does not include GApps.

| Component | Current tested build |
|---|---|
| Linux | 4.14.357-perf-g2e381f23e9cd |
| Compiled source | `2e381f23e9cd70474f3a8b0e6d106e712e125359` |
| KernelSU Next | v3.4.2-legacy-a16-susfs2.3, driver 33355, UAPI 5 |
| SUSFS | 2.3.0, inline/non-GKI |
| WLAN | Built into Image |
| Status | Experimental prerelease; installed and initially tested |

## Download

[Release: boot.img, checksums and build information](https://github.com/juanmacasado/kernel-oneplus-guacamoleb-infinity-a16/releases/tag/guacamoleb-a16-ksunext-3.4.2-susfs-2.3.0-20261028).

The boot image is **100663296 bytes (96 MiB)**. SHA-256:

```text
1a13d1e5d0699b0619fd16afe7669cdf6d051fb02bb11883ef7f14aaf4be3042
```

Download the accompanying README and SHA256SUMS/SHA512SUMS and verify them before
use. The release contains **no recovery-flashable ZIP**. GitHub's generated source
archives contain source code, not an installer. Private device backups remain local.

## Validation and limits

The image passed a temporary boot and two boots after installation into boot_a,
with Android fully started, root, SELinux Enforcing, KSU and SUSFS responding,
and Wi-Fi connected. Three display off/on cycles and four local gateway pings
passed. The owner reported working camera, audio and GPS.

Deep suspend, overnight drain, cellular calls and long-term stability remain
unvalidated. A charger IRQ warning also reproduces with the preceding kernel.
Builds used diagnostic Clang/LLD 23.1.4 rather than the original Android release
toolchain. Initial success is not a complete hardware or stability qualification.

## Documentation

- [Integration and validation overview](Documentation/guacamoleb/README.md)
- [Harish merge and Android 16 compatibility decisions](Documentation/guacamoleb/HARISH_UPDATES.md)
- [Persistent installation and hardware checks](Documentation/guacamoleb/PERSISTENT_TEST.md)
- [KernelSU Next 3.4.2 legacy port](Documentation/guacamoleb/VERSION_3_4_2.md)
- [Source revisions](Documentation/guacamoleb/source-lock.json)
- [Isolated build plan](Documentation/guacamoleb/BUILD_CHECK_PLAN.md)
- [Initial integration review](Documentation/guacamoleb/REVIEW.md)

Historical reports identify their original stage and link to current results.
Kernel code, configuration and published boot bytes are unchanged by documentation
translations. Upstream Linux documentation remains available through [README](README).
