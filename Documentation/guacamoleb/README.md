# Infinity X Android 16: KernelSU Next legacy + SUSFS

Rama de desarrollo para **OnePlus 7 (`guacamoleb`) con Infinity X 3.12 Vanilla
Android 16**, preparada el 28 de octubre de 2026.

El código integra KernelSU Next legacy actualizado y SUSFS **2.3.0** sobre la
rama Android 16 de Harish. **Compilan y enlazan Image, 20 DTB y los cinco
módulos con Clang 23. No está probado en hardware ni hay un boot.img nuevo
listo para instalar.** El resultado y los hashes están en
[BUILD_RESULTS.md](BUILD_RESULTS.md) y [build-result.json](build-result.json).

## Base y procedencia

- Kernel: [Codecity001/android_kernel_oneplus_sm8150](https://github.com/Codecity001/android_kernel_oneplus_sm8150),
  `16-c` fijada en `943be052999e4d65f805f8c6a5f22b44ad832683`.
- Driver: integración legacy/SUSFS de Harish en
  `b1d34c4a99eaed5531333781ec8f389c53b9bad9`, importada desde
  `drivers/kernelsu`. Incluye la actualización `13af45224` y la alineación
  UAPI 5 de `4854e6820`.
- SUSFS: 21 cherry-picks con autores y referencias de origen conservados,
  desde la base SUSFS 2.2.0 hasta 2.3.0 y sus correcciones posteriores.
- Compatibilidad: correcciones seleccionadas de KernelSU Next legacy
  `165b87fa99abfe78058c4dc9df43c432e86b8011`, adaptadas a este árbol.

Las revisiones y los 21 commits completos figuran en
[source-lock.json](source-lock.json). Las ramas remotas pueden avanzar; el lock
describe las revisiones incorporadas aquí.

No se recuperó el commit `6e88ac37df0c` declarado por la imagen rooted del
1 de agosto. Por ello esta rama es una base Android 16 identificada, **no una
reproducción demostrada de aquella imagen**. Antes de empaquetar o instalar
deben contrastarse los módulos de la ROM concreta y sus demás componentes.

## Integración

La configuración habitual sigue usando los dos fragmentos originales:
`vendor/sm8150-perf_defconfig` y `vendor/oplus.config`. Este último habilita
KSU integrado (`CONFIG_KSU=y`), manual hooks y las funciones SUSFS que ya
estaban habilitadas en la imagen antigua. SUS_MEMFD permanece desactivado.
Se añadió la inclusión del driver en `drivers/Kconfig` y `drivers/Makefile`.

Se conservan los DTS/DTB de la base Android 16, su esquema de montaje de vendor,
la política de firma de módulos y todos los ajustes de producto ajenos a KSU.
La actualización no importa el ramdisk, recovery, fstab o política de la ROM
Android 17. No se ha reempaquetado ninguna imagen ni alterado firmware.

Cambios específicos para la integración:

- Un único hook en `do_execveat_common` cubre `execve` y `execveat`, tanto
  nativos como compat. Pasa direcciones reales de `fd` y `flags`, comprueba el
  filename y evita las conversiones antiguas de `AT_FDCWD` a puntero.
- La declaración y llamada de `ksu_handle_sys_read` coinciden ahora con el
  driver actualizado: `void(unsigned int fd)`.
- Se añade el hook manual de devpts para el etiquetado de terminales.
- El registro de sucompat manual incluye el ejecutable; no registra los
  argumentos completos. Evita interpretar `struct user_arg_ptr` como un
  array de punteros de kernel, que era lo que hacía el código importado.
- Se usa `kvcalloc` nativo, ya retroportado en este árbol y con comprobación
  de desbordamiento. Se corrigen inclusiones y precedencia de headers.
- Se conserva el acceso mediante `flex_array` que realmente usa SELinux en
  este árbol 4.14. No se copia el cambio genérico de legacy que lo sustituye
  por acceso directo a un array basándose solo en el número de versión.
- El Makefile de KSU comprueba los backports que ya están versionados y falla
  si faltan. Se eliminan sus escrituras automáticas mediante `sed -i`.
- Kbuild genera los headers privados de SELinux antes de la compilación
  paralela o parcial de KSU. Se corrige también el parseo de sus comprobaciones
  de helpers, que impedía iniciar la compilación.
- Se mantiene la integración manual de init.rc. El nuevo preinit runner y su
  helper de compilación se omiten de esta variante; no deben activarse por
  la mera presencia de headers generados en un directorio de salida.

## Gestor y versiones

El driver anuncia código **33315**, UAPI **5** y la etiqueta propia
`v3.4.0-legacy-a16-susfs2.3`. La etiqueta identifica una integración legacy
adaptada; no afirma que exista una release oficial v3.4.2 para este kernel.

Se contrastó con las fuentes públicas del gestor **KernelSU Next v3.4.2**:
exige al menos 33188 y utiliza UAPI 5. Los campos de las 23 estructuras y
los números de las 20 órdenes ioctl compartidas del encabezado supercall
coinciden textualmente. Es una comprobación del contrato de fuentes, no una
prueba del gestor en ejecución ni una validación completa de ABI compilada.

El helper de usuarios `ksu_susfs` debe corresponder a SUSFS 2.3.0/non-GKI.
El módulo Android que lo distribuye puede tener una numeración diferente;
su nombre o versión no acredita por sí solo compatibilidad. No se ha
instalado, ejecutado o actualizado un módulo Android o APK en esta fase.

## Verificación realizada

Desde la raíz de este repositorio:

```text
python3 tools/guacamoleb/verify_integration.py --self-test
python3 tools/guacamoleb/check_c_contracts.py
python3 tools/guacamoleb/test_susfs_strings.py
git diff --no-ext-diff --no-textconv --check 943be052999e4d65f805f8c6a5f22b44ad832683
```

Pasan **24 comprobaciones estáticas y 18 regresiones negativas**. Comprueban
la inclusión del driver, selección de hooks, firmas de las interfaces,
fuentes de objetos, backports, layout SELinux y preservación del alcance.
Las regresiones introducen en memoria errores como desactivar KSU, cambiar la
firma de módulos, restaurar un hook antiguo o tocar el DTS, y exigen detectarlos.
El helper es de lectura: no ejecuta Kbuild ni código del kernel ni usa red.

Se añaden **8 sondas C de solo sintaxis para AArch64**, con declaraciones
extraídas del árbol y datos sintéticos. Contrastan callbacks, firmas de hooks
y layout de `user_arg_ptr`; tres casos deben fallar por el diagnóstico previsto.
No ejecutan Kbuild ni código del kernel. El helper puro de validación de
cadenas se prueba por separado con 22 casos sintéticos de límites y ASan/UBSan
en el anfitrión; LeakSanitizer está desactivado por la restricción ptrace del
sandbox y ese helper no realiza reservas de heap.

La [revisión completa](REVIEW.md) documenta los errores detectados después de
la primera publicación y sus correcciones. El [plan de Kbuild](BUILD_CHECK_PLAN.md)
delimita la comprobación aislada autorizada y realizada.

Kconfig conserva los ajustes solicitados de KSU/SUSFS. La configuración
resuelta coincide semánticamente con la extraída del boot Android 16 de agosto
(opciones ausentes tratadas como desactivadas). La compilación completa pasa,
con cuatro avisos heredados de secciones en el código OPlus de inicialización.
Los CRC de los cinco módulos generados coinciden con sus exportaciones;
esto no valida los módulos que lleva instalada la ROM ni el arranque.

## Pendiente antes de producir una imagen

1. Repetir la compilación de publicación con el toolchain Android adecuado.
   El árbol Android 16 común consultado selecciona Clang `r574158`; no se ha
   descargado ni ejecutado ese toolchain durante esta integración.
2. Contrastar los módulos de la ROM concreta con el candidato. La base
   conserva un bypass de CRC para `wlan`
   cuando KSU está activo; ese bypass no demuestra que el módulo sea compatible.
3. Obtener y contrastar los módulos y el boot original de la ROM exacta.
   Preparar un candidato con su ramdisk Android 16 y componentes coherentes,
   conservar hashes y revisar el resultado offline.
4. Plantear por separado cualquier prueba en hardware. No hay comandos de
   instalación o flash en este documento.

Se ejecutaron las comprobaciones locales y, tras autorización específica,
Kbuild y sus auxiliares en aislamiento sin red, con fuentes en solo lectura
y menos de 1 GiB de salida frente al límite de 8 GiB. No se ejecutaron setup
scripts o binarios Android; no se instalaron dependencias, extrajeron OTA,
montaron imágenes ni accedió al teléfono.
