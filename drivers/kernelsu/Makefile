kernelsu-objs := core/init.o

kernelsu-objs += compat/kernel_compat.o
kernelsu-objs += feature/kernel_umount.o
kernelsu-objs += feature/sulog.o
kernelsu-objs += feature/sucompat.o
kernelsu-objs += feature/shell_su_adb_only.o
kernelsu-objs += feature/selinux_hide.o

kernelsu-objs += hook/hook_manager.o
kernelsu-objs += hook/lsm_hooks.o
kernelsu-objs += hook/setuid_hook.o
kernelsu-objs += extras.o
kernelsu-objs += tiny_sulog.o

kernelsu-objs += infra/file_wrapper.o
kernelsu-objs += infra/event_queue.o
kernelsu-objs += infra/symbol_resolver.o
kernelsu-objs += infra/seccomp_cache.o
kernelsu-objs += infra/su_mount_ns.o

ifneq ($(CONFIG_KSU_DISABLE_MANAGER),y)
kernelsu-objs += manager/apk_sign.o
kernelsu-objs += manager/throne_tracker.o
kernelsu-objs += manager/pkg_observer.o
endif

kernelsu-objs += policy/allowlist.o
kernelsu-objs += policy/app_profile.o
kernelsu-objs += policy/feature.o

kernelsu-objs += runtime/boot_event.o
kernelsu-objs += runtime/ksud_integration.o

kernelsu-objs += selinux/selinux.o
kernelsu-objs += selinux/rules.o
kernelsu-objs += selinux/sepolicy.o

kernelsu-objs += sulog/event.o
kernelsu-objs += sulog/fd.o

kernelsu-objs += supercall/dispatch.o
kernelsu-objs += supercall/perm.o
kernelsu-objs += supercall/supercall.o

kernelsu-objs += feature/adb_root.o

ifdef KBUILD_EXTMOD
ifeq ($(CONFIG_KSU_DISABLE_MANAGER),y)
ccflags-y += -DCONFIG_KSU_DISABLE_MANAGER=1
endif
ifeq ($(CONFIG_KSU_DISABLE_POLICY),y)
ccflags-y += -DCONFIG_KSU_DISABLE_POLICY=1
endif
ifeq ($(CONFIG_KSU_DEBUG),y)
ccflags-y += -DCONFIG_KSU_DEBUG=1
endif
endif

ccflags-y += -I$(srctree)/security/selinux -I$(srctree)/security/selinux/include
ccflags-y += -I$(objtree)/security/selinux -include $(srctree)/include/uapi/asm-generic/errno.h

ifeq ($(filter /%,$(src)),)
KSU_KERNEL_DIR := $(srctree)/$(src)
else
KSU_KERNEL_DIR := $(src)
endif

ccflags-y += -I$(KSU_KERNEL_DIR) -iquote $(KSU_KERNEL_DIR)/include

# Android 16 / Linux 4.14 uses the existing init.rc manual hook. The new
# preinit runner requires the pt_regs syscall hook ABI; do not auto-enable it
# based on whether an unrelated headers_install output happens to exist.
ccflags-y += -DKSU_NO_PREINIT

obj-$(CONFIG_KSU) += kernelsu.o

LPATH := /usr/bin/env PATH="$$PATH":/usr/bin:/usr/local/bin
MDIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))

# Vendored legacy + SUSFS integration from Harish b1d34c4a99ea.
# Base driver: sidex15 d999a2af + KernelSU-Next legacy 0b17f242.
# Selected applicable fixes from legacy 165b87fa99ab are applied locally.
# There is no upstream v3.4.2 legacy tag. Keep the inherited numeric ABI
# version, but identify this integration honestly rather than as a release.
KSU_GIT_VERSION := 3026
KSU_GIT_TAG := v3.4.0-legacy-a16-susfs2.3
KSU_GIT_VERSION_VALID := 1

# Calculate version if git version is available
ifdef KSU_GIT_VERSION_VALID
$(eval KSU_VERSION=$(shell expr 30000 + $(KSU_GIT_VERSION) + 289))
$(info -- KernelSU-Next version: $(KSU_VERSION))
else
# If there is no .git directory, use default version
$(warning "KSU_GIT_VERSION not defined! It is better to make KernelSU-Next a git repository!")
KSU_VERSION_FALLBACK := 1
$(info -- KernelSU-Next version fallback: $(KSU_VERSION_FALLBACK))
KSU_VERSION := $(KSU_VERSION_FALLBACK)
endif

# Allow integrators to pin the reported version (e.g. when backporting
# onto release branches where the commit count does not match releases)
ifdef KSU_VERSION_OVERRIDE
KSU_VERSION := $(KSU_VERSION_OVERRIDE)
$(info -- KernelSU-Next version override: $(KSU_VERSION))
endif
ccflags-y += -DKSU_VERSION=$(KSU_VERSION)

