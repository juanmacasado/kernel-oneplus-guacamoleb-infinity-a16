# Infinity X Android 16: KernelSU Next 3.4.2 legacy + SUSFS

Rama de desarrollo para **OnePlus 7 (`guacamoleb`) con Infinity X 3.12 Vanilla
Android 16**, preparada el 28 de octubre de 2026.

El código integra **KernelSU Next 3.4.2 legacy**, SUSFS **2.3.0** y las
actualizaciones posteriores de Harish hasta `17-c` del 24 de octubre de 2026,
adaptadas a la ROM Android 16. Se fusionó el historial completo; las excepciones
de ABI y arranque están en [HARISH_UPDATES.md](HARISH_UPDATES.md).

El kernel `2e381f23e9cd` compila Image, 20 DTB y cuatro módulos; WLAN va
integrado. Tras la prueba temporal se instaló en **boot_a** por petición del
usuario y pasó dos arranques desde la partición instalada: Android completo,
root, SELinux Enforcing, driver 33355/UAPI 5, gestor 3.4.2, SUSFS y WLAN.
También pasaron tres ciclos de pantalla y cuatro pings al router sin pérdidas.

Se mantiene como experimental: el contador de suspensión profunda siguió en
cero, y faltan pruebas prolongadas y de hardware. El aviso de IRQ del cargador
se reproduce también con el kernel anterior. El usuario confirmó cámara, audio y GPS
funcionando. Estado y límites: [prueba persistente](PERSISTENT_TEST.md) y
[lecturas resumidas](runtime-harish-persistent.json).

La versión anterior `8bb17398cadd` se conserva como recuperación local. Su
historial está en [VERSION_3_4_2.md](VERSION_3_4_2.md). Evidencia anterior:
[compilación](build-result-harish.json) y [arranque temporal](runtime-harish.json).

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
- Release 3.4.2: delta oficial revisado hasta
  `4c706b5938665866ebe16944a481a7b91e3396af`, con los cambios aplicables
  portados y el backend manual 4.14 conservado.

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
Android 17. El candidato sustituye solo el kernel del backup Android 16.

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

El driver responde código **33355**, UAPI **5** y etiqueta propia
`v3.4.2-legacy-a16-susfs2.3`. Se verificó mediante GET_INFO/GET_VERSION_TAG
después de reiniciar. Identifica el port legacy descrito en su informe; no
afirma equivalencia completa con el backend GKI oficial.

Se contrastó con las fuentes públicas del gestor **KernelSU Next v3.4.2**:
exige al menos 33188 y utiliza UAPI 5. Los campos de las 23 estructuras y
los números de las 20 órdenes ioctl compartidas del encabezado supercall
coinciden textualmente. El APK instalado figura como v3.4.2/33355, con firma
criptográfica contrastada contra el certificado anterior. Las lecturas de
runtime no sustituyen una validación completa de todas las funciones del gestor.

El helper de usuarios `ksu_susfs` debe corresponder a SUSFS 2.3.0/non-GKI.
El módulo Android que lo distribuye puede tener una numeración diferente;
su nombre o versión no acredita por sí solo compatibilidad. Se compiló e
instaló el helper universal desde fuentes fijadas de sidex15; sus consultas
devuelven v2.3.0 y diez funciones habilitadas, ambas con código 0. No se han
configurado nuevas reglas automáticas de ocultación.

## Verificación realizada

Desde la raíz de este repositorio:

```text
python3 tools/guacamoleb/verify_integration.py --self-test
python3 tools/guacamoleb/check_c_contracts.py
python3 tools/guacamoleb/test_susfs_strings.py
python3 tools/guacamoleb/test_342_forced_features.py
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
El parser de features forzadas pasa 14 casos con ASan/UBSan; la regresión que
restaura el avance incorrecto tras NUL debe producir heap-buffer-overflow.

La [revisión completa](REVIEW.md) documenta los errores detectados después de
la primera publicación y sus correcciones. El [plan de Kbuild](BUILD_CHECK_PLAN.md)
delimita la comprobación aislada autorizada y realizada.

Kconfig conserva los ajustes solicitados de KSU/SUSFS. La configuración
resuelta coincide semánticamente con la extraída del boot Android 16 de agosto
(opciones ausentes tratadas como desactivadas). La compilación completa pasa,
con cuatro avisos heredados de secciones en el código OPlus de inicialización.
Los CRC de los cinco módulos generados y los 394 del WLAN instalado coinciden
con las exportaciones. El arranque y el enlace Wi-Fi se comprobaron en el
teléfono; no se ha medido estabilidad prolongada ni todo el hardware.

## Validación que permanece pendiente

1. Repetir la compilación de publicación con el toolchain Android adecuado.
   El árbol Android 16 común consultado selecciona Clang `r574158`; no se ha
   descargado ni ejecutado ese toolchain durante esta integración.
2. Completar la comprobación de módulos y funcionamiento. Los 394 CRC del
   WLAN instalado ya coinciden con el candidato. La base
   conserva un bypass de CRC para `wlan`
   cuando KSU está activo; ese bypass no demuestra que el módulo sea compatible.
3. Comprobar llamadas, cámara, suspensión, consumo y estabilidad prolongada.
4. Comprobar las funciones de ocultación y los módulos Android concretos
   que se quieran utilizar. No se infiere su eficacia de la lista de features.

Se ejecutaron las comprobaciones locales y, tras autorización específica,
Kbuild y sus auxiliares en aislamiento sin red, con fuentes en solo lectura
y menos de 1 GiB de salida frente al límite de 8 GiB. Posteriormente el usuario
autorizó lecturas ADB, la copia de boot_a y el empaquetado local. No se ejecutaron
setup scripts, instalaron dependencias, extrajeron OTA ni montaron imágenes.
El usuario pidió después el flasheo y la actualización de ambos componentes:
se probó primero el arranque temporal y luego se escribió únicamente boot_a,
con backup y comprobación del hash leído tras reiniciar. Se actualizó el APK
conservando sus datos y se instaló el helper SUSFS solicitado.
