# KernelSU Next 3.4.2 — legacy port for guacamoleb

Official reference: [v3.4.2, 4c706b5938665866ebe16944a481a7b91e3396af](https://github.com/KernelSU-Next/KernelSU-Next/tree/4c706b5938665866ebe16944a481a7b91e3396af).
The 61-commit official v3.4.0..v3.4.2 delta was reviewed. This branch retains its
manual 4.14 backend and inline SUSFS 2.3.0. The resulting tag
`v3.4.2-legacy-a16-susfs2.3` identifies a **compatibility port**, not the unchanged
official GKI driver. Version code is explicitly pinned to 33355 rather than
inventing a commit count.

This historical report covers the 8bb17398 build. The subsequent Harish merge
and installed kernel are documented in [HARISH_UPDATES.md](HARISH_UPDATES.md)
and [PERSISTENT_TEST.md](PERSISTENT_TEST.md).

## Effective changes

- Import v3.4.2 `feature/module_blacklist.c/.h`, using the kernel's native
  mechanism. `block_modules` is empty by default: no module is blocked unless
  the user explicitly requests it.
- Retry forced features after post-fs-data and at the end of late initialization,
  matching the release. The current configuration forces no new values.
- Fix RCU reads of the SELinux policy inside the mutex on the branch using
  `selinux_state.policy`; retain the old backend's locks and the actual
  flex_array layout of this vendor 4.14 tree.
- Fix an additional legacy-port defect: the `force_feature` parser advanced
  past the final NUL because it tested pointer `end` rather than `*end`.
  ASan/UBSan tests pass 14 cases and reproduce heap-buffer-overflow when the
  old condition is restored.

## Official changes already present or specific to the backend

The preceding integration already included manager pinning/cache changes,
package extraction using strrchr, APK scanning outside the iterate_dir callback,
task_work deferral, shell_su_adb_only and the adbd SID, EVENT_SERVICES without
duplicates, forced features, avtab/xperms fixes and policydb.len synchronization.
Their legacy implementations were reviewed; they are not replaced with GKI
versions incompatible with 4.14.

The release's ksyscall change uses pt_regs wrappers unavailable in 4.14; this
port retains direct sys_* calls. RISC-V and its orig_a0 registers are not imported
into this ARM64 product. The release's new SUSFS LKM is not loaded over the
already active inline SUSFS. SELinux Hide retains the legacy implementation
adapted to this vendor tree, which differs from the GKI backend's policy-backup
reimplementation. Complete feature or hiding equivalence is not claimed.
Preinit remains disabled and UAPI remains 5, compatible with the manager.

## Manager

The APK was updated from v3.2.0/33129 to **v3.4.2/33355**, preserving its data.
SHA-256: `774a5511f7034a4930e881114e202319cbdc34c5aaaa5c7c6b6d2902364e4c58`.
Before updating, both APKs were cryptographically checked with apksigner: the
v2 certificate matches the previous APK and the driver's expected identity.
A local copy of the previous APK was retained. The app was not uninstalled
and its data was not wiped.

## Validation of this build

Compiled and tested commit: **8bb17398caddb23966f215e55518174687289353**.

- Image, 20 DTBs and five modules: complete build, status 0, 295.7 seconds.
- Configuration semantically identical to the preceding kernel; CRCs of the
  five generated modules and all 394 installed WLAN entries match.
- Four inherited section warnings in update_manifest and update_telephony_manifest,
  with unchanged OPlus source. One host compiler const warning in modpost,
  without a compilation error.
- 24 static contracts, 18 negative regressions, eight C probes, 22 string cases
  and 14 parser cases, including ASan rejection of the old loop.
- Successful temporary and persistent boots, UID 0, SELinux Enforcing,
  wlan0 up/carrier=1 and SUSFS v2.3.0 with ten features.
- Driver read by ioctl: **33355, v3.4.2-legacy-a16-susfs2.3, UAPI 5**.
- Installed manager: **v3.4.2 / 33355**.
- boot_a read after reboot: SHA-256
  `0af449c667ad7d09679f4c3c306785bfd47eed0cb5a9bccf174f1045811e22d7`,
  matching that new boot exactly. Previous ramdisk and DTBs were preserved
  byte for byte. boot_b was not written.

The backup preceding this update has SHA-256
`edaabd74693d0cf215e64c21817d1aa9662236eb3c05921569140c6fbccda6af`
and corresponds to tested kernel `30a151d718fb`. Long-term stability, all hardware
and hiding effectiveness remain outside this report. Diagnostic Clang 23 is
still used rather than the original Android Clang.

The project diagnostic [ksu_get_info.c](../../tools/guacamoleb/ksu_get_info.c)
only reads GET_INFO/GET_VERSION_TAG and was removed from the device temporary
directory after use. It was compiled with NDK r27d, API 29 and 64-byte ARM64 TLS
alignment; an initial API 24 attempt was rejected by Bionic before entering main.