ifdef KSU_GIT_VERSION_VALID
$(eval KSU_VERSION_TAG=$(KSU_GIT_TAG))
else
$(warning "KSU_VERSION_TAG not defined! It is better to make KernelSU-Next a git submodule!")
KSU_VERSION_TAG_FALLBACK := v0.0.1
KSU_VERSION_TAG=$(KSU_VERSION_TAG_FALLBACK)
endif

ifdef KSU_VERSION_TAG_OVERRIDE
KSU_VERSION_TAG := $(KSU_VERSION_TAG_OVERRIDE)
endif

$(info -- KernelSU-Next tag: $(KSU_VERSION_TAG))
ccflags-y += -DKSU_VERSION_TAG=\"$(KSU_VERSION_TAG)\"

ifndef KSU_NEXT_MANAGER_SIZE
KSU_NEXT_MANAGER_SIZE := 0x3e6
endif

ifndef KSU_NEXT_MANAGER_HASH
KSU_NEXT_MANAGER_HASH := 79e590113c4c4c0c222978e413a5faa801666957b1212a328e46c00c69821bf7
endif

ifdef KSU_MANAGER_PACKAGE
ccflags-y += -DKSU_MANAGER_PACKAGE=\"$(KSU_MANAGER_PACKAGE)\"
$(info -- KernelSU-Next Manager package name: $(KSU_MANAGER_PACKAGE))
endif

$(info -- KernelSU-Next Manager signature size: $(KSU_NEXT_MANAGER_SIZE))
$(info -- KernelSU-Next Manager signature hash: $(KSU_NEXT_MANAGER_HASH))

# RKSU: checks for available hook
## Logic flipped for HAVE_KSU_HOOK: 0 is success, 1 is failure
HAVE_KSU_HOOK ?= 1

# Checks hooks state
ifeq ($(CONFIG_KSU_KPROBES_HOOK), y)
$(info -- KernelSU-Next: Hook mode: Kprobes)
ccflags-y += -DKSU_KPROBES_HOOK
# Let's make it 0, so it would pass.
HAVE_KSU_HOOK := 0
endif

ifeq ($(CONFIG_KSU_SYSCALL_TABLE_HOOK), y)
$(info -- KernelSU-Next: Hook mode: Syscall table patching)
ccflags-y += -DKSU_SYSCALL_TABLE_HOOK
HAVE_KSU_HOOK := 0
kernelsu-objs += hook/patch_memory.o
kernelsu-objs += hook/syscall_table_hook.o
endif

ifeq ($(CONFIG_KSU_MANUAL_HOOK), y)
HAVE_KSU_HOOK := $(shell grep -q "ksu_handle_sys_reboot" $(srctree)/kernel/reboot.c && echo 0 || echo 1)
ifeq ($(HAVE_KSU_HOOK),0)
$(info -- KernelSU-Next: Hook mode: Manual)
endif
endif

ifneq ($(HAVE_KSU_HOOK),0)
$(error -- KernelSU-Next: No hooks were defined, please integrate manual hooks in your kernel!)
endif

# Backports are tracked in this tree; never mutate sources from Kbuild.
ifneq ($(shell grep -Eq "^static int can_umount" $(srctree)/fs/namespace.c; echo $$?),0)
$(error KernelSU requires the tracked can_umount backport)
endif
ifneq ($(shell grep -Eq "^int path_umount" $(srctree)/fs/namespace.c; echo $$?),0)
$(error KernelSU requires the tracked path_umount backport)
endif
ifneq ($(shell grep -Eq "^int path_umount" $(srctree)/fs/internal.h; echo $$?),0)
$(error KernelSU requires the tracked path_umount declaration)
endif
ifneq ($(shell grep -q "atomic_t filter_count;" $(srctree)/include/linux/seccomp.h; echo $$?),0)
$(error KernelSU requires the tracked seccomp filter_count backport)
endif
ifneq ($(shell grep -q "selinux_inode(" $(srctree)/security/selinux/include/objsec.h; echo $$?),0)
$(error KernelSU requires the tracked selinux_inode helper)
endif
ifneq ($(shell grep -q "selinux_cred(" $(srctree)/security/selinux/include/objsec.h; echo $$?),0)
$(error KernelSU requires the tracked selinux_cred helper)
endif

# see security_delete_hooks
ifeq ($(shell grep -A5 "^struct security_hook_list" $(srctree)/include/linux/lsm_hooks.h 2>/dev/null | grep -q "struct hlist_node" 2>/dev/null; echo $$?),0)
$(info -- KSU_NEXT: security_hook_list - hlist_node found!)
ccflags-y += -DKSU_COMPAT_SECURITY_DELETE_HOOKS_HLIST
endif

