# Infinity X Android 16: KernelSU Next 3.4.2 legacy + SUSFS

Development branch for **OnePlus 7 (`guacamoleb`) running Infinity X 3.12 Vanilla
Android 16**, prepared on 28 October 2026.

This tree integrates **KernelSU Next 3.4.2 legacy**, SUSFS **2.3.0** and Harish
updates through `17-c` of 24 October 2026, adapted to the Android 16 ROM. The
histories were merged; boot and ABI exceptions are documented in
[HARISH_UPDATES.md](HARISH_UPDATES.md).

Kernel `2e381f23e9cd` builds Image, 20 DTBs and four modules, with WLAN built in.
After the temporary test, it was installed into **boot_a** at the user's request
and passed two boots from the installed partition: Android fully started, root,
SELinux Enforcing, driver 33355/UAPI 5, manager 3.4.2, SUSFS and WLAN. Three
display cycles and four pings to the local router also passed without loss.

The build remains experimental: the deep-suspend success counter stayed at zero
and extended hardware/endurance tests remain outstanding. The charger IRQ warning
also reproduces with the preceding kernel. The user confirmed working camera,
audio and GPS. Current evidence and limits: [persistent test](PERSISTENT_TEST.md)
and [sanitized runtime report](runtime-harish-persistent.json).

The preceding `8bb17398cadd` image is retained locally for recovery. Its history
is in [VERSION_3_4_2.md](VERSION_3_4_2.md). Earlier evidence:
[build](build-result-harish.json) and [temporary boot](runtime-harish.json).

## Baseline and provenance

