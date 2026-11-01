"""El filtro de direcciones borra domicilios, no la trayectoria («dirección de tesis»)."""
from services.privacy_service import ADDRESS_RE


def filtrar(texto):
    return ADDRESS_RE.sub("[direccion]", texto)


def test_borra_domicilios_con_numero():
    assert filtrar("Vivo en Calle 45 # 12-30, Bogotá") == "Vivo en [direccion], Bogotá"
    assert filtrar("Carrera 7 No. 40-62, Bogotá") == "[direccion], Bogotá"
    assert filtrar("Domicilio: Av. Siempreviva 742, Springfield") == "Domicilio: [direccion], Springfield"


def test_no_toca_la_trayectoria():
    for texto in ("Dirección de semilleros de investigación. Coordino trabajos de grado",
                  "Dirección de tesis de maestría en economía, 2019"):
        assert filtrar(texto) == texto


def test_no_se_come_la_frase_siguiente():
    assert filtrar("Calle 45. Quiero aprender econometría") == "[direccion]. Quiero aprender econometría"
