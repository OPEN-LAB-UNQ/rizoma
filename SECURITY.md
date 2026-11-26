# Seguridad de Rizoma

## Cómo reportar una vulnerabilidad

Escribí en privado a <maximilianoperez1981@gmail.com> con el asunto «Seguridad · Rizoma», indicando la versión, el componente, el impacto y los pasos para reproducirla con perfiles ficticios. También se puede usar «Report a vulnerability» (Security Advisory privado) en el repositorio, si está habilitado.

No envíes credenciales ni datos personales, y no publiques detalles de una falla abierta en *issues* o *pull requests*. Solo la última versión publicada recibe correcciones de seguridad.

## Cuidados para quien instala

- `SECRET_KEY` debe ser propia y tener al menos 32 caracteres: `python -c "import secrets; print(secrets.token_urlsafe(48))"`.
- La API escucha en `127.0.0.1` y se publica con HTTPS detrás de un servidor web que envíe `X-Forwarded-For`, para que los límites de intentos se apliquen a cada visitante.
- Las sesiones duran como máximo 12 horas, en una cookie `Secure`, `HttpOnly` y `SameSite=Lax`. Salir revoca las sesiones de la cuenta.
- El registro público crea siempre cuentas de participante. Los roles de docente u organización y la institución los asigna la administración con `PUT /api/admin/security/users/{id}/authorization` (`role`, `institution` y `evidence`), y queda registro. Solo el personal habilitado valida participaciones.
- `POST /api/admin/security/users/{id}/revoke-sessions` revoca las sesiones de una cuenta.
- Los ingresos y registros tienen límite de intentos (10 por cuenta y 30 por dirección cada 15 minutos), guardado sin direcciones ni correos en claro.
- Los currículums admiten hasta 2,5 MB comprimidos y 20 MB de contenido descomprimido.
- La política de seguridad de contenido admite los scripts propios y no reemplaza el escape del contenido.

## Al actualizar desde 2.2

Aplicar `sql/2026_11_26_autorizacion_institucional.sql` antes de reiniciar. Las sesiones anteriores dejan de valer. Las cuentas de docente u organización y las credenciales verificadas con versiones anteriores quedan pendientes hasta que la administración las revise.
