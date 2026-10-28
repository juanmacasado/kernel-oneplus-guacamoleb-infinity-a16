# Later Harish kernel updates for Infinity X Android 16

Review date: 28 October 2026. The user clarified that the goal was to find and
incorporate Harish updates after June rather than remain at that baseline.

## Provenance

Android 16 baseline: `943be052999e4d65f805f8c6a5f22b44ad832683`, branch `16-c`,
committer date 27 June 2026. None of the Android 16 branches inspected is newer.
Original backport author dates must not be confused with Harish integration dates.

The merged `17-c` branch from
[Codecity001/android_kernel_oneplus_sm8150](https://github.com/Codecity001/android_kernel_oneplus_sm8150)
is pinned to `b1d34c4a99eaed5531333781ec8f389c53b9bad9` (24 October 2026).
Common ancestor: `6ecfabed032b68a8f0a0fd003cf5fbfb6d672acb`.
The histories diverge by 832/1037 commits; excluding patch-equivalent entries
leaves 39/244, including merge commits. A merge preserves both ancestries,
including fixes specific to the Android 16 baseline.

The result incorporates network and skb/zerocopy fixes, WLAN/GTK and legacy
firmware compatibility, memory/KFENCE, RNG, camera, audio, suspend, IRQ, build
integration and GPU include-path changes, clone3/checkpoint-restore syscalls and
Baseband Guard. Linux remains **4.14.357**; this is not a move to another Linux
series. EROFS was already enabled in the preceding resolved configuration;
imported configuration requests do not make it a newly enabled feature.

## Android 16 integration decisions

- Retain the already tested **adapted KSU Next 3.4.2 legacy driver**, UAPI 5 and
  SUSFS 2.3.0, including memory, SELinux and manual-hook fixes. Do not restore
  setup scripts, preinit or broken hooks from the Harish reimport. Import the
  manual fstat hooks for init.rc size reporting; their implementations already
  exist in our driver.
- Retain all six vendor fstab DT nodes, the Android 16 display/ULPS fixes and
  paired IPA PM operations. Import the ramoops console/ECC changes and audio
  routing source fixes.
- Defer **56cf6b817bde**, the migration of OEM power_supply properties to
  oplus_chg: it removes the interface used by the Android 16 ROM. Keep the
  independent RTC fix already present and the newer log-reduction changes.
- Preserve FORTIFY, unprivileged BPF disabled, HZ=250, no forced module signing,
  no LTO and no Shadow Call Stack. Do not impose a different ABI on vendor
  binaries. Enable KFENCE, suspend/lockup diagnostics, DMA-BUF statistics and
  LZO pstore compression; preserve existing EROFS support.
- Build WLAN **into Image**, so driver updates are actually used instead of
  existing only in a .ko the ROM never loads. The code supports this mode.
  The ROM retains its old-module insmod attempt; the rebuilt driver is already
  registered. wlan0 and association were checked during boot tests. Vendor is
  not modified.
- Include Baseband Guard with boot/recovery blocking disabled. Protect its
  device cache with a spinlock and duplicate checks; initialize diagnostic
  storage even if get_cmdline fails. Identify zram through get_gendisk without
  opening a block device from an LSM hook. Its scope depends on the
  su/ksu/magisk SELinux domains and its partition list; it is not general
  protection against malicious root software.
- Retain structured ld detection: Harish's &&/|| expression can return two
  names for GNU gold. Import the independent addtree fix.
- Bound the new /proc/cmdline construction and check capacity before appending
  force_normal_boot. Both boot-migration options remain disabled for Android 16.
  Synthetic ASan/UBSan tests cover four configurations and 255 lengths per
  configuration, rejecting an unbounded append. Preserve the SUSFS cmdline path
  and its static buffer.

## Candidate validation

Compiled commit: `2e381f23e9cd70474f3a8b0e6d106e712e125359`.
Image, 20 DTBs and four modules compile in 305.7 seconds with less than 1 GiB
of output. WLAN is built in, so no vendor WLAN .ko installation is required.
The resolved configuration retains HZ=250 and the Android 16 options above.
The four manifest/initdata modpost warnings belong to the same OPlus code as
the baseline; those functions are called during their initcall.

The repacker passes byte-identical round trips and 14 rejection cases for
malformed, signed, reordered or fstab-modified images/DTBs. Each old DTB matches
exactly one file in the preceding build, byte for byte. The 20 replacement blobs
change only ramoops console-size and ecc-size; IDs, order and fstab remain intact.
Ramdisk and recovery DTBO are preserved exactly.

An explicitly authorized fastboot boot test wrote no partitions. Android booted
fully with root, SELinux Enforcing, KSU 33355/UAPI 5, SUSFS 2.3.0/ten features,
KFENCE and Baseband Guard. Built-in WLAN associated successfully, carrier=1,
operstate=up. The temporary GET_INFO probe was removed. A charger enable_irq
warning was reproduced after returning to the preceding installed kernel, in
the same function with unchanged source; it is an inherited warning rather
than one newly introduced by this merge. That temporary test ended on the
preceding boot, with its boot_a SHA-256 unchanged.

The user subsequently requested persistent installation. The same image is now
installed and passed two boots, three display off/on cycles and a local Wi-Fi
gateway ping test. The user reported working camera, audio and GPS. These
later results and their limits are in [PERSISTENT_TEST.md](PERSISTENT_TEST.md).
Deep suspend, overnight drain and long-term stability remain unvalidated.

The artifact is published as an experimental prerelease for the stated device
and ROM. The local PC ZIP is not published as a recovery installer. Supporting
records: [build-result-harish.json](build-result-harish.json),
[runtime-harish.json](runtime-harish.json) and
[runtime-harish-persistent.json](runtime-harish-persistent.json).
