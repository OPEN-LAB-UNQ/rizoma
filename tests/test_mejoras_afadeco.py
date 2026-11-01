"""Mejoras traídas de Rizoma Afadeco: carga guiada sin CV y temas clasificados a la vista (sin base ni servicios externos)."""
from pathlib import Path
from types import SimpleNamespace

from routers.users import mis_temas

RAIZ = Path(__file__).resolve().parent.parent


class _Consulta:
    def __init__(self, filas):
        self.filas = filas

    def join(self, *a, **k):
        return self

    def filter(self, *a, **k):
        return self

    def all(self):
        return self.filas


class _Base:
    def __init__(self, filas):
        self.filas = filas

    def query(self, *a):
        return _Consulta(self.filas)


def test_mis_temas_agrupa_relaciones_y_ordena_por_clasificacion():
    datos = SimpleNamespace(id="t1", label="Análisis de datos", macro="Tecnología", subtema="Datos")
    turnos = SimpleNamespace(id="t2", label="Gestión de turnos", macro="Salud", subtema="Gestión")
    nuevo = SimpleNamespace(id="t3", label="Huerta urbana", macro=None, subtema=None)
    filas = [(SimpleNamespace(relation="wants"), datos), (SimpleNamespace(relation="interest"), datos),
             (SimpleNamespace(relation="offers"), turnos), (SimpleNamespace(relation="offers"), turnos),
             (SimpleNamespace(relation="interest"), nuevo)]
    salida = mis_temas(user=SimpleNamespace(id="u1"), db=_Base(filas))
    assert [t["tema"] for t in salida] == ["Gestión de turnos", "Análisis de datos", "Huerta urbana"]
    assert salida[1]["relaciones"] == ["Querés aprender", "Te interesa"]
    assert salida[0]["relaciones"] == ["Sabés"]          # sin repetidos
    assert salida[2]["macro"] == "" and salida[2]["subtema"] == ""


def test_pantalla_tiene_carga_guiada_en_voseo_y_temas_clasificados():
    html = (RAIZ / "static" / "index.html").read_text(encoding="utf-8")
    js = (RAIZ / "static" / "js" / "app.js").read_text(encoding="utf-8")
    for texto in ("¿No tenés el CV a mano?", "¿Qué sabés hacer?", "¿Qué querés aprender?", "¿Qué te interesa?",
                  'id="misTemasLista"', "Así quedaron clasificados tus temas"):
        assert texto in html
    assert "JEL" not in html
    assert "/api/users/me/temas" in js and "function guardarCargaGuiada" in js
