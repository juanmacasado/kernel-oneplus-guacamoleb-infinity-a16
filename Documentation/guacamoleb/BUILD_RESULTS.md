# Isolated build results

28 October 2026. **Image, DTBs and modules compile and link successfully** at
commit `30a151d718fb5b91ad20f44c5a1f16fade51de26`. Later documentation changes
are not part of that binary. The artifact inventory and SHA-256 hashes are in
[build-result.json](build-result.json).

This historical report covers the first build stage. The boot candidate prepared
later is documented in [FLASH_CANDIDATE.md](FLASH_CANDIDATE.md); the currently
installed Harish update is covered by [PERSISTENT_TEST.md](PERSISTENT_TEST.md).

## Environment and authorization

The user explicitly authorized the [plan](BUILD_CHECK_PLAN.md). Bubblewrap
provided no network, read-only system and sources, a private `/tmp`, and a new
writable output directory. The run used four jobs, an 8 GiB limit and output-size
and elapsed-time monitoring. Complete output occupied approximately 840 MiB,
below the limit. No dependencies were installed.

Already installed tools: Clang/LLD **23.1.4**, LLVM utilities and host GCC
**16.2.1 20260810**. `HOSTCFLAGS=-O2 -std=gnu11` pins the language standard for
this old tree's host helpers. Android AArch64 tools generated binaries that were
only inspected as data during this stage.

Clang 23 is diagnostic: **it does not reproduce Android Clang r574158**. This
result is not presented as an official build or a build using the release toolchain.

## Configuration and targets

Requests from `vendor/sm8150-perf_defconfig` and `vendor/oplus.config` were
combined and resolved with `olddefconfig`. Built-in KSU, manual hooks and SUSFS
remain enabled; dynamic hooks and SUS_MEMFD are disabled, MODVERSIONS is enabled,
and module signing is disabled as in the baseline.

There are no semantic differences from the configuration extracted from the
August Android 16 image: 5020 old symbols and 5021 current symbols, treating
absence as `n`. This does not prove identical sources or binaries. Requests
discarded because of dependencies/choices and Kconfig warnings were recorded;
options were not forced merely to silence them. Kconfig was resolved at
`0dcf4b1858c10547b20097306232c5d258bd07d6`; product fragments and the driver's
Kconfig were checked to be unchanged through the compiled commit.

The partial KSU build and modified fs/mm objects pass. Then
`make -j4 Image dtbs modules` finishes with status **0** in 301 seconds:

| Result | Offline check |
|---|---|
| `arch/arm64/boot/Image` | Valid ARM64 header; release `4.14.357-perf-g30a151d718fb` |
| `vmlinux` | KSU, its hooks and SUSFS linked; no undefined strong symbols. Only two optional weak BTF references remain |
| 20 DTBs | Valid FDT headers, including the four for `18821`; their sources retain the Android 16 baseline |
| `wlan.ko` | AArch64 ELF with this kernel's vermagic; all 393 strong imports are exported; all 394 CRCs, including module_layout, match Module.symvers |
| Four other modules | gspca_main, tcp_bic, tcp_htcp and tcp_westwood; their combined 90 CRCs also match |

The **newly generated** WLAN module corresponds to this kernel. At this stage,
the ROM's installed WLAN module had not been compared. The baseline retains a
WLAN CRC bypass when KSU is active; that bypass does not establish compatibility
with a different module.

## Diagnostics and fixes

Kbuild revealed two additional defects, fixed before the successful result:

- Two grep patterns containing literal parentheses broke parsing of
  `$(shell ...)` in the KSU Makefile; they now match the complete identifier.
- Partial/parallel KSU compilation lacked a dependency to generate `flask.h`.
  `prepare` now invokes the existing SELinux rule before compiling KSU.
  Sources are not rewritten during the build.

The original build log review reported no compiler errors or warnings. Modpost
reports **four cross-section references**, identified by running its detailed
diagnostics against the same `vmlinux.o`: `update_manifest()` and
`update_telephony_manifest()` reference `boot_command_line`, marked `__initdata`.

`drivers/soc/oplus/system/oplus_project/qcom/oplus_project.c` is identical to the
Android 16 baseline at this stage. The only active calls observed originate in
`oplus_project_init()`, marked `__init` and registered with `arch_initcall`, before
initdata is freed. This is documented as an inherited annotation warning; that
driver was not changed or exercised on hardware during this build stage.

Local suites pass: **24 source contracts, 18 negative regressions, eight C probes
and 22 boundary cases with ASan/UBSan**. Their coverage remains as described in
[REVIEW.md](REVIEW.md).

## Limits at this stage

No boot.img or installable ZIP was generated, no APK or Android binary was run,
and the phone was not accessed during this build stage. Image still needed boot
packing; these files alone were not a flash proposal.

The Android release toolchain, the exact ROM's unmodified modules/boot and all
hardware checks of boot, root, SELinux, WLAN, suspend, power consumption and
SUSFS were still pending. The exact commit declared by the old image
(`6e88ac37df0c`) was not recovered. Compilation does not certify absence of
malware or compatibility with a daily driver. Later outcomes are recorded
separately rather than retroactively attributed to this build-only stage.
