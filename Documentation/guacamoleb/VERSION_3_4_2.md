# KernelSU Next 3.4.2 — port legacy para guacamoleb

Referencia oficial: [v3.4.2, 4c706b5938665866ebe16944a481a7b91e3396af](https://github.com/KernelSU-Next/KernelSU-Next/tree/4c706b5938665866ebe16944a481a7b91e3396af).
Se revisó el delta oficial v3.4.0..v3.4.2, de 61 commits. Se conservan el
backend manual 4.14 y SUSFS inline 2.3.0 de esta rama. La etiqueta resultante
`v3.4.2-legacy-a16-susfs2.3` identifica un **port de compatibilidad**, no el
driver GKI oficial sin cambios. Código de versión fijado explícitamente en
33355, sin inventar un recuento de commits.

## Cambios efectivos

- Se incorpora de v3.4.2 `feature/module_blacklist.c/.h`, usando el mecanismo
  nativo del kernel. El parámetro `block_modules` está vacío por defecto:
  no se bloquea ningún módulo si el usuario no lo solicita expresamente.
- Se aplica la repetición de features forzadas tras post-fs-data y al terminar
  la inicialización tardía, como en la release. La configuración actual no
  fuerza valores nuevos.
- Se corrigen las lecturas RCU de la política SELinux dentro del mutex en la
  rama que utiliza `selinux_state.policy`; se conservan los locks del backend
  antiguo y su layout flex_array real en este vendor 4.14.
- Se corrige un defecto adicional del port legacy: el parser `force_feature`
  avanzaba más allá del NUL final porque comprobaba el puntero `end` en vez
  de `*end`. Una prueba con ASan/UBSan pasa 14 casos y reproduce el
  heap-buffer-overflow al reintroducir la condición antigua.

## Cambios oficiales ya presentes o específicos del backend

La integración anterior ya traía los cambios de pinning/caché de manager,
extracción de paquete mediante strrchr, escaneo de APK fuera del callback
iterate_dir, deferral mediante task_work, shell_su_adb_only y SID de adbd,
EVENT_SERVICES sin duplicados, features forzadas, correcciones de avtab/xperms
y sincronización de policydb.len. Se revisaron sus implementaciones legacy;
no se reemplazan por versiones GKI incompatibles con 4.14.

El cambio ksyscall de la release utiliza wrappers pt_regs inexistentes en
4.14; el port mantiene sus llamadas sys_* directas. RISC-V y sus registros
orig_a0 no se incorporan a este producto ARM64. El nuevo módulo SUSFS LKM
de la release tampoco se carga sobre el SUSFS inline que ya está activo.
SELinux Hide conserva la implementación legacy adaptada a este vendor, que
difiere de la reimplementación con backup de política del backend GKI; no se
afirma equivalencia completa de todas sus funciones o de su ocultación.
Preinit continúa desactivado y UAPI continúa en 5, compatible con el gestor.

## Gestor

Se actualizó el APK de v3.2.0/33129 a **v3.4.2/33355** conservando datos.
SHA-256: `774a5511f7034a4930e881114e202319cbdc34c5aaaa5c7c6b6d2902364e4c58`.
Antes de actualizar se validaron criptográficamente ambos APK con apksigner:
el certificado v2 coincide y es el esperado por el driver. Se conservó una
copia local del APK anterior. No se desinstaló la aplicación ni borraron datos.

## Estado de validación

Preparación del port: pasan los contratos estáticos existentes, ocho sondas C,
22 casos de strings y las 14 pruebas nuevas del parser. La compilación y
prueba de arranque de esta nueva revisión deben quedar registradas por su
commit exacto antes de considerarla instalada. Los informes anteriores
describen el kernel probado `30a151d718fb`, que sigue siendo el baseline de
recuperación mientras se valida este port.
