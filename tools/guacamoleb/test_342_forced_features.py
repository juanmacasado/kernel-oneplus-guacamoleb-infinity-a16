#!/usr/bin/env python3
"""Exercise the imported pure boot-param parser with synthetic host stubs."""
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
source = (ROOT / 'drivers/kernelsu/policy/feature.c').read_text()
enum = (ROOT / 'drivers/kernelsu/include/uapi/feature.h').read_text()
names = re.search(r'static const char \*const feature_names.*?\n};', source, re.S)[0]
parse_id = source.split('static int parse_feature_id', 1)[1].split('\n}', 1)[0]
parse_value = source.split('static int force_feature_param_set', 1)[1].split('\n}', 1)[0]
prefix = r'''
#define _GNU_SOURCE
#include <assert.h>
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef uint32_t u32;
typedef uint64_t u64;
struct kernel_param { int unused; };
#define pr_info(...) ((void)0)
#define pr_err(...) ((void)0)
static int kstrtou32(const char *s, int base, u32 *out) {
    char *end; errno = 0; unsigned long long v = strtoull(s, &end, base);
    if (!*s || *s == '-' || *end || errno || v > UINT32_MAX) return -EINVAL;
    *out = v; return 0;
}
static int kstrtou64(const char *s, int base, u64 *out) {
    char *end; errno = 0; unsigned long long v = strtoull(s, &end, base);
    if (!*s || *s == '-' || *end || errno) return -EINVAL;
    *out = v; return 0;
}
static void set_bit(unsigned id, unsigned long *a) { a[id] = 1; }
'''
body = prefix + enum + names + r'''
static u64 forced_values[KSU_FEATURE_MAX];
static unsigned long forced_mask[KSU_FEATURE_MAX], forced_pending[KSU_FEATURE_MAX];
''' + 'static int parse_feature_id' + parse_id + '\n}\n' + 'static int force_feature_param_set' + parse_value + '\n}\n'
body += r'''
static void check(const char *text, int count, int id1, u64 value1, int id2, u64 value2) {
    memset(forced_values, 0, sizeof(forced_values));
    memset(forced_mask, 0, sizeof(forced_mask));
    memset(forced_pending, 0, sizeof(forced_pending));
    char *p = text ? strdup(text) : NULL;
    assert(force_feature_param_set(p, NULL) == 0);
    int actual = 0;
    for (unsigned i = 0; i < KSU_FEATURE_MAX; ++i) {
        assert(forced_mask[i] == forced_pending[i]);
        actual += !!forced_mask[i];
    }
    assert(actual == count);
    if (id1 >= 0) assert(forced_mask[id1] && forced_values[id1] == value1);
    if (id2 >= 0) assert(forced_mask[id2] && forced_values[id2] == value2);
    free(p);
}
int main(void) {
    check(NULL, 0, -1, 0, -1, 0);
    check("", 0, -1, 0, -1, 0);
    check("su_compat:1", 1, 0, 1, -1, 0);
    check("0:0", 1, 0, 0, -1, 0);
    check("adb_root:1,selinux_hide:0", 2, 3, 1, 4, 0);
    check("adb_root:1,", 1, 3, 1, -1, 0);
    check(",,", 0, -1, 0, -1, 0);
    check("bad", 0, -1, 0, -1, 0);
    check("unknown:1", 0, -1, 0, -1, 0);
    check("10004:1", 0, -1, 0, -1, 0);
    check("avc_spoof:0x3", 1, 10003, 3, -1, 0);
    check("su_compat:18446744073709551615", 1, 0, UINT64_MAX, -1, 0);
    check("su_compat:18446744073709551616", 0, -1, 0, -1, 0);
    check("abcdefghijklmnopqrstuvwxyz0123456789:1", 0, -1, 0, -1, 0);
    puts("14 cases passed");
}
'''
env = dict(os.environ, ASAN_OPTIONS='detect_leaks=0:abort_on_error=1')
results = {}
with tempfile.TemporaryDirectory(prefix='ksu342-parser-') as directory:
    for label, text in [('fixed', body), ('reject_old_loop', body.replace('p = *end ? end + 1 : end', 'p = end ? end + 1 : end'))]:
        p = Path(directory) / (label + '.c')
        exe = Path(directory) / label
        p.write_text(text)
        subprocess.run(['/usr/bin/gcc', '-O1', '-g', '-fsanitize=address,undefined', '-fno-omit-frame-pointer', str(p), '-o', str(exe)], check=True, capture_output=True)
        run = subprocess.run([str(exe)], capture_output=True, text=True, env=env)
        if label == 'fixed':
            assert run.returncode == 0, run.stderr
        else:
            assert run.returncode != 0 and 'heap-buffer-overflow' in run.stderr, run.stderr
        results[label] = {'passed': True, 'returncode': run.returncode}
print(json.dumps({'synthetic_cases': 14, 'sanitizers': ['address', 'undefined'], 'results': results,
                  'scope': 'pure parser with host stubs; no kernel/Android execution'}, indent=2))
