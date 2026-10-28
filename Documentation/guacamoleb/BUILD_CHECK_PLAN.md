# Comprobación local de Kbuild autorizada

El usuario autorizó el 28 de octubre de 2026 esta comprobación aislada,
respondiendo: «Sí, autoriza esa comprobación aislada». Esa autorización cumple
el requisito de AGENTS.md para ejecutar Kbuild y sus auxiliares dentro de este
alcance. Los resultados están en [BUILD_RESULTS.md](BUILD_RESULTS.md).
Este documento no autoriza acceso a un teléfono ni empaquetado de boot.

## Alcance concreto

- Generar `.config` con las peticiones de los fragmentos
  `vendor/sm8150-perf_defconfig` y `vendor/oplus.config`, y ejecutar `olddefconfig`.
- Comprobar que Kconfig conserva KSU integrado, manual hooks, SUSFS y la
  política de módulos prevista; registrar cualquier opción descartada.
- Compilar primero el objetivo de directorio `drivers/kernelsu/` y los archivos de fs/mm
  modificados. Si esa fase pasa, intentar `Image`, `dtbs` y módulos, incluido
  WLAN, y comprobar los símbolos enlazados.
- Usar las herramientas ya instaladas: Clang 23.1.4, LLD y utilidades LLVM,
  binutils GNU AArch64, GCC anfitrión, flex, bison y bc. No instalar ni
  descargar dependencias o toolchains ejecutables.

Clang 23 es un **toolchain diagnóstico**. No reproduce el Clang Android
`r574158` usado por la base de agosto. Los resultados deben identificar esta
diferencia; no se trasladarán a ciegas cambios para Clang 23 que alteren la
compatibilidad del toolchain original.

## Aislamiento y salidas

Bubblewrap se comprobó ejecutando únicamente `/usr/bin/true` con
`--unshare-all --die-with-parent --ro-bind / /`. El primer intento desde el
sandbox restringido falló por NETLINK_ROUTE; el intento fuera de esa restricción
confirmó que el aislamiento funciona sin sudo.

La ejecución autorizada usa ese aislamiento sin red, el sistema y las fuentes
en solo lectura, un `/tmp` privado y un directorio nuevo de salida dentro del
workspace como único directorio persistente escribible. No se reutilizará ni
borrará una salida ajena. Se limitarán los trabajos a cuatro y se interrumpirá
la ejecución si las salidas superan 8 GiB. Se conservarán comandos, resultados
y diagnósticos en ese directorio.

Los argumentos de Kbuild fijarán `ARCH=arm64`, `CC=/usr/bin/clang`,
`CLANG_TRIPLE=aarch64-linux-gnu-`, `CROSS_COMPILE=aarch64-linux-gnu-`,
`LD=/usr/bin/ld.lld`, `AR=/usr/bin/llvm-ar`, `NM=/usr/bin/llvm-nm` y
`OBJCOPY=/usr/bin/llvm-objcopy`, con `O=` apuntando al directorio nuevo.

Solo se ejecutarán Kbuild, sus auxiliares del árbol revisado y las herramientas
instaladas que requieren esos objetivos. Quedan fuera los setup/install scripts,
gestores de paquetes, extracción de OTA, empaquetado de boot, montajes de
imágenes, ADB, fastboot y cualquier modificación del teléfono.

Una compilación completa permitiría comprobar configuración, sintaxis y enlace.
No demostraría compatibilidad con el módulo WLAN instalado, reproducción de la
imagen de agosto ni arranque o funcionamiento en hardware.