- Kernel: [Codecity001/android_kernel_oneplus_sm8150](https://github.com/Codecity001/android_kernel_oneplus_sm8150),
  Android 16 branch `16-c` pinned to `943be052999e4d65f805f8c6a5f22b44ad832683`.
  The later merge imports `17-c` at `b1d34c4a99eaed5531333781ec8f389c53b9bad9`
  while retaining the Android 16 integration decisions.
- Driver reference: Harish's legacy/SUSFS integration at
  `b1d34c4a99eaed5531333781ec8f389c53b9bad9`, imported from `drivers/kernelsu`,
  including update `13af45224` and UAPI 5 alignment `4854e6820`.
- SUSFS: 21 cherry-picks with original authors and source references retained,
  taking the SUSFS 2.2.0 baseline through 2.3.0 and subsequent fixes.
- Compatibility: selected KernelSU Next legacy fixes from
  `165b87fa99abfe78058c4dc9df43c432e86b8011`, adapted to this tree.
- Release 3.4.2: official delta reviewed through
  `4c706b5938665866ebe16944a481a7b91e3396af`, porting applicable changes while
  retaining the manual 4.14 backend.

Full revisions and all 21 SUSFS source commits are listed in
[source-lock.json](source-lock.json). Remote branches may advance; the lock
records the revisions incorporated here.

Commit `6e88ac37df0c`, declared by the rooted 1 August image, was not recovered.
This is therefore an identified Android 16 source baseline, **not a demonstrated
reproduction of that image**. Modules and boot components must be checked against
the exact ROM before preparing or installing another build.

## Integration

The normal configuration uses the original two fragments:
`vendor/sm8150-perf_defconfig` and `vendor/oplus.config`. The latter enables
built-in KSU (`CONFIG_KSU=y`), manual hooks and the SUSFS features already enabled
in the old image. SUS_MEMFD remains disabled. Driver inclusion was added to
`drivers/Kconfig` and `drivers/Makefile`.

The initial root-only integration retained the Android 16 DTS/DTBs, vendor mount
scheme, module-signing policy and non-KSU product settings, replacing only the
kernel in an Android 16 backup. The later Harish merge also updates the DTBs:
only ramoops console-size and ecc-size change in the 20 packaged blobs. Their
IDs, order and vendor fstab remain intact. The Android 17 ROM's ramdisk, recovery,
fstab and policy are not imported. Ramdisk and recovery DTBO remain byte-identical
to the Android 16 template. [HARISH_UPDATES.md](HARISH_UPDATES.md) records the
additional resolved configuration changes, including built-in WLAN and KFENCE.

Root integration fixes:

- One hook in `do_execveat_common` covers native and compat `execve`/`execveat`,
  passes real addresses for `fd`/`flags`, checks the filename and avoids the old
  conversion of `AT_FDCWD` into a pointer.
- The declaration and call of `ksu_handle_sys_read` match the updated driver:
  `void(unsigned int fd)`.
- A manual devpts hook handles terminal labeling; manual fstat/fstat64 hooks
  account for the init.rc extension size.
- Manual sucompat logging includes the executable rather than complete arguments.
  It avoids interpreting `struct user_arg_ptr` as an array of kernel pointers,
  as the imported implementation did.
- Use the native `kvcalloc`, already backported here with overflow checking.
  Correct explicit includes and header precedence.
- Retain the actual SELinux `flex_array` layout used by this vendor 4.14 tree.
  Do not copy a generic legacy change to direct array access based only on the
  kernel version number.
- The KSU Makefile checks that required backports are tracked and fails if they
  are missing. Automatic source rewrites using `sed -i` were removed.
- Kbuild generates private SELinux headers before partial/parallel KSU compilation.
  Fix parsing of helper checks that previously prevented the build from starting.
- Keep manual init.rc integration. The new preinit runner and its build helper
  are omitted from this variant and must not activate merely because generated
  headers happen to exist in an output directory.

## Manager and versions

The driver reports code **33355**, UAPI **5**, and project tag
`v3.4.2-legacy-a16-susfs2.3`. GET_INFO/GET_VERSION_TAG verified these after reboot.
This identifies the documented legacy port, not complete equivalence with the
official GKI backend.

The public **KernelSU Next v3.4.2 manager** sources require driver 33188 or newer
and use UAPI 5. Fields in all 23 shared structures and numbers for the 20 shared
ioctl commands match the supercall header textually. The installed APK reports
v3.4.2/33355; its signature was cryptographically compared with the preceding
certificate. Runtime reads do not replace complete testing of every manager feature.

The `ksu_susfs` userspace helper must support SUSFS 2.3.0/non-GKI. A distributing
Android module may use a different version number; its name/version alone does
not prove compatibility. The universal helper was built from pinned sidex15
sources and installed. Queries return v2.3.0 and ten enabled features, both with
status 0. No new automatic hiding rules were configured.

## Validation

Run from the repository root:

```sh
python3 tools/guacamoleb/verify_integration.py --self-test
python3 tools/guacamoleb/check_c_contracts.py
python3 tools/guacamoleb/test_susfs_strings.py
python3 tools/guacamoleb/test_342_forced_features.py
python3 tools/guacamoleb/test_upstream_cmdline.py
python3 tools/guacamoleb/test_bbg_cache.py
```

The initial integration passed **24 source contracts and 18 negative regressions**.
After the Harish merge, this increased to **27 contracts and 21 negative regressions**.
They check driver inclusion, hook selection and signatures, object sources,
backports, SELinux layout and reviewed scope. Regressions mutate in-memory copies,
for example disabling KSU, changing module-signing policy or restoring a broken
hook, and require detection. The checker reads sources without running Kbuild,
target kernel code or network requests.

Eight syntax-only AArch64 C probes extract declarations and use synthetic types.
They check callbacks, hook signatures and `user_arg_ptr` layout; three negative
cases must fail with the expected diagnostic. They run no Kbuild or target code.
The pure string helper has 22 synthetic boundary cases under host ASan/UBSan.
LeakSanitizer is disabled because of the sandbox's ptrace restriction; that helper
performs no heap allocation. The forced-feature parser passes 14 ASan/UBSan cases;
restoring its invalid advancement beyond NUL must produce heap-buffer-overflow.
The imported cmdline initializer is checked across four configurations and 255
lengths each. The BBG cache test exercises actual cache functions using host
lock/hash stubs, eight threads and 10,000 iterations per thread.

The [follow-up review](REVIEW.md) records problems found after the first publication
and their fixes. The [Kbuild plan](BUILD_CHECK_PLAN.md) defines the isolated build
check that was authorized and completed. Initial resolved root-only configuration
matched the August Android 16 image semantically, treating missing options as
disabled. The later Harish build has separately reviewed configuration changes.

The initial full build passed with four inherited OPlus initialization section
warnings. Generated module CRCs and all 394 installed WLAN CRCs matched the
exports for that stage. The current image builds WLAN in instead of loading the
old vendor module. Boot, Wi-Fi association, root, SELinux, KSU and SUSFS were tested
on the phone; the owner reported working camera, audio and GPS. Those checks do
not establish long-term stability or complete hardware coverage.

## Outstanding validation

1. Rebuild with the intended Android release toolchain. The Android 16 common
   tree inspected selects Clang `r574158`; it was not downloaded or executed.
2. Complete testing of modules and runtime behavior. Previous WLAN CRC matches
   do not prove compatibility with every module. The source baseline retains a
   WLAN CRC bypass when KSU is active; that bypass is not compatibility evidence.
   Current WLAN is built into Image.
3. Validate deep suspend, overnight drain, cellular calls, extended use and all
   camera/audio modes. The initial manual checks are recorded separately.
4. Test hiding features and any particular Android modules the owner intends
   to use. Their effectiveness cannot be inferred from the enabled-feature list.

Local checks and, following explicit authorization, Kbuild and helpers ran with
no network, read-only sources and less than 1 GiB of output against the 8 GiB
limit. Later authorization covered ADB reads, boot_a backup and local boot
packing. Setup scripts were not run, dependencies were not installed, OTAs were
not extracted and images were not mounted.

The user subsequently requested flashing and updating both manager and driver.
Temporary boot tests preceded writing only boot_a, with backups and post-reboot
hash verification. The manager APK was updated without clearing its data, and
the requested SUSFS helper was installed. The newer Harish image was subsequently
installed and tested as documented in [PERSISTENT_TEST.md](PERSISTENT_TEST.md).
