#!/usr/bin/env python3
"""Read-only source-contract checks; does not run Kbuild or target binaries."""

import argparse
import json
from pathlib import Path
import re
import subprocess

BASE = "943be052999e4d65f805f8c6a5f22b44ad832683"
ROOT = Path(__file__).resolve().parents[2]
KSU = "drivers/kernelsu/"
CONFIG = "arch/arm64/configs/vendor/oplus.config"
SUSFS_FILES = {
    "fs/namespace.c", "fs/notify/fdinfo.c", "fs/proc/fd.c",
    "fs/proc/task_mmu.c", "fs/proc_namespace.c", "fs/stat.c",
    "fs/statfs.c", "fs/super.c", "fs/susfs.c", "include/linux/susfs.h",
    "include/linux/susfs_def.h", "mm/shmem.c",
}
INTEGRATION_FILES = {
    CONFIG, "drivers/Kconfig", "drivers/Makefile", "fs/devpts/inode.c",
    "fs/exec.c", "fs/read_write.c",
}


def git(*args):
    return subprocess.check_output(
        ["git", "-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false", *args],
        cwd=ROOT, text=True,
    )


def config_values(text):
    out = {}
    for line in text.splitlines():
        match = re.fullmatch(r"(CONFIG_\w+)=(.*)", line)
        unset = re.fullmatch(r"# (CONFIG_\w+) is not set", line)
        if match:
            out[match[1]] = match[2]
        elif unset:
            out[unset[1]] = "n"
    return out


