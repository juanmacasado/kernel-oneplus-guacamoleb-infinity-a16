#!/usr/bin/env python3
"""Exercise the actual BBG cache functions with host locks and synthetic IDs."""
import json
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
source = (ROOT / 'security/baseband-guard/baseband_guard.c').read_text()
cache = source.split('struct device_hash_node', 1)[1].split('static bool is_zram_device', 1)[0]
prefix = r'''
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdlib.h>
#include <pthread.h>
#include <stdatomic.h>
#include <sys/types.h>
struct hlist_node { struct hlist_node *next; };
#define DEFINE_HASHTABLE(name, bits) struct hlist_node *name[1 << (bits)]
#define DEFINE_SPINLOCK(name) pthread_mutex_t name = PTHREAD_MUTEX_INITIALIZER
#define spin_lock_irqsave(lock, flags) do { flags = 0; assert(!pthread_mutex_lock(lock)); } while (0)
#define spin_unlock_irqrestore(lock, flags) do { (void)flags; assert(!pthread_mutex_unlock(lock)); } while (0)
#define NODE(ptr) ((struct device_hash_node *)((char *)(ptr) - __builtin_offsetof(struct device_hash_node, h)))
#define hash_for_each_possible(table, p, member, key) \
    for (struct hlist_node *link = table[(key) & 127]; link && ((p = NODE(link)), 1); link = link->next)
#define hash_add(table, node, key) do { (node)->next = table[(key) & 127]; table[(key) & 127] = node; } while (0)
#define u64 uint64_t
#define GFP_ATOMIC 0
#define bb_pr(...) ((void)0)
static _Atomic unsigned allocated, released;
static bool fail_alloc;
static void *test_alloc(size_t n) {
    if (fail_alloc) return NULL;
    void *p = malloc(n); assert(p); allocated++; return p;
}
static void test_free(void *p) { if (p) released++; free(p); }
#define kmalloc(n, flags) test_alloc(n)
#define kfree(p) test_free(p)
'''
suffix = r'''
static void *worker(void *arg) {
    (void)arg;
    for (unsigned i = 0; i < 10000; i++) {
        dev_t d = 1 + i % 64;
        allow_add(d);
        assert(allow_has(d));
        assert(!allow_has(999));
    }
    return NULL;
}
int main(void) {
    allow_add(0); assert(!allow_has(0)); assert(allocated == 0);
    fail_alloc = true; allow_add(1); assert(!allow_has(1));
    fail_alloc = false;
    pthread_t threads[8];
    for (int i = 0; i < 8; i++) assert(!pthread_create(&threads[i], NULL, worker, NULL));
    for (int i = 0; i < 8; i++) assert(!pthread_join(threads[i], NULL));
    unsigned count = 0;
    for (int i = 0; i < 128; i++) {
        struct hlist_node *p = allowed_devs[i];
        while (p) { count++; p = p->next; }
    }
    assert(count == 64 && allocated - released == 64);
    for (int i = 1; i <= 64; i++) assert(allow_has(i));
    return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='guacamoleb-bbg-cache-') as directory:
    path = Path(directory) / 'cache.c'
    binary = Path(directory) / 'cache'
    path.write_text(prefix + 'struct device_hash_node' + cache + suffix)
    subprocess.run(['/usr/bin/clang', '-pthread', '-fsanitize=address,undefined',
                    '-g', str(path), '-o', str(binary)], check=True)
    subprocess.run([str(binary)], check=True,
                   env=dict(os.environ, ASAN_OPTIONS='detect_leaks=0:abort_on_error=1'))
print(json.dumps({'threads': 8, 'iterations_per_thread': 10000,
                  'unique_entries': 64, 'zero_and_allocation_failure': 'passed',
                  'scope': 'actual cache functions with host lock/hash stubs; no device I/O'}))
