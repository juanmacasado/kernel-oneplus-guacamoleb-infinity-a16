# Android 16 boot candidate and recovery

Prepared on 28 October 2026 at the user's request. **Historical stage: image
packed and verified offline, before any boot test.** At this point, fastboot had
not been run and the phone had not been rebooted or flashed. For the subsequent
installed kernel, see [PERSISTENT_TEST.md](PERSISTENT_TEST.md).

## Inputs checked against the device

The user authorized specific ADB reads and later a root-assisted copy of
`boot_a`. Observed device: OnePlus 7/GM1901, Infinity X **3.12**, Android **16**,
slot **A**, kernel `4.14.357-perf-g6e88ac37df0c`. Both boot partitions have
**100663296 bytes (96 MiB)**.

The copy read from `boot_a` is identical to the local August rooted image:
SHA-256 `46fd37244c31eb09381b2347d77a9d67396b2a42e03e61f4f19723aa0b28798e`.
This is the recovery image prepared for observed slot A. boot_b was not read
and is not assumed to contain the same ROM.

`/vendor/lib/modules/qca_cld3_wlan.ko` was also copied read-only:
SHA-256 `c99c6949fd4e35d567e93e3808e39f8fea8fecd945f4d1248dc3070212bca9a8`.
Its **394 CRCs**, including module_layout, match the compiled kernel's exports.
The remainder of vermagic matches. This tree's `same_magic()` omits the release
word when CRCs exist: falsifying the kernel release or replacing WLAN is not
needed to satisfy these static contracts. This does not replace a functional
Wi-Fi test or a complete ABI audit.

Android properties report locked/green. With a rooted kernel, those properties
do not establish the actual bootloader state. At this stage, fastboot had not
been queried and no bootloader unlock had been attempted.

## Produced image

`boot-guacamoleb-infinity-a16-ksunext-susfs230-30a151d.img`

- Size: **100663296 bytes**.
- SHA-256: `edaabd74693d0cf215e64c21817d1aa9662236eb3c05921569140c6fbccda6af`.
- Kernel: exact Image from `30a151d718fb5b91ad20f44c5a1f16fade51de26`, with
  KSU Next legacy 33315/UAPI 5 and SUSFS 2.3.0.
- Ramdisk, empty second-stage loader, recovery DTBO and all 20 original DTBs
  are preserved **byte for byte**, as are cmdline, addresses, Android 16/header
  patch level and AVB properties. No GApps or Android 17 ramdisk is added.
- Kernel size, boot SHA-1 ID, recovery offset, AVB image size/hash and footer
  location are recalculated. AVB algorithm **NONE**, salt, flags and rollback
  indexes are preserved. No OEM signature is created and no device vbmeta
  partition is changed.

The [project repacker](../../tools/guacamoleb/repack_boot_v2.py) uses only the
Python standard library and requires input hashes. It rejects unexpected formats
and signed AVB templates, and creates output exclusively without overwriting.
The initial version passed a byte-identical template round trip and nine
negative cases. An independent second read checked sections, header changes,
AVB digest and embedded configuration.

The format was checked against [AOSP boot headers](https://source.android.com/docs/core/architecture/bootloader/boot-image-header),
the installed `mkbootimg.py` read as data, and the
[AVB structures](https://android.googlesource.com/platform/external/avb/+/refs/heads/main/libavb/avb_hash_descriptor.h).
No downloaded third-party packers, installers or scripts were executed.

## Delivery and limitations

The PC bundle includes the candidate, exact backup, SHA256SUMS, verification
results and manual steps to check the bootloader, test a temporary boot, install
into slot A and restore it. **The delivery ZIP is not a recovery or KernelSU
installer.** There are no automatic flashing scripts. The backup and device data
remain local; private backup binaries and USB identifiers are not published.

At this stage, the user still had to authorize a boot test separately. Clang 23
remained a diagnostic toolchain and the exact August source commit had not been
recovered. The manager checked was KernelSU Next v3.4.2; the SUSFS userspace
helper/module must support 2.3.0/non-GKI. The installed KernelSU module collection
had not been inspected or updated. Matching CRCs and a consistent footer do not
certify boot, security or stability.
