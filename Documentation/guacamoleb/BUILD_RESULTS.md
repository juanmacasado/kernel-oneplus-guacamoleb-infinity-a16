# Resultado de compilación aislada

28 de octubre de 2026. **Image, DTB y módulos compilan y enlazan con éxito**
en el commit `30a151d718fb5b91ad20f44c5a1f16fade51de26`.
Las actualizaciones posteriores de documentación no forman parte del binario.
El inventario y los hashes SHA-256 están en [build-result.json](build-result.json).
Este documento describe la fase de compilación; el candidato boot preparado
posteriormente se documenta en [FLASH_CANDIDATE.md](FLASH_CANDIDATE.md).

## Entorno y autorización

El usuario autorizó expresamente ejecutar el [plan](BUILD_CHECK_PLAN.md).
Se usó Bubblewrap sin red, con el sistema y las fuentes en solo lectura,
`/tmp` privado y un directorio nuevo de salidas escribible. Cuatro trabajos,
tope de 8 GiB y monitor de tamaño/tiempo. La salida completa ocupó unos
840 MiB, por debajo del límite. No se instalaron dependencias.

Herramientas ya instaladas: Clang/LLD **23.1.4**, utilidades LLVM,
GCC anfitrión **16.2.1 20260810**. `HOSTCFLAGS=-O2 -std=gnu11` fija el
estándar de los auxiliares anfitriones de este árbol antiguo. Las herramientas
Android AArch64 generaron binarios que solo se inspeccionaron como datos.

Clang 23 sirve como diagnóstico: **no reproduce Clang Android r574158**.
Este resultado no se presenta como build oficial o de publicación.

## Configuración y objetivos

Se combinaron las peticiones de `vendor/sm8150-perf_defconfig` y
`vendor/oplus.config`, y se resolvieron con `olddefconfig`. Conserva KSU
integrado, hooks manuales y SUSFS; hooks dinámicos y SUS_MEMFD desactivados,
MODVERSIONS activo y firma de módulos desactivada como en la base.

No hay diferencias semánticas frente a la configuración extraída de la imagen
Android 16 de agosto: 5020 símbolos antiguos y 5021 actuales, considerando
ausencia como `n`. Esto no demuestra que los fuentes o binarios sean iguales.
Las peticiones de fragmentos descartadas por dependencias/choices y los avisos
de Kconfig quedaron registrados; no se forzaron opciones para silenciarlos.
Kconfig se resolvió en `0dcf4b1858c10547b20097306232c5d258bd07d6` y se
comprobó que los fragmentos y Kconfig del driver no cambiaron hasta el commit
compilado.

La compilación parcial de KSU y los archivos fs/mm modificados pasa. Después,
`make -j4 Image dtbs modules` termina con código **0**, en 301 segundos:

| Resultado | Comprobación offline |
|---|---|
| `arch/arm64/boot/Image` | Cabecera ARM64 válida; release `4.14.357-perf-g30a151d718fb` |
| `vmlinux` | KSU, sus hooks y SUSFS enlazados; sin símbolos fuertes indefinidos. Solo quedan dos referencias débiles opcionales de BTF |
| 20 DTB | Cabeceras FDT válidas, incluidos los cuatro de `18821`; sus fuentes conservan la base Android 16 |
| `wlan.ko` | ELF AArch64, vermagic de este kernel; las 393 importaciones fuertes están exportadas; los 394 CRC, incluido module_layout, coinciden con Module.symvers |
| Otros cuatro módulos | gspca_main, tcp_bic, tcp_htcp y tcp_westwood; sus 90 CRC combinados también coinciden |

El módulo WLAN **recién generado** corresponde a este kernel. No se ha
contrastado el WLAN que lleva instalada la ROM. La base mantiene un bypass
de CRC para WLAN cuando KSU está activo: ese bypass no acredita compatibilidad
de un módulo distinto.

## Diagnósticos y correcciones

Kbuild descubrió dos defectos adicionales, corregidos antes del resultado:

- Dos patrones grep con un paréntesis literal rompían el parseo de
  `$(shell ...)` del Makefile de KSU; ahora usan el identificador completo.
- La compilación parcial/paralela de KSU carecía de dependencia para generar
  `flask.h`. `prepare` invoca ahora la regla existente de SELinux antes de
  compilar KSU. No se reescriben fuentes durante el build.

No aparecen errores ni avisos del compilador en el log completo. Modpost
informa de **cuatro referencias entre secciones**, identificadas ejecutándolo
con diagnósticos detallados sobre el mismo `vmlinux.o`:
`update_manifest()` y `update_telephony_manifest()` referencian
`boot_command_line`, marcado `__initdata`.

El archivo `drivers/soc/oplus/system/oplus_project/qcom/oplus_project.c`
es idéntico al de la base Android 16. Las únicas llamadas activas observadas
proceden de `oplus_project_init()`, que es `__init` y `arch_initcall`, antes
de liberar initdata. Se documenta como aviso heredado de anotaciones; no se
ha alterado ese controlador ni comprobado su ejecución en hardware.

Las suites locales pasan: **24 contratos de fuentes, 18 regresiones negativas,
8 sondas C y 22 casos de límites con ASan/UBSan**. Su cobertura sigue siendo
la descrita en [REVIEW.md](REVIEW.md).

## Lo que falta

No se generó boot.img ni un ZIP instalable, no se ejecutaron APK o binarios
Android y no se accedió al teléfono. Image carece del empaquetado de boot
necesario; estos archivos no constituyen una propuesta de flasheo.

Siguen pendientes el toolchain Android de publicación, los módulos/boot sin
modificar de la ROM exacta y cualquier prueba de arranque, root, SELinux,
WLAN, suspensión, consumo o SUSFS en hardware. El commit exacto declarado por
la imagen antigua (`6e88ac37df0c`) no se ha recuperado. La compilación no
certifica ausencia de malware ni compatibilidad del daily driver.
