import pytest
from src.db import consult, crear_tablas
from src.gastos import registrar_gasto, listar_gastos, gastos_por_categoria

OCTUBRE = ("2026-10-01", "2026-11-01")


@pytest.fixture
def ruta(tmp_path):
    r = str(tmp_path / "prueba.db")
    crear_tablas(r)
    return r


def contar(ruta):
    return consult(ruta=ruta, consulta="SELECT COUNT(*) FROM gastos")[0][0]


# ---------- registrar ----------
def test_registrar_y_listar_un_gasto(ruta):
    gasto_id = registrar_gasto("luz", 2000, "Factura octubre", fecha="2026-10-15 09:30:00", ruta=ruta)
    assert gasto_id == 1
    assert listar_gastos(*OCTUBRE, ruta=ruta) == [(1, "2026-10-15 09:30:00", "luz", "Factura octubre", 2000)]


def test_sin_fecha_usa_la_fecha_de_ahora(ruta):
    registrar_gasto("otros", 500, ruta=ruta)
    assert len(listar_gastos("2000-01-01", "2999-01-01", ruta=ruta)) == 1


def test_una_fecha_solo_con_dia_se_normaliza(ruta):
    registrar_gasto("agua", 800, fecha="2026-10-15", ruta=ruta)
    assert listar_gastos(*OCTUBRE, ruta=ruta)[0][1] == "2026-10-15 00:00:00"


@pytest.mark.parametrize("monto", [0, -5])
def test_monto_invalido_falla_y_no_guarda(ruta, monto):
    with pytest.raises(ValueError, match="mayor a 0"):
        registrar_gasto("luz", monto, ruta=ruta)
    assert contar(ruta) == 0


@pytest.mark.parametrize("categoria", ["", "inventada", "Luz"])
def test_categoria_invalida_falla_y_no_guarda(ruta, categoria):
    with pytest.raises(ValueError, match="Categoría inválida"):
        registrar_gasto(categoria, 100, ruta=ruta)
    assert contar(ruta) == 0


def test_fecha_invalida_falla_y_no_guarda(ruta):
    with pytest.raises(ValueError, match="Fecha inválida"):
        registrar_gasto("luz", 100, fecha="ayer", ruta=ruta)
    assert contar(ruta) == 0


# ---------- rangos de fechas ----------
def test_el_rango_incluye_el_inicio_y_excluye_el_fin(ruta):
    registrar_gasto("luz", 1, fecha="2026-09-30 23:59:59", ruta=ruta)    # antes: fuera
    registrar_gasto("luz", 2, fecha="2026-10-01 00:00:00", ruta=ruta)    # inicio exacto: dentro
    registrar_gasto("luz", 3, fecha="2026-10-31 18:00:00", ruta=ruta)    # último día con hora: dentro
    registrar_gasto("luz", 4, fecha="2026-11-01 00:00:00", ruta=ruta)    # fin exacto: fuera
    montos = sorted(g[4] for g in listar_gastos(*OCTUBRE, ruta=ruta))
    assert montos == [2, 3]


def test_el_mas_reciente_aparece_primero(ruta):
    registrar_gasto("luz", 1, fecha="2026-10-05", ruta=ruta)
    registrar_gasto("luz", 2, fecha="2026-10-20", ruta=ruta)
    registrar_gasto("luz", 3, fecha="2026-10-10", ruta=ruta)
    assert [g[4] for g in listar_gastos(*OCTUBRE, ruta=ruta)] == [2, 3, 1]


def test_un_rango_invertido_falla(ruta):
    with pytest.raises(ValueError, match="Rango"):
        listar_gastos("2026-11-01", "2026-10-01", ruta=ruta)


# ---------- por categoría ----------
def test_gastos_por_categoria_agrupa_suma_y_ordena(ruta):
    registrar_gasto("luz", 2000, fecha="2026-10-03", ruta=ruta)
    registrar_gasto("luz", 1500, fecha="2026-10-20", ruta=ruta)
    registrar_gasto("alquiler", 10000, fecha="2026-10-01", ruta=ruta)
    registrar_gasto("transporte", 500, fecha="2026-10-15", ruta=ruta)
    registrar_gasto("luz", 9999, fecha="2026-09-15", ruta=ruta)          # fuera del rango
    assert gastos_por_categoria(*OCTUBRE, ruta=ruta) == [
        ("alquiler", 10000), ("luz", 3500), ("transporte", 500),
    ]


def test_gastos_por_categoria_vacio_si_no_hay_gastos(ruta):
    assert gastos_por_categoria(*OCTUBRE, ruta=ruta) == []


def test_el_fin_exacto_con_hora_tambien_se_excluye(ruta):
    """Con un rango dado con hora completa, el instante final tampoco entra."""
    registrar_gasto("luz", 1, fecha="2026-10-31 23:59:59", ruta=ruta)    # dentro
    registrar_gasto("luz", 2, fecha="2026-11-01 00:00:00", ruta=ruta)    # justo en el fin: fuera
    gastos = listar_gastos("2026-10-01 00:00:00", "2026-11-01 00:00:00", ruta=ruta)
    assert [g[4] for g in gastos] == [1]