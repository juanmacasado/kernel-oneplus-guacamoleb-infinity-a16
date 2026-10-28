# Actualizaciones posteriores de Harish para Infinity X Android 16

Revisión del 28 de octubre de 2026. El usuario aclaró que desea buscar e
incorporar actualizaciones posteriores de Harish, sin detenerse en junio.

## Procedencia

Base Android 16: `943be052999e4d65f805f8c6a5f22b44ad832683`, rama `16-c`,
fecha de committer 27 de junio de 2026. Ninguna de las ramas Android 16
consultadas supera esa fecha. No confundir las fechas originales de autor
de los backports con la fecha de integración de Harish.

Se fusiona la rama `17-c` de
[Codecity001/android_kernel_oneplus_sm8150](https://github.com/Codecity001/android_kernel_oneplus_sm8150),
fijada en `b1d34c4a99eaed5531333781ec8f389c53b9bad9` (24 de octubre de 2026).
Ancestro común: `6ecfabed032b68a8f0a0fd003cf5fbfb6d672acb`.
El historial diverge en 832/1037 commits; excluyendo equivalentes por parche
quedan 39/244. Se conserva la ascendencia de ambas ramas mediante un merge,
incluidas las correcciones específicas de la base A16.

Se incorporan correcciones de red y skb/zerocopy, WLAN/GTK y firmware legacy,
memoria/KFENCE, RNG, cámara, GPU, audio, suspensión, IRQ, herramientas de
compilación, syscalls clone3/checkpoint-restore y Baseband Guard. La versión
Linux continúa siendo 4.14.357; esto no es un salto a otra serie de Linux.

## Resoluciones para Android 16

- Se mantiene el driver KSU Next **3.4.2 legacy adaptado**, UAPI 5 y SUSFS 2.3.0
  ya probado, incluidos sus arreglos de memoria, SELinux y hooks manuales.
  No se recuperan los setup scripts, preinit ni hooks rotos del reimport de
  Harish. Se incorporan sus hooks manuales fstat para el tamaño de init.rc:
  sus implementaciones ya existen en nuestro driver.
- Se mantienen los seis nodos DT de fstab vendor y las correcciones A16 de
  pantalla/ULPS y operaciones PM emparejadas de IPA. Se incorporan consola
  ramoops, ECC desactivado y correcciones de rutas de audio.
- Se aplaza **56cf6b817bde**, traslado de propiedades OEM de power_supply a
  oplus_chg: elimina la interfaz que espera la ROM A16. Se conservan las
  correcciones de RTC y reducción de logs, independientes de esa migración.
- Se mantienen FORTIFY, BPF sin privilegios desactivado, HZ=250, módulos sin
  firma forzada, sin LTO ni Shadow Call Stack. No se impone a los binarios
  vendor una ABI distinta. KFENCE, diagnósticos de suspensión/bloqueos,
  estadísticas DMA-BUF, EROFS y compresión LZO de pstore se incorporan.
- WLAN se prepara **integrado en Image**, para que las actualizaciones del
  controlador no queden únicamente en un .ko que la ROM nunca cargará.
  El código admite esta modalidad; necesita comprobarse en arranque temporal.
  La ROM conserva su insmod del módulo antiguo: debe fallar al encontrar el
  controlador ya registrado, sin impedir wlan0. No se modifica vendor.
- Baseband Guard se incorpora con bloqueo de boot/recovery desactivado.
  La caché de dispositivos lleva spinlock y comprobación de duplicados;
  el diagnóstico inicializa su buffer incluso si get_cmdline falla. La
  identificación de zram usa get_gendisk, sin abrir dispositivos desde un
  hook LSM. Su alcance depende de los dominios SELinux su/ksu/magisk y de
  una lista de particiones; no es una garantía general contra root malicioso.
- Se conserva la detección estructurada de ld: la expresión &&/|| de Harish
  puede devolver dos nombres para GNU gold. Se incorpora el arreglo addtree.
- El nuevo constructor de /proc/cmdline usa copia limitada y comprueba espacio
  antes de añadir force_normal_boot. Ambas opciones de migración de arranque
  permanecen desactivadas para A16. Pruebas sintéticas con ASan/UBSan cubren
  cuatro combinaciones y 255 longitudes por combinación; rechazan el append
  sin límites. SUSFS conserva su ruta de cmdline y su buffer estático.

## Validación del candidato

El commit compilado es `2e381f23e9cd70474f3a8b0e6d106e712e125359`.
Image, veinte DTB y cuatro módulos compilan en 305,7 s, con salida inferior a
1 GiB. WLAN está integrado y no se genera un .ko para instalar en vendor.
La configuración resuelta mantiene HZ=250 y las opciones A16 indicadas.
Los cuatro avisos modpost de manifest/initdata pertenecen al mismo código
OPlus de la base; las funciones se llaman durante su initcall.

El repacker pasa round trips idénticos y catorce rechazos de imágenes/DTB
malformados, firmados, desordenados o con fstab cambiado. Cada DTB antiguo
coincide byte a byte con exactamente un archivo de la compilación anterior.
Los veinte nuevos solo cambian console-size y ecc-size de ramoops; mantienen
identificadores, orden y fstab. Ramdisk y recovery DTBO se conservan exactos.

Se comprobó el candidato con fastboot boot expresamente autorizado, sin
escribir particiones. Completó Android, root, SELinux Enforcing, KSU 33355/UAPI 5,
SUSFS 2.3.0/diez funciones, KFENCE y Baseband Guard. WLAN integrado se asoció
a la red, carrier=1, operstate=up. La sonda GET_INFO temporal fue retirada.
Hay un aviso de enable_irq en el cargador: se reprodujo al volver al kernel
anterior, en la misma función, sin cambios en su fuente. No es una regresión
introducida por la fusión. El teléfono terminó con el boot anterior; boot_a
conserva su SHA-256 original. No se han realizado pruebas prolongadas ni una
validación completa de cámara, audio, telefonía, GPS o suspensión.

El artefacto se publica como prerelease experimental para el modelo y ROM
indicados. No se publica el ZIP local de PC como si fuese instalable desde
recovery. Véanse [build-result-harish.json](build-result-harish.json) y
[runtime-harish.json](runtime-harish.json).
