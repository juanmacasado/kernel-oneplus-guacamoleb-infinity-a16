# Installed Harish kernel: initial validation

On 28 October 2026, at the user's explicit request, `boot_a` on the OnePlus 7
GM1901 running Infinity X 3.12 Vanilla Android 16 was flashed. The installed
boot matches the published image. SHA-256:
`1a13d1e5d0699b0619fd16afe7669cdf6d051fb02bb11883ef7f14aaf4be3042`.
The exact preceding boot is retained locally, SHA-256
`0af449c667ad7d09679f4c3c306785bfd47eed0cb5a9bccf174f1045811e22d7`.
This operation wrote only boot_a.

Two boots from the installed partition passed with Android fully started,
root UID 0, SELinux Enforcing, KSU driver 33355/UAPI 5 and manager 3.4.2,
SUSFS 2.3.0 with ten features, and built-in WLAN connected. All four pings to
the local router replied without loss. Three display off/on cycles passed,
retaining the boot ID, completed Android boot and WLAN connection. The camera
service registers four devices; that inventory alone does not prove capture works.

The deep-suspend success counter remained zero: neither deep sleep nor overnight
drain was validated with the phone connected over USB. No new BUG/Oops/panic/
lockup diagnostics were found in the inspected logs from these boots. The
charger IRQ 600 warning also reproduced on the preceding kernel remains.

The user confirmed working camera, audio and GPS. These are the owner's manual
tests, distinct from the ADB observations. Afterwards, the same boot ID, completed
Android boot and WLAN connection were checked, with no new severe diagnostics
in the inspected log. Cellular calls, all camera/audio modes and long-term
stability remain unvalidated.

The initial result is favorable, but the build remains experimental. The phone
was left with the new kernel installed. Unfiltered logs containing device and
network identifiers remain only on the local computer; the
[JSON report](runtime-harish-persistent.json) omits those identifiers.
