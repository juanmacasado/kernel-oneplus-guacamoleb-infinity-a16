# Kernel Harish instalado: comprobación inicial

El 28 de octubre de 2026, por petición explícita del usuario, se flasheó
`boot_a` del OnePlus 7 GM1901 con Infinity X 3.12 Vanilla Android 16.
El boot instalado coincide con la imagen publicada; SHA-256:
`1a13d1e5d0699b0619fd16afe7669cdf6d051fb02bb11883ef7f14aaf4be3042`.
Se conserva localmente la copia exacta del anterior (SHA-256
`0af449c667ad7d09679f4c3c306785bfd47eed0cb5a9bccf174f1045811e22d7`).
Esta operación solo escribió boot_a.

Pasaron dos arranques desde la partición instalada con Android completo,
root UID 0, SELinux Enforcing, KSU driver 33355/UAPI 5 y gestor 3.4.2,
SUSFS 2.3.0 con diez funciones y WLAN integrado conectado. Respondieron los
cuatro pings al router local, sin pérdidas. Pasaron tres ciclos de pantalla
apagada/encendida manteniendo boot ID, Android iniciado y WLAN conectado.
El servicio de cámara registra cuatro dispositivos; eso no demuestra que
la captura funcione.

El contador de suspensión profunda siguió en cero: no se ha validado reposo
profundo ni consumo nocturno con el teléfono conectado por USB. No se
registraron BUG/Oops/panic/lockup nuevos en los logs inspeccionados de estos
arranques. Sigue el aviso de IRQ 600 del cargador reproducido con el kernel
anterior. El usuario confirmó que funcionan cámara, audio y GPS; son pruebas manuales
del propietario, distintas de las lecturas por ADB. Después de esas pruebas
se comprobó el mismo boot ID, Android completo y WLAN conectado, sin nuevos
diagnósticos graves en el registro inspeccionado. Telefonía, todos los modos
de cámara/audio y estabilidad prolongada siguen sin validación.

La comprobación inicial es favorable, pero se mantiene la consideración de
versión experimental. El teléfono termina con el kernel nuevo instalado.
Los registros sin filtrar, con identificadores de dispositivo y red, permanecen
solo en el ordenador; el informe JSON omite esos identificadores.