# SELinux drivers check
ifeq ($(shell grep -q "current_sid(void)" $(srctree)/security/selinux/include/objsec.h; echo $$?),0)
ccflags-y += -DKSU_COMPAT_HAS_CURRENT_SID
endif
ifeq ($(shell grep -q "struct selinux_state " $(srctree)/security/selinux/include/security.h; echo $$?),0)
ccflags-y += -DKSU_COMPAT_USE_SELINUX_STATE
endif
ifeq ($(shell grep -q "^DEFINE_RWLOCK(policy_rwlock);" $(srctree)/security/selinux/ss/services.c; echo $$?),0)
ccflags-y += -DKSU_COMPAT_HAS_EXPORTED_POLICY_RWLOCK
endif
ifeq ($(shell grep -q "cpus_ptr;" $(srctree)/include/linux/sched.h; echo $$?),0)
ccflags-y += -DKSU_COMPAT_HAS_BACKPORTED_CPUS_PTR
endif
ifeq ($(shell grep -q "struct pid \*task_pgrp" $(srctree)/include/linux/sched.h; echo $$?),0)
ccflags-y += -DKSU_COMPAT_HAS_TASK_PGRP_FUNC
endif

# fallthrough check for allowlist v2
ifneq ($(shell [ -f $(srctree)/include/linux/compiler_attributes.h ] && grep -q "define fallthrough" $(srctree)/include/linux/compiler_attributes.h; echo $$?),0)
$(info -- KSU_NEXT: fallthrough in compiler_attributes.h not found)
ccflags-y += -DKSU_ALLOWLIST_DOES_NOT_HAVE_FALLTHROUGH
endif

# Handle optional backports
ifeq ($(shell grep -q "strncpy_from_user_nofault" $(srctree)/include/linux/uaccess.h; echo $$?),0)
ccflags-y += -DKSU_OPTIONAL_STRNCPY
endif

ifeq ($(shell grep -q "ssize_t kernel_read" $(srctree)/fs/read_write.c; echo $$?),0)
ccflags-y += -DKSU_OPTIONAL_KERNEL_READ
endif

ifeq ($(shell grep "ssize_t kernel_write" $(srctree)/fs/read_write.c | grep -q "const void" ; echo $$?),0)
ccflags-y += -DKSU_OPTIONAL_KERNEL_WRITE
endif

ifeq ($(shell grep -q "int\s\+path_mount" $(srctree)/fs/namespace.c; echo $$?),0)
ccflags-y += -DKSU_HAS_PATH_MOUNT
endif

ifeq ($(shell grep -q "int\s\+path_umount" $(srctree)/fs/namespace.c; echo $$?),0)
ccflags-y += -DKSU_HAS_PATH_UMOUNT
endif

# some old kernel backport this, let's check if put_seccomp_filter still exist
ifneq ($(shell grep -wq "put_seccomp_filter" $(srctree)/kernel/seccomp.c $(srctree)/include/linux/seccomp.h; echo $$?),0)
ifeq ($(shell grep -wq "seccomp_filter_release" $(srctree)/kernel/seccomp.c $(srctree)/include/linux/seccomp.h; echo $$?),0)
ccflags-y += -DKSU_OPTIONAL_SECCOMP_FILTER_RELEASE
endif
endif

ifeq ($(shell grep -q "security_inode_init_security_anon" $(srctree)/include/linux/security.h; echo $$?),0)
ccflags-y += -DKSU_COMPAT_HAS_INIT_SEC_ANON
endif

# Checks Samsung
ifeq ($(shell grep -q "CONFIG_KDP_CRED" $(srctree)/kernel/cred.c; echo $$?),0)
ccflags-y += -DSAMSUNG_UH_DRIVER_EXIST
endif

ifeq ($(shell grep -q "SEC_SELINUX_PORTING_COMMON" $(srctree)/security/selinux/avc.c; echo $$?),0)
ccflags-y += -DSAMSUNG_SELINUX_PORTING
endif

ccflags-y += -DEXPECTED_MANAGER_SIZE=$(KSU_NEXT_MANAGER_SIZE)
ccflags-y += -DEXPECTED_MANAGER_HASH=\"$(KSU_NEXT_MANAGER_HASH)\"

ccflags-y += -Wno-strict-prototypes -Wno-int-conversion -Wno-gcc-compat -Wno-missing-prototypes
ccflags-y += -Wno-declaration-after-statement -Wno-unused-function -Wno-unused-variable

## For susfs stuff ##
ifeq ($(shell test -e $(srctree)/fs/susfs.c; echo $$?),0)
$(eval SUSFS_VERSION=$(shell cat $(srctree)/include/linux/susfs.h | grep -E '^#define SUSFS_VERSION' | cut -d' ' -f3 | sed 's/"//g'))
$(info )
$(info -- SUSFS_VERSION: $(SUSFS_VERSION))
else
$(info -- You have not integrated susfs in your kernel yet.)
$(info -- Read: https://gitlab.com/simonpunk/susfs4ksu)
endif

# Keep a new line here!! Because someone may append config
