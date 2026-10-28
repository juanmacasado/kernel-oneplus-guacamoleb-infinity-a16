// SPDX-License-Identifier: GPL-2.0
#include <stdbool.h>
#include <stdio.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <sys/syscall.h>
#include "uapi/supercall.h"
/* AArch64 Bionic requires PT_TLS alignment >= 64. */
static _Thread_local char tls_alignment __attribute__((aligned(64), used));
/* Read-only driver information; no settings, root grants or boot events. */
int main(void) {
    if (getuid() != 0) { fputs("root required\n", stderr); return 1; }
    int fd = -1;
    (void)syscall(SYS_reboot, KSU_INSTALL_MAGIC1, KSU_INSTALL_MAGIC2, 0, &fd);
    if (fd < 0) { fputs("KSU information fd unavailable\n", stderr); return 2; }
    struct ksu_get_info_cmd info = {0};
    struct ksu_get_version_tag_cmd tag = {0};
    if (ioctl(fd, KSU_IOCTL_GET_INFO, &info) < 0) { perror("GET_INFO"); close(fd); return 3; }
    if (ioctl(fd, KSU_IOCTL_GET_VERSION_TAG, &tag) < 0) { perror("GET_VERSION_TAG"); close(fd); return 4; }
    close(fd);
    tag.tag[sizeof(tag.tag)-1] = '\0';
    for (unsigned i=0; tag.tag[i]; ++i)
        if (tag.tag[i] < 32 || tag.tag[i] == '"' || tag.tag[i] == '\\') return 5;
    printf("{\"driver_version\":%u,\"driver_tag\":\"%s\",\"uapi\":%u,\"flags\":%u}\n",
           info.version, tag.tag, info.uapi_version, info.flags);
    return 0;
}
