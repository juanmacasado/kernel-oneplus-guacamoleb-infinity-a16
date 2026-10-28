#!/usr/bin/env python3
"""Syntax-only C probes from source declarations; no Kbuild or target execution."""

import json
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]


def read(path):
    return (ROOT / path).read_text()


def prototype(text, name):
    match = re.search(r"(?:extern |static )?(?:int|void)\s+" + name + r"\s*\([^)]*\)", text)
    if not match:
        raise ValueError("missing declaration: " + name)
    return re.sub(r"^(?:extern |static )", "", match[0]) + ";\n"


def arg_struct(text, name):
    start = text.index("struct user_arg_ptr {")
    brace = text.index("{", start)
    depth = 1
    end = brace + 1
    while depth:
        depth += (text[end] == "{") - (text[end] == "}")
        end += 1
    return text[start:end].replace("struct user_arg_ptr", "struct " + name, 1) + ";\n"


def check(compiler, source, expected=True, failure_pattern=None):
    result = subprocess.run(
        [compiler, "--target=aarch64-linux-gnu", "-x", "c", "-std=gnu11", "-nostdinc",
         "-Werror", "-fsyntax-only", "-"],
        input=source, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=20,
    )
    ok = (result.returncode == 0) == expected
    if not expected:
        ok = ok and bool(failure_pattern and re.search(failure_pattern, result.stderr))
    return {"passed": ok, "expected_success": expected, "returncode": result.returncode,
            "diagnostic": result.stderr if not ok else ""}


def main():
    compiler = shutil.which("clang")
    if compiler is None:
        raise SystemExit("clang is required; no dependency will be installed")
    preamble = """struct seq_file; struct fsnotify_mark; struct file; struct filename;
typedef unsigned int compat_uptr_t;
typedef _Bool bool;
#define __user
"""
    fdinfo = read("fs/notify/fdinfo.c")
    ino = prototype(fdinfo, "inotify_fdinfo")
    fan = prototype(fdinfo, "fanotify_fdinfo")
    cb_type = "typedef void (*callback)(struct seq_file *, struct fsnotify_mark *, struct file *);\n"
    cb_assert = "_Static_assert(__builtin_types_compatible_p(__typeof__(&fanotify_fdinfo), callback), \"fanotify callback ABI\");\n"
    ino_assert = cb_assert.replace("fanotify", "inotify")
    results = {}
    results["fdinfo_callbacks"] = check(compiler, preamble + ino + fan + cb_type + cb_assert + ino_assert)
    results["reject_old_fanotify_callback"] = check(
        compiler, preamble + ino + fan.replace(", struct file *file", "") + cb_type + cb_assert,
        False, r"static assertion failed[^\n]*fanotify callback ABI")
    caller = prototype(read("fs/read_write.c"), "ksu_handle_sys_read")
    callee = prototype(read("drivers/kernelsu/runtime/ksud_integration.c"), "ksu_handle_sys_read")
    results["read_hook_declarations"] = check(compiler, preamble + caller + callee)
    results["reject_old_read_hook"] = check(
        compiler, preamble + caller.replace("void ksu_handle_sys_read", "int ksu_handle_sys_read") + callee,
        False, r"conflicting types for 'ksu_handle_sys_read'")
    exec_caller = prototype(read("fs/exec.c"), "ksu_handle_execveat")
    exec_callee = prototype(read("drivers/kernelsu/core/init.c"), "ksu_handle_execveat")
    results["exec_hook_declarations"] = check(compiler, preamble + exec_caller + exec_callee)
    structures = arg_struct(read("fs/exec.c"), "exec_args") + arg_struct(
        read("drivers/kernelsu/runtime/ksud.h"), "driver_args")
    layout = """
_Static_assert(sizeof(struct exec_args) == sizeof(struct driver_args), "argument size");
_Static_assert(__alignof__(struct exec_args) == __alignof__(struct driver_args), "argument alignment");
_Static_assert(__builtin_offsetof(struct exec_args, ptr) == __builtin_offsetof(struct driver_args, ptr), "pointer offset");
"""
    for compat in [False, True]:
        define = "#define CONFIG_COMPAT 1\n" if compat else ""
        if compat:
            extra = "_Static_assert(__builtin_offsetof(struct exec_args, is_compat) == __builtin_offsetof(struct driver_args, is_compat), \"compat offset\");\n"
        else:
            extra = ""
        results["user_arg_ptr_compat_" + str(compat).lower()] = check(
            compiler, preamble + define + structures + layout + extra)
    wrong = structures.replace("struct driver_args {", "struct driver_args { unsigned long bad_prefix;")
    results["reject_changed_user_arg_layout"] = check(
        compiler, preamble + wrong + layout, False, r"static assertion failed[^\n]*argument size")
    print(json.dumps({"probes": results, "compiler": compiler,
                      "scope": "synthetic declaration probes, syntax-only AArch64; no kernel build or target code execution"}, indent=2))
    raise SystemExit(0 if all(x["passed"] for x in results.values()) else 1)


if __name__ == "__main__":
    main()
