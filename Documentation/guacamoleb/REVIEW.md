# Follow-up integration review

28 October 2026. Starting point:
`54d672f23da147c472ba31b7ba2cfb9cc965626c`.

The first validation checked textual invariants, not a complete build or linkage.
This review found two errors in the published integration and five further
problems in inherited code. The authorized build found two more Kbuild defects,
also fixed. The full kernel and WLAN compile and link.

This report records that review stage. Later boot and device results are in
[VERSION_3_4_2.md](VERSION_3_4_2.md) and [PERSISTENT_TEST.md](PERSISTENT_TEST.md).

## Fixes

| Finding | Evidence and consequence | Fix |
|---|---|---|
| Resolver missing in manual mode | `do_lookup_symbols()` calls `ksu_lookup_kernel_symbols()`, but its object was selected only for syscall-table hooks, disabled by this product | Always link the resolver and initialize it once from `kernelsu_init()` before registering interfaces; remove initialization exclusive to the dynamic hook |
| kvcalloc fallback conflicts with the backport | `include/linux/mm.h` already defines `kvcalloc`; an added alias could turn it into a second `ksu_kvcalloc`, depending on include order | Use the native function and `check_mul_overflow`; explicitly include `linux/mm.h`. Do not infer absence from the 4.14 version number |
| Leak when SUSFS work is already pending | `ksu_handle_extra_susfs_work()` allocated `tw` before returning on `work_pending()`, without freeing it | Allocate after that early return; retain freeing when `task_work_add()` fails |
| Inconsistent fanotify callback signature | With SUS_MOUNT or SUS_KSTAT, `show_fdinfo()` expected three arguments while fanotify retained two. The old configuration disables FANOTIFY, but the combination was invalid | Use a consistent three-argument internal signature for inotify, fanotify and the dispatcher, regardless of SUSFS options |
| Unsynchronized init.rc claim/publication | READ_ONCE/WRITE_ONCE on `rc_hooked` did not prevent two readers claiming the proxy and writing its global operations concurrently | Protect checking, initialization and publication with a mutex; stop the repeated hook outside it |
| Unchecked userspace string termination | Path/uname commands copied complete arrays and then passed them to string functions without requiring an in-field NUL | Validate 12 fields across ten SUSFS inputs and return ENAMETOOLONG before use if the terminator is missing |
| Concurrent allocation of shared cmdline storage | Two writers could pass the pointer check and allocate different buffers, leaking one | Use a single static array, retaining publication/copy under the existing seqlock |
| Invalid KSU Makefile parsing | Literal parentheses in two grep patterns unbalanced `$(shell ...)`, so make failed before compilation | Match the identifier using `grep -wq` without the parenthesis |
| Missing SELinux header prerequisite | Partial/parallel KSU compilation could include `flask.h` before another directory generated it | Add a KSU-conditional `prepare` prerequisite using the existing SELinux rule. At this review stage, the remainder of the top-level Makefile retained the baseline hash |

At this stage, DTS, vendor mounting, module-signing policy and non-KSU product
settings from the Android 16 baseline were retained. The boot image was not
replaced with an Android 17 image.

## Expanded validation

- 24 source contracts and 18 negative regressions, including resolver selection
  in manual mode, fanotify signature, allocation order in SUSFS and the init.rc
  mutex. Scope checking now also includes new untracked files, previously missed.
- Eight C probes using installed Clang, `--target=aarch64-linux-gnu`, `-nostdinc`,
  `-Werror` and `-fsyntax-only`. They use only extracted declarations and synthetic
  types: callbacks, read/exec hook signatures and argument layout with/without
  CONFIG_COMPAT. Negative cases must produce the expected diagnostic; unrelated
  syntax failures do not count as success.
- 22 boundary cases for the added pure string helper, using GCC, ASan/UBSan and
  synthetic data. No Android code runs. LeakSanitizer does not work under this
  sandbox's ptrace restriction and is disabled only for this allocation-free test.
- Textual manager 3.4.2 contract: 23 shared structures, 20 shared ioctl numbers,
  UAPI 5 and minimum driver 33188, compared with driver 33315 at this stage.
- Local manager APK SHA-256:
  `774a5511f7034a4930e881114e202319cbdc34c5aaaa5c7c6b6d2902364e4c58`,
  matching the public asset digest previously retrieved as metadata. Its 998-byte
  v2 certificate has SHA-256
  `79e590113c4c4c0c222978e413a5faa801666957b1212a328e46c00c69821bf7`,
  matching the identity expected by the driver. At this review stage, data was
  extracted; the APK was not run and its complete signature had not yet been
  verified cryptographically. Later verification is recorded separately.
- `git diff --check` and scope checks against the Android 16 baseline.
- Kconfig, modified objects and a full build of Image, 20 DTBs and five modules
  with Clang/LLD 23.1.4, without errors. All 394 versioned WLAN CRCs, including
  module_layout, and the other four modules' CRCs match Module.symvers. Details,
  inherited warnings, hashes and limits are in [BUILD_RESULTS.md](BUILD_RESULTS.md).

## Remaining limits at this review stage

Compilation uses diagnostic Clang 23, not the original Android toolchain. The
installed WLAN module's 394 CRCs were subsequently compared and a
[boot candidate](FLASH_CANDIDATE.md) was prepared. At this stage there was no
validation of boot, effective root, SELinux, suspend, power consumption or SUSFS
behavior on hardware.

The exact August image commit remained unrecovered. This does not certify
absence of malware or compatibility with a daily driver. The user specifically
authorized the [isolated Kbuild plan](BUILD_CHECK_PLAN.md), with no dependency
installation, network or device access during that build-only stage.
