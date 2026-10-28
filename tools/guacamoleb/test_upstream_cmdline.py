#!/usr/bin/env python3
"""Run the imported cmdline initializer against synthetic boundary inputs."""
import json
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
source = (ROOT / 'fs/proc/cmdline.c').read_text()
body = source.split('#include <asm/setup.h>\n', 1)[1].split(
    '#ifdef CONFIG_KSU_SUSFS_SPOOF_CMDLINE_OR_BOOTCONFIG', 1)[0]
prefix = r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#define strlcpy test_strlcpy
#define strlcat test_strlcat
#define COMMAND_LINE_SIZE 128
static char input[256];
static char *saved_command_line = input;
static size_t strlcpy(char *d, const char *s, size_t n) {
    size_t l = strlen(s);
    if (n) { size_t c = l < n - 1 ? l : n - 1; memcpy(d, s, c); d[c] = 0; }
    return l;
}
static size_t strlcat(char *d, const char *s, size_t n) {
    size_t l = strnlen(d, n);
    if (l == n) return n + strlen(s);
    return l + strlcpy(d + l, s, n - l);
}
'''
suffix = r'''
int main(void) {
    for (size_t len = 0; len < sizeof(input) - 1; len++) {
        memset(input, 'x', len); input[len] = 0;
        if (len >= 14) memcpy(input, "skip_initramfs ", 14);
        proc_command_line_init();
        size_t copied = len < COMMAND_LINE_SIZE ? len : COMMAND_LINE_SIZE - 1;
        assert(strlen(proc_command_line) < COMMAND_LINE_SIZE);
#ifdef CONFIG_INITRAMFS_IGNORE_SKIP_FLAG
        if (len >= 14) assert(!strncmp(proc_command_line, "want_initramfs", 13));
#endif
#ifdef CONFIG_PROC_CMDLINE_APPEND_ANDROID_FORCE_NORMAL_BOOT
        const char *token = " androidboot.force_normal_boot=1";
        if (len >= 14 && copied + strlen(token) < COMMAND_LINE_SIZE) {
            assert(strlen(proc_command_line) == copied + strlen(token));
            assert(!strcmp(proc_command_line + copied, token));
        } else assert(strlen(proc_command_line) == copied);
#else
        assert(strlen(proc_command_line) == copied);
#endif
    }
    return 0;
}
'''
env = dict(os.environ, ASAN_OPTIONS='detect_leaks=0:abort_on_error=1')
results = []
with tempfile.TemporaryDirectory(prefix='guacamoleb-cmdline-') as directory:
    for ignore in (False, True):
        for append in (False, True):
            flags = []
            if ignore:
                flags += ['-DCONFIG_INITRAMFS_IGNORE_SKIP_FLAG']
            if append:
                flags += ['-DCONFIG_PROC_CMDLINE_APPEND_ANDROID_FORCE_NORMAL_BOOT']
            path = Path(directory) / 'probe.c'
            path.write_text(prefix + body + suffix)
            binary = Path(directory) / 'probe'
            subprocess.run(['/usr/bin/clang', '-fsanitize=address,undefined', '-g',
                            *flags, str(path), '-o', str(binary)], check=True)
            subprocess.run([str(binary)], check=True, env=env, capture_output=True)
            results.append({'ignore_skip': ignore, 'append_normal_boot': append,
                            'boundary_cases': 255})
    # The old unchecked append must fail with the same generated harness.
    broken = body.replace('if (sizeof(proc_command_line) - cmdline_len >=\n'
                          '\t\t    sizeof(" " ANDROID_FORCE_NORMAL_BOOT_STR))', 'if (1)')
    broken = broken.replace('strlcat(proc_command_line, " " ANDROID_FORCE_NORMAL_BOOT_STR,\n'
                            '\t\t\t\tsizeof(proc_command_line));',
                            'strcat(proc_command_line, " " ANDROID_FORCE_NORMAL_BOOT_STR);')
    assert broken != body
    path.write_text(prefix + broken + suffix)
    subprocess.run(['/usr/bin/clang', '-fsanitize=address,undefined', '-g',
                    '-DCONFIG_PROC_CMDLINE_APPEND_ANDROID_FORCE_NORMAL_BOOT',
                    str(path), '-o', str(binary)], check=True)
    result = subprocess.run([str(binary)], env=env, capture_output=True, text=True)
    assert result.returncode and 'global-buffer-overflow' in result.stderr
print(json.dumps({'configurations': results, 'unchecked_append_rejected': True}, indent=2))
