# Revisión posterior de la integración

28 de octubre de 2026. Punto de partida:
`54d672f23da147c472ba31b7ba2cfb9cc965626c`.

La primera validación comprobaba invariantes textuales; no era una
comprobación completa de compilación o enlace. Esta revisión encontró dos
errores en la integración publicada y cinco problemas adicionales en el código
heredado. Se han corregido en fuentes; la compilación sigue pendiente.

## Correcciones

| Hallazgo | Evidencia y consecuencia | Corrección |
|---|---|---|
| Resolver ausente en modo manual | `do_lookup_symbols()` llama a `ksu_lookup_kernel_symbols()`, pero su objeto solo se seleccionaba con syscall-table hooks. La configuración del producto los desactiva. | Compilar el resolver siempre e inicializarlo una vez desde `kernelsu_init()`, antes de registrar las interfaces. Retirar su inicialización exclusiva del hook dinámico. |
| Fallback de kvcalloc incompatible con el backport | `include/linux/mm.h` ya define `kvcalloc`. El alias añadido podía convertir esa definición en una segunda `ksu_kvcalloc`, según el orden de includes. | Usar la función nativa y su comprobación `check_mul_overflow`; incluir explícitamente `linux/mm.h`. No inferir su ausencia del número 4.14. |
| Fuga al encontrar trabajo SUSFS pendiente | `ksu_handle_extra_susfs_work()` reservaba `tw` antes de retornar por `work_pending()`, sin liberar la reserva. | Reservar después de esa salida temprana; conservar la liberación cuando falla `task_work_add()`. |
| Firma de callback fanotify incoherente | Con SUS_MOUNT o SUS_KSTAT activos, `show_fdinfo()` esperaba tres argumentos; fanotify conservaba dos. La configuración antigua tiene FANOTIFY desactivado, pero la combinación era inválida. | Usar una firma interna uniforme de tres argumentos para inotify/fanotify y para el despachador, independientemente de las opciones SUSFS. |
| Claim y publicación de init.rc sin exclusión | READ_ONCE/WRITE_ONCE sobre `rc_hooked` no impedían que dos lectores reclamaran simultáneamente el proxy y escribieran sus operaciones globales. | Proteger con mutex la comprobación, inicialización y publicación. Detener el hook repetido fuera del mutex. |

| Cadenas de usuarios sin terminación comprobada | Las órdenes de rutas y uname copiaban arrays completos y después los pasaban a funciones de strings, sin exigir un NUL dentro del campo. | Validar 12 campos en 10 entradas de SUSFS y devolver ENAMETOOLONG antes de utilizarlos si falta el terminador. |
| Reserva concurrente del cmdline compartido | Dos escritores podían superar el test del puntero y reservar buffers distintos, perdiendo una reserva. | Usar un único array estático, con la publicación y copia protegidas por el seqlock existente. |

Se mantuvieron el DTS, el montaje de vendor, la política de firmas y los
ajustes de producto ajenos a KSU de la base Android 16. No se sustituyó la
imagen de arranque por una de Android 17.

## Validación ampliada

- 23 contratos de fuentes y 18 regresiones negativas. Ahora se incluye la
  selección del resolver en modo manual, la firma fanotify, el orden de la
  reserva en SUSFS y el mutex de init.rc. El control de alcance también
  considera archivos nuevos no versionados, antes omitidos.
- 8 sondas C con Clang instalado, `--target=aarch64-linux-gnu`, `-nostdinc`,
  `-Werror` y `-fsyntax-only`. Se usan solo declaraciones extraídas y tipos
  sintéticos: callbacks, read/exec hooks y layout de los argumentos con y sin
  CONFIG_COMPAT. Los casos negativos deben producir el diagnóstico específico;
  un fallo ajeno de sintaxis no se cuenta como éxito.
- 22 casos de límites del helper de cadenas añadido localmente, con GCC, ASan
  y UBSan y datos sintéticos. No se ejecuta código Android. LeakSanitizer no
  funciona bajo el ptrace del sandbox y se desactiva solo en esa prueba; el
  helper no usa heap.
- Contrato textual del gestor 3.4.2: 23 estructuras y 20 números ioctl
  compartidos, UAPI 5 y mínimo de driver 33188 frente a 33315.
- APK local del gestor: SHA-256
  `774a5511f7034a4930e881114e202319cbdc34c5aaaa5c7c6b6d2902364e4c58`,
  coincidente con el digest del asset público previamente descargado como
  metadatos. Certificado v2 de 998 bytes y SHA-256
  `79e590113c4c4c0c222978e413a5faa801666957b1212a328e46c00c69821bf7`,
  coincidente con la identidad esperada por el driver. Se extrajeron datos;
  no se ejecutó el APK ni se verificó criptográficamente su firma completa.
- `git diff --check` y comprobación de alcance contra la base Android 16.

## Límites que permanecen

No se ha ejecutado Kconfig o Kbuild. Las sondas no compilan el kernel ni
resuelven todos sus símbolos. No hay validación de módulos instalados, arranque,
root efectivo, SELinux, suspensión, consumo o comportamiento de SUSFS.

El commit exacto de la imagen de agosto continúa sin recuperarse. No se
certifica ausencia de malware ni compatibilidad del daily driver. Para avanzar
en la verificación de compilación está preparado el
[plan aislado de Kbuild](BUILD_CHECK_PLAN.md), sin instalar dependencias,
sin red durante la ejecución y sin acceso al teléfono.
