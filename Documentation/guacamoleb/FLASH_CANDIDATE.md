# Candidato boot Android 16 y restauración

Preparado el 28 de octubre de 2026 a petición del usuario. **Imagen empaquetada
y verificada offline; todavía sin prueba de arranque.** No se ha ejecutado
fastboot, reiniciado ni flasheado el teléfono.

## Insumos contrastados con el dispositivo

El usuario autorizó ADB para lecturas concretas y posteriormente la copia de
`boot_a` mediante root. Se observaron OnePlus 7/GM1901, Infinity X **3.12**,
Android **16**, slot **A** y kernel `4.14.357-perf-g6e88ac37df0c`.
Las dos particiones boot tienen **100663296 bytes (96 MiB)**.

La copia leída de `boot_a` es idéntica a la imagen rooted de agosto local:
SHA-256 `46fd37244c31eb09381b2347d77a9d67396b2a42e03e61f4f19723aa0b28798e`.
Esta es la restauración preparada para el slot A observado. No se leyó boot_b
ni se presupone que contenga la misma ROM.

Se obtuvo también `/vendor/lib/modules/qca_cld3_wlan.ko` en lectura:
SHA-256 `c99c6949fd4e35d567e93e3808e39f8fea8fecd945f4d1248dc3070212bca9a8`.
Sus **394 CRC**, incluido module_layout, coinciden con las exportaciones del
kernel compilado. El resto del vermagic coincide. `same_magic()` de este
árbol omite la palabra de release cuando existen CRC: no hace falta falsear
la release del kernel ni sustituir WLAN para superar estos contratos estáticos.
Esto no sustituye la prueba funcional de Wi-Fi ni una auditoría completa de ABI.

Las propiedades Android dicen locked/green. Con un kernel rooted esas
propiedades no acreditan el estado real del bootloader; no se ha consultado
en fastboot ni se ha intentado desbloquearlo.

## Imagen producida

`boot-guacamoleb-infinity-a16-ksunext-susfs230-30a151d.img`

- Tamaño: **100663296 bytes**.
- SHA-256: `edaabd74693d0cf215e64c21817d1aa9662236eb3c05921569140c6fbccda6af`.
- Kernel: Image exacto del commit `30a151d718fb5b91ad20f44c5a1f16fade51de26`,
  con KSU Next legacy 33315/UAPI 5 y SUSFS 2.3.0.
- Se conservan **byte a byte** ramdisk, segundo cargador vacío, recovery DTBO
  y los 20 DTB originales; también cmdline, direcciones, Android 16/parche de
  cabecera y propiedades AVB. No se añaden GApps ni se importa ramdisk Android 17.
- Se recalculan tamaño del kernel, ID SHA-1 de boot, desplazamiento de recovery,
  tamaño/hash de la imagen en AVB y ubicación del footer. Se conserva algoritmo
  AVB **NONE**, salt, flags e índices de rollback; no se crea una firma OEM ni
  se altera una partición vbmeta del dispositivo.

El [empaquetador propio](../../tools/guacamoleb/repack_boot_v2.py) usa solo
Python estándar y exige hashes de entrada. Rechaza formatos inesperados y
plantillas AVB firmadas; crea la salida de forma exclusiva, sin sobrescribir.
Pasa una reconstrucción byte a byte de la plantilla y nueve casos negativos.
Una segunda lectura independiente del resultado verificó secciones, cambios
de cabecera, digest AVB y configuración incrustada.

El formato se contrastó con [boot headers de AOSP](https://source.android.com/docs/core/architecture/bootloader/boot-image-header),
el `mkbootimg.py` instalado leído como datos y las estructuras de
[AVB](https://android.googlesource.com/platform/external/avb/+/refs/heads/main/libavb/avb_hash_descriptor.h).
No se ejecutaron empaquetadores, instaladores o scripts descargados de terceros.

## Entrega y límites

El paquete para PC incluye candidato, backup exacto, SHA256SUMS, verificación
y pasos manuales para comprobar el bootloader, probar el arranque temporal,
instalar en el slot A y restaurarlo. **El ZIP de entrega no es un instalador
para recovery ni para KernelSU.** No hay scripts de flasheo automático.
El backup y datos obtenidos del teléfono se conservan localmente; no se
publican binarios ni identificadores USB en el fork.

El usuario todavía debe decidir una prueba de arranque por separado. El
toolchain continúa siendo Clang 23 de diagnóstico, y no se ha recuperado el
commit exacto de agosto. El gestor contrastado es KernelSU Next v3.4.2; el
helper/módulo de usuarios SUSFS debe admitir 2.3.0/non-GKI. No se ha inspeccionado
ni actualizado el conjunto instalado de módulos KernelSU. Una coincidencia
de CRC o un footer consistente no certifican arranque, seguridad o estabilidad.