def validate(read, changed, original_config):
    checks = {}
    make = read(KSU + "Makefile")
    cfg = config_values(read(CONFIG))
    original = config_values(original_config)
    checks["product_enables_manual_root"] = all(cfg.get(k) == v for k, v in {
        "CONFIG_KSU": "y", "CONFIG_KSU_MANUAL_HOOK": "y",
        "CONFIG_KSU_DISABLE_MANAGER": "n", "CONFIG_KSU_DISABLE_POLICY": "n",
        "CONFIG_KSU_KPROBES_HOOK": "n", "CONFIG_KSU_SYSCALL_TABLE_HOOK": "n",
    }.items())
    checks["susfs_features_match_base"] = all(cfg.get(k) == "y" for k in [
        "CONFIG_KSU_SUSFS", "CONFIG_KSU_SUSFS_SUS_PATH", "CONFIG_KSU_SUSFS_SUS_MOUNT",
        "CONFIG_KSU_SUSFS_SUS_KSTAT", "CONFIG_KSU_SUSFS_TRY_UMOUNT",
        "CONFIG_KSU_SUSFS_SPOOF_UNAME", "CONFIG_KSU_SUSFS_ENABLE_LOG",
        "CONFIG_KSU_SUSFS_HIDE_KSU_SUSFS_SYMBOLS",
        "CONFIG_KSU_SUSFS_SPOOF_CMDLINE_OR_BOOTCONFIG",
        "CONFIG_KSU_SUSFS_OPEN_REDIRECT", "CONFIG_KSU_SUSFS_SUS_MAP",
    ]) and cfg.get("CONFIG_KSU_SUSFS_SUS_MEMFD") == "n"
    checks["non_root_product_settings_preserved"] = {
        k: v for k, v in cfg.items() if not k.startswith("CONFIG_KSU")
    } == {k: v for k, v in original.items() if not k.startswith("CONFIG_KSU")}
    checks["scope_preserves_android16_boot_and_drivers"] = all(
        p.startswith((KSU, "Documentation/guacamoleb/", "tools/guacamoleb/"))
        or p in SUSFS_FILES | INTEGRATION_FILES for p in changed
    )
    checks["driver_reachable_from_kbuild_and_kconfig"] = (
        'source "drivers/kernelsu/Kconfig"' in read("drivers/Kconfig")
        and "obj-$(CONFIG_KSU) += kernelsu/" in read("drivers/Makefile")
        and "obj-$(CONFIG_KSU) += kernelsu.o" in make
        and "obj-$(CONFIG_KSU_SUSFS) += susfs.o" in read("fs/Makefile")
        and "select THREAD_INFO_IN_TASK" in read("arch/arm64/Kconfig")
    )
    symbols = set(re.findall(r"^config (\w+)$", read(KSU + "Kconfig"), re.M))
    checks["root_config_symbols_declared"] = all(
        k.removeprefix("CONFIG_") in symbols for k in cfg if k.startswith("CONFIG_KSU")
    )
    objects = re.findall(r"^kernelsu-objs\s*(?:\+|:)?=\s*([^\n]+)", make, re.M)
    objects = [obj for row in objects for obj in row.split() if obj.endswith(".o")]
    checks["driver_object_sources_exist"] = bool(objects) and all(
        read(KSU + obj[:-2] + ".c") or read(KSU + obj[:-2] + ".S") for obj in objects
    )
    checks["kbuild_does_not_rewrite_sources"] = not re.search(
        r"\$\(shell[^\n]*(?:sed\s+-i|\b(?:curl|wget|patch|cp|mv|rm)\s)", make
    )
    checks["manual_init_path_is_deterministic"] = (
        "ccflags-y += -DKSU_NO_PREINIT" in make and "preinit/preinit.o" not in make
        and "$(wildcard $(KSU_UAPI_INC)" not in make
    )
    exe = read("fs/exec.c")
    common = exe.split("static int do_execveat_common(", 1)[1].split("\n}", 1)[0]
    checks["exec_hook_covers_native_and_compat_execveat"] = (
        exe.count("ksu_handle_execveat(&fd, &filename, &argv, &envp, &flags);") == 1
        and "ksu_handle_execveat(&fd" in common
        and "if (!IS_ERR_OR_NULL(filename))" in common
        and "(int *)AT_FDCWD" not in exe
    )
    rw = read("fs/read_write.c")
    checks["read_hook_matches_updated_driver_abi"] = (
        "extern void ksu_handle_sys_read(unsigned int fd);" in rw
        and "ksu_handle_sys_read(fd);" in rw
        and "void ksu_handle_sys_read(unsigned int fd)" in read(KSU + "runtime/ksud_integration.c")
        and "ksu_handle_sys_read(fd, " not in rw
    )
    pts = read("fs/devpts/inode.c")
    checks["manual_devpts_hook_present"] = (
        "ksu_handle_devpts(d_inode(dentry));" in pts
        and bool(re.search(r"int\s+(?:__maybe_unused\s+)?ksu_handle_devpts\(struct inode \*inode\)",
                           read(KSU + "feature/sucompat.c")))
    )
    checks["legacy_allocations_check_overflow"] = (
        "#include <linux/mm.h>" in read(KSU + "compat/kernel_compat.h")
        and "#define kvcalloc" not in read(KSU + "compat/kernel_compat.h")
        and "check_mul_overflow(n, size, &bytes)" in read("include/linux/mm.h")
        and "return kvmalloc_array(n, size, flags | __GFP_ZERO);" in read("include/linux/mm.h")
        and '#include "compat/kernel_compat.h"' in read(KSU + "supercall/dispatch.c")
    )
    resolver_assignment = "kernelsu-objs += infra/symbol_resolver.o"
    dynamic_hook_block = make.split("ifeq ($(CONFIG_KSU_SYSCALL_TABLE_HOOK), y)", 1)[1].split("endif", 1)[0]
    checks["resolver_available_in_manual_mode"] = (
        make.count(resolver_assignment) == 1 and resolver_assignment not in dynamic_hook_block
        and "ksu_init_symbol_resolver();" in read(KSU + "core/init.c")
        and "ksu_init_symbol_resolver();" not in read(KSU + "hook/syscall_table_hook.c")
    )
    fdinfo = read("fs/notify/fdinfo.c")
    checks["fdinfo_callbacks_have_consistent_signatures"] = all(
        f"static void {name}(struct seq_file *m, struct fsnotify_mark *mark, struct file *file)" in fdinfo
        for name in ["inotify_fdinfo", "fanotify_fdinfo"]
    ) and "show(m, mark, f);" in fdinfo and "show(m, mark);" not in fdinfo
    work = read(KSU + "hook/setuid_hook.c").split("static void ksu_handle_extra_susfs_work(void)", 1)[1].split("\n}", 1)[0]
    checks["susfs_work_does_not_leak_on_pending_branch"] = (
        work.index("if (work_pending(") < work.index("kzalloc(sizeof(*tw)")
        and "kfree(tw);" in work
    )
    proxy = read(KSU + "runtime/ksud_integration.c").split("static void ksu_apply_init_rc_proxy(struct file *file)", 1)[1].split("\n}", 1)[0]
    checks["init_rc_proxy_claim_and_publication_serialized"] = (
        "static DEFINE_MUTEX(rc_proxy_lock);" in proxy
        and "mutex_lock(&rc_proxy_lock);" in proxy
        and proxy.index("mutex_lock(&rc_proxy_lock);") < proxy.index("if (rc_hooked)")
        and proxy.index("file->f_op = &fops_proxy;") < proxy.index("rc_hooked = true;")
        and proxy.count("mutex_unlock(&rc_proxy_lock);") == 2
    )
    susfs = read("fs/susfs.c")
    string_fields = {
        "susfs_add_sus_path": ["target_pathname"],
        "susfs_add_sus_path_loop": ["target_pathname"],
        "susfs_add_sus_kstat": ["target_pathname"],
        "susfs_update_sus_kstat": ["target_pathname"],
        "susfs_add_try_umount": ["target_pathname"],
        "susfs_set_uname": ["release", "version"],
        "susfs_add_open_redirect": ["target_pathname", "redirected_pathname"],
        "susfs_add_sus_map": ["target_pathname"],
        "susfs_add_sus_memfd": ["target_pathname"],
        "susfs_set_cmdline_or_bootconfig": ["fake_cmdline_or_bootconfig"],
    }
    guards = []
    for name, fields in string_fields.items():
        body = susfs.split(name + "(void __user **user_info)", 1)[1].split("\nout_copy_to_user:", 1)[0]
        operator = "->" if name == "susfs_set_cmdline_or_bootconfig" else "."
        guards.append("-ENAMETOOLONG" in body and all(
            f"susfs_string_terminated(info{operator}{field}, sizeof(info{operator}{field}))" in body
            for field in fields))
    checks["susfs_copied_strings_are_bounded"] = all(guards)
    checks["cmdline_buffer_has_single_static_storage"] = (
        "static char fake_cmdline_or_bootconfig[SUSFS_FAKE_CMDLINE_OR_BOOTCONFIG_SIZE];" in susfs
        and "fake_cmdline_or_bootconfig = (char *)kzalloc" not in susfs
    )
    checks["selinux_layout_matches_this_4_14_tree"] = (
        "struct flex_array *htable;" in read("security/selinux/ss/avtab.h")
        and "#if LINUX_VERSION_CODE < KERNEL_VERSION(5, 1, 0)\n"
        "        for (n = flex_array_get_ptr(db->te_avtab.htable, i); n;"
        in read(KSU + "selinux/sepolicy.c")
    )
    checks["manual_sulog_does_not_treat_user_arg_wrapper_as_kernel_array"] = (
        "const char *const sucompat_argv[] = { su, NULL };" in read(KSU + "feature/sucompat.c")
        and "(const char *const *)__never_use_argv" not in read(KSU + "feature/sucompat.c")
    )
    checks["susfs_2_3_and_correct_ctime_mask"] = (
        '#define SUSFS_VERSION "v2.3.0"' in read("include/linux/susfs.h")
        and "#define KSTAT_SPOOF_CTIME_TV_SEC (1 << 8)" in read("include/linux/susfs.h")
    )
    checks["tracked_backports_present"] = all([
        "static int can_umount(" in read("fs/namespace.c"),
        "int path_umount(" in read("fs/namespace.c"),
        "int path_umount(" in read("fs/internal.h"),
        "atomic_t filter_count;" in read("include/linux/seccomp.h"),
        "selinux_inode(" in read("security/selinux/include/objsec.h"),
        "selinux_cred(" in read("security/selinux/include/objsec.h"),
    ])
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    cache = {}

    def read(path):
        if path not in cache:
            file = ROOT / path
            cache[path] = file.read_text() if file.is_file() else ""
        return cache[path]

    changed = sorted(set(git("diff", "--no-ext-diff", "--no-textconv", "--name-only", BASE).splitlines()
                         + git("ls-files", "--others", "--exclude-standard").splitlines()))
    original = git("show", BASE + ":" + CONFIG)
    checks = validate(read, changed, original)
    mutations = [
        (CONFIG, "CONFIG_KSU=y", "CONFIG_KSU=n", "product_enables_manual_root"),
        (CONFIG, "# CONFIG_MODULE_SIG is not set", "CONFIG_MODULE_SIG=y", "non_root_product_settings_preserved"),
        (CONFIG, "# CONFIG_KSU_SUSFS_SUS_MEMFD is not set", "CONFIG_KSU_SUSFS_SUS_MEMFD=y", "susfs_features_match_base"),
        ("drivers/Makefile", "obj-$(CONFIG_KSU) += kernelsu/", "", "driver_reachable_from_kbuild_and_kconfig"),
        (KSU + "Makefile", "kernelsu-objs := core/init.o", "kernelsu-objs := core/missing.o", "driver_object_sources_exist"),
        (KSU + "Makefile", "ccflags-y += -DKSU_NO_PREINIT", "", "manual_init_path_is_deterministic"),
        ("fs/exec.c", "ksu_handle_execveat(&fd, &filename, &argv, &envp, &flags);", "ksu_handle_execveat((int *)AT_FDCWD, &filename, &argv, &envp, 0);", "exec_hook_covers_native_and_compat_execveat"),
        ("fs/read_write.c", "ksu_handle_sys_read(fd);", "ksu_handle_sys_read(fd, &buf, &count);", "read_hook_matches_updated_driver_abi"),
        ("fs/devpts/inode.c", "ksu_handle_devpts(d_inode(dentry));", "", "manual_devpts_hook_present"),
        ("include/linux/mm.h", "check_mul_overflow(n, size, &bytes)", "skip_mul_overflow(n, size, &bytes)", "legacy_allocations_check_overflow"),
        (KSU + "Makefile", "kernelsu-objs += infra/symbol_resolver.o", "", "resolver_available_in_manual_mode"),
        ("fs/notify/fdinfo.c", "fanotify_fdinfo(struct seq_file *m, struct fsnotify_mark *mark, struct file *file)", "fanotify_fdinfo(struct seq_file *m, struct fsnotify_mark *mark)", "fdinfo_callbacks_have_consistent_signatures"),
        (KSU + "hook/setuid_hook.c", "if (work_pending(&susfs_extra_works))", "tw = kzalloc(sizeof(*tw), GFP_ATOMIC);\n    if (work_pending(&susfs_extra_works))", "susfs_work_does_not_leak_on_pending_branch"),
        (KSU + "runtime/ksud_integration.c", "mutex_lock(&rc_proxy_lock);", "", "init_rc_proxy_claim_and_publication_serialized"),
        ("fs/susfs.c", "susfs_string_terminated(info.redirected_pathname, sizeof(info.redirected_pathname))", "unchecked_string(info.redirected_pathname)", "susfs_copied_strings_are_bounded"),
        ("fs/susfs.c", "static char fake_cmdline_or_bootconfig[SUSFS_FAKE_CMDLINE_OR_BOOTCONFIG_SIZE];", "static char *fake_cmdline_or_bootconfig;", "cmdline_buffer_has_single_static_storage"),
        ("include/linux/susfs.h", "KSTAT_SPOOF_CTIME_TV_SEC (1 << 8)", "KSTAT_SPOOF_CTIME_TV_SEC (1 < 8)", "susfs_2_3_and_correct_ctime_mask"),
    ]
    regression_count = 0
    if args.self_test:
        for path, old, new, check in mutations:
            source = read(path)
            assert old in source, (path, old)
            mutated = source.replace(old, new)
            result = validate(lambda p: mutated if p == path else read(p), changed, original)
            assert not result[check], ("regression not detected", check)
            regression_count += 1
        assert not validate(read, [*changed, "arch/arm64/boot/dts/qcom/sm8150.dtsi"], original)[
            "scope_preserves_android16_boot_and_drivers"]
        regression_count += 1
    print(json.dumps({"checks": checks, "negative_regressions": regression_count,
                      "scope": "static only; no compilation, execution of target code or device access"}, indent=2))
    raise SystemExit(0 if all(checks.values()) else 1)


if __name__ == "__main__":
    main()
