#!/usr/bin/env python3
"""Exercise the locally added bounded-string helper with synthetic host data."""

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]


def main():
    text = (ROOT / "fs/susfs.c").read_text()
    helper = re.search(
        r"static bool susfs_string_terminated\(const char \*str, size_t size\)\s*\{[^{}]*\}", text)
    if helper is None:
        raise SystemExit("bounded-string helper not found")
    # Only this small, locally reviewed pure helper may enter the host fixture.
    # No includes, declarations or other code from the kernel are executed.
    body = re.sub(r"\s+", " ", helper[0].split("{", 1)[1].rsplit("}", 1)[0]).strip()
    if body != "return memchr(str, '\\0', size) != NULL;":
        raise SystemExit("helper body changed; review it before running this fixture")
    source = "#include <stdbool.h>\n#include <stddef.h>\n#include <string.h>\n#include <stdio.h>\n"
    source += helper[0] + r'''
int main(void)
{
    const size_t sizes[] = { 1, 65, 256, 4096 };
    char buf[4096];
    unsigned tests = 0;
    for (size_t i = 0; i < sizeof(sizes) / sizeof(sizes[0]); ++i) {
        size_t size = sizes[i];
        memset(buf, 'x', sizeof(buf));
        if (susfs_string_terminated(buf, size)) return 1;
        ++tests;
        buf[size - 1] = 0;
        if (!susfs_string_terminated(buf, size)) return 2;
        ++tests;
        if (susfs_string_terminated(buf, size - 1)) return 3;
        ++tests;
        buf[0] = 0;
        if (!susfs_string_terminated(buf, size)) return 4;
        ++tests;
        if (susfs_string_terminated(buf, 0)) return 5;
        ++tests;
    }
    /* NUL beyond the field must not make a malformed field look valid. */
    memset(buf, 'x', sizeof(buf));
    buf[256] = 0;
    if (susfs_string_terminated(buf, 256)) return 6;
    ++tests;
    if (!susfs_string_terminated(buf, 257)) return 7;
    ++tests;
    printf("%u\n", tests);
    return 0;
}
'''
    compiler = shutil.which("gcc")
    if not compiler:
        raise SystemExit("gcc missing; no dependencies will be installed")
    with tempfile.TemporaryDirectory(prefix="guacamoleb-string-test-") as directory:
        path = Path(directory)
        src = path / "probe.c"
        exe = path / "probe"
        src.write_text(source)
        subprocess.run([compiler, "-std=gnu11", "-Wall", "-Wextra", "-Werror",
                        "-fsanitize=address,undefined", "-fno-omit-frame-pointer",
                        str(src), "-o", str(exe)], check=True, timeout=30)
        # The local command sandbox uses ptrace, unsupported by LeakSanitizer.
        # This pure helper allocates no heap; keep ASan bounds and UBSan enabled.
        env = dict(os.environ, ASAN_OPTIONS="detect_leaks=0:abort_on_error=1",
                   UBSAN_OPTIONS="halt_on_error=1")
        result = subprocess.run([str(exe)], check=True, text=True, stdout=subprocess.PIPE,
                                timeout=20, env=env)
        count = int(result.stdout.strip())
    print(json.dumps({"passed_cases": count, "sanitizers": ["address", "undefined"],
                      "leak_sanitizer": "disabled: ptrace sandbox; helper has no heap allocations",
                      "scope": "local pure helper and synthetic host data; no Kbuild or Android execution"}, indent=2))


if __name__ == "__main__":
    main()
