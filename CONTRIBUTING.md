# Cómo contribuir

Gracias por tu interés en Rizoma. Estas pautas buscan que cada cambio mantenga lo que la herramienta promete: las sugerencias son hipótesis para conversar, cada persona decide qué se ve de ella y el orden lo calcula el grafo, no un modelo de lenguaje.

## Informar un fallo

Abrí un *issue* con:

- qué hiciste, qué esperabas y qué pasó;
- la versión que estás usando;
- si es posible, los pasos para reproducirlo con **perfiles ficticios**. Nunca subas currículums, datos de personas reales, claves ni capturas de una instalación en uso.

**Las vulnerabilidades no se informan en un issue.** Seguí el procedimiento privado de [SECURITY.md](SECURITY.md).

## Proponer un cambio

1. Hacé un *fork* y una rama con un nombre descriptivo.
2. Instalá las dependencias de desarrollo: `pip install -r requirements-dev.txt`.
3. Agregá una prueba que reproduzca el problema o que describa el comportamiento nuevo.
4. Corré la suite con una base **temporal**, nunca la de una instalación en uso: `python -m pytest -q tests`. Las pruebas que recrean tablas exigen que el nombre de la base contenga `rizoma_security_test_`.
5. Si cambiás la base, agregá un archivo en `sql/` con la fecha en el nombre.
6. Abrí un *pull request* explicando qué cambia, por qué y cómo lo verificaste.

## Reglas que no se negocian

- Ningún dato identificatorio se envía a un modelo sin la copia seudonimizada que la persona puede revisar.
- Nadie obtiene un rol institucional ni emite una credencial verificada sin habilitación de la administración.
- Toda ruta nueva verifica la sesión y respeta la visibilidad que eligió cada persona.
- Si cambiás el aviso de privacidad, subí su versión.
- No se quitan ni se aflojan pruebas para que la suite pase.

## Estilo

- Nombres, comentarios y mensajes en español, en lenguaje llano.
- Cambios pequeños y fáciles de revisar.

## Conducta

La participación en el proyecto se rige por el [código de conducta](CODE_OF_CONDUCT.md).
