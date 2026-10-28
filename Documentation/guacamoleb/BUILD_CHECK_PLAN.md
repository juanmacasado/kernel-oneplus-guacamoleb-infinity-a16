# Authorized isolated Kbuild check

On 28 October 2026, the user explicitly approved this isolated check. Their
confirmation, translated into English, was: “Yes, authorize that isolated check.”
This meets the inherited AGENTS.md requirement to authorize Kbuild and its
helpers within the following scope. Results are in [BUILD_RESULTS.md](BUILD_RESULTS.md).
This historical build plan does not itself authorize device access or boot packing.
For the current device state, see [PERSISTENT_TEST.md](PERSISTENT_TEST.md).

## Specific scope

- Generate `.config` from the requests in `vendor/sm8150-perf_defconfig` and
  `vendor/oplus.config`, then run `olddefconfig`.
- Check that Kconfig retains built-in KSU, manual hooks, SUSFS and the intended
  module policy; record any discarded options.
- First compile `drivers/kernelsu/` and the modified fs/mm files. If that passes,
  attempt `Image`, `dtbs` and modules, including WLAN, and inspect linked symbols.
- Use the already installed tools: Clang 23.1.4, LLD and LLVM utilities,
  AArch64 GNU binutils, host GCC, flex, bison and bc. Do not install or download
  dependencies or executable toolchains.

Clang 23 is a **diagnostic toolchain**. It does not reproduce Android Clang
`r574158`, used by the August baseline. Results must identify this difference;
changes needed for Clang 23 must not be copied blindly if they would alter
compatibility with the original toolchain.

## Isolation and output

Bubblewrap was checked by running only `/usr/bin/true` with
`--unshare-all --die-with-parent --ro-bind / /`. The first attempt inside the
restricted sandbox failed because of NETLINK_ROUTE. A subsequent attempt
outside that restriction confirmed that isolation works without sudo.

The authorized run uses no network, read-only system and source trees, a private
`/tmp`, and a new output directory inside the workspace as its only persistent
writable directory. It must not reuse or delete someone else's output. Limit the
build to four jobs and stop it if output exceeds 8 GiB. Preserve commands,
results and diagnostics in that directory.

Kbuild arguments pin `ARCH=arm64`, `CC=/usr/bin/clang`,
`CLANG_TRIPLE=aarch64-linux-gnu-`, `CROSS_COMPILE=aarch64-linux-gnu-`,
`LD=/usr/bin/ld.lld`, `AR=/usr/bin/llvm-ar`, `NM=/usr/bin/llvm-nm` and
`OBJCOPY=/usr/bin/llvm-objcopy`, with `O=` pointing to the new directory.

Only Kbuild, its helpers from the reviewed source tree, and the installed tools
required by those targets may run. Setup/install scripts, package managers,
OTA extraction, boot packing, image mounts, ADB, fastboot and all device changes
are outside this particular authorization.

A successful full build would check configuration, syntax and linkage. It would
not demonstrate compatibility with the installed WLAN module, reproduction of
the August image, or boot and hardware behavior.
