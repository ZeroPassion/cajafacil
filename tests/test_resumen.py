import pytest
from src.db import consult, crear_tablas
from src.ventas import LineaVenta, registrar_venta
from src.fiado import registrar_abono
from src.gastos import registrar_gasto
from src.resumen import resumen_periodo

TODO = ("2000-01-01", "2999-01-01")      # rango amplio: las ventas se registran con la fecha de hoy
OCTUBRE = ("2026-10-01", "2026-11-01")

CLAVES = ["ventas", "costo_ventas", "ganancia_bruta", "gastos", "ganancia_estimada",
          "cobrado", "por_cobrar", "mercancia_comprada", "productos_bajo_stock"]


@pytest.fixture
def ruta(tmp_path):
    r = str(tmp_path / "prueba.db")
    crear_tablas(r)
    return r


# ---------- ayudas ----------
def nuevo_producto(ruta, nombre="Arroz", costo=5000, precio=7500, stock=100, minimo=0, activo=1):
    return consult(
        ruta=ruta,
        consulta="""INSERT INTO productos (nombre, categoria, costo, precio, stock, stock_minimo, activo)
                    VALUES (?, 'General', ?, ?, ?, ?, ?)""",
        parametros=(nombre, costo, precio, stock, minimo, activo),
    )


def nuevo_cliente(ruta, nombre="Juan"):
    return consult(ruta=ruta, consulta="INSERT INTO clientes (nombre) VALUES (?)", parametros=(nombre,))


def insertar_venta(ruta, fecha, tipo, producto, cantidad, precio, costo, cliente=None):
    """Inserta una venta con fecha controlada (registrar_venta siempre usa la fecha de hoy)."""
    venta_id = consult(
        ruta=ruta,
        consulta="INSERT INTO ventas (cliente_id, fecha, tipo_pago, total) VALUES (?, ?, ?, ?)",
        parametros=(cliente, fecha, tipo, cantidad * precio),
    )
    consult(
        ruta=ruta,
        consulta="""INSERT INTO detalle_venta (venta_id, producto_id, cantidad, precio_unitario, costo_unitario)
                    VALUES (?, ?, ?, ?, ?)""",
        parametros=(venta_id, producto, cantidad, precio, costo),
    )
    return venta_id


# ---------- escenario calculado a mano ----------
def test_escenario_completo(ruta):
    arroz = nuevo_producto(ruta, "Arroz", costo=5000, precio=7500, stock=100)
    nuevo_producto(ruta, "Sal", costo=100, precio=200, stock=1, minimo=2)               # bajo stock
    nuevo_producto(ruta, "Viejo", costo=100, precio=200, stock=0, minimo=5, activo=0)   # desactivado: no cuenta
    juan = nuevo_cliente(ruta)

    registrar_venta([LineaVenta(arroz, 2)], ruta=ruta)                                  # contado: 15,000 (costo 10,000)
    registrar_gasto("luz", 2000, ruta=ruta)
    registrar_venta([LineaVenta(arroz, 1)], tipo_pago="f", cliente_id=juan, ruta=ruta)  # fiado: 7,500 (costo 5,000)
    registrar_abono(juan, 2500, ruta=ruta)
    registrar_gasto("mercancia", 50000, ruta=ruta)                                      # compra: NO resta a la ganancia

    assert resumen_periodo(*TODO, ruta=ruta) == {
        "ventas": 22500,                # 15,000 + 7,500
        "costo_ventas": 15000,          # 3 x 5,000
        "ganancia_bruta": 7500,
        "gastos": 2000,                 # solo la luz
        "ganancia_estimada": 5500,      # 7,500 - 2,000
        "cobrado": 17500,               # 15,000 de contado + 2,500 de abono
        "por_cobrar": 5000,             # 7,500 fiados - 2,500 abonados
        "mercancia_comprada": 50000,
        "productos_bajo_stock": 1,      # solo Sal
    }


def test_la_mercancia_no_se_resta_dos_veces(ruta):
    arroz = nuevo_producto(ruta)
    registrar_venta([LineaVenta(arroz, 1)], ruta=ruta)      # ganancia bruta 2,500
    registrar_gasto("mercancia", 50000, ruta=ruta)
    resumen = resumen_periodo(*TODO, ruta=ruta)
    assert resumen["ganancia_estimada"] == 2500
    assert resumen["mercancia_comprada"] == 50000


def test_base_vacia_devuelve_todo_en_cero(ruta):
    assert resumen_periodo(*TODO, ruta=ruta) == {clave: 0 for clave in CLAVES}


# ---------- períodos ----------
def test_solo_cuenta_lo_que_cae_dentro_del_periodo(ruta):
    arroz = nuevo_producto(ruta)
    insertar_venta(ruta, "2026-09-30 23:59:59", "c", arroz, 1, 7500, 5000)    # antes: fuera
    insertar_venta(ruta, "2026-10-01 00:00:00", "c", arroz, 2, 7500, 5000)    # inicio exacto: dentro
    insertar_venta(ruta, "2026-10-31 23:59:59", "c", arroz, 1, 7500, 5000)    # último segundo: dentro
    insertar_venta(ruta, "2026-11-01 00:00:00", "c", arroz, 4, 7500, 5000)    # fin exacto: fuera
    registrar_gasto("luz", 1000, fecha="2026-10-10", ruta=ruta)
    registrar_gasto("luz", 9999, fecha="2026-09-10", ruta=ruta)               # fuera

    resumen = resumen_periodo(*OCTUBRE, ruta=ruta)
    assert resumen["ventas"] == 3 * 7500
    assert resumen["costo_ventas"] == 3 * 5000
    assert resumen["gastos"] == 1000
    assert resumen["ganancia_estimada"] == 3 * 2500 - 1000


def test_por_cobrar_no_depende_del_periodo(ruta):
    arroz = nuevo_producto(ruta)
    juan = nuevo_cliente(ruta)
    insertar_venta(ruta, "2026-09-15 10:00:00", "f", arroz, 1, 7500, 5000, cliente=juan)   # fiado de septiembre
    resumen = resumen_periodo(*OCTUBRE, ruta=ruta)
    assert resumen["ventas"] == 0           # no se vendió nada en octubre...
    assert resumen["por_cobrar"] == 7500    # ...pero la deuda sigue pendiente


def test_un_rango_invertido_falla(ruta):
    with pytest.raises(ValueError, match="Rango"):
        resumen_periodo("2026-11-01", "2026-10-01", ruta=ruta)


def test_el_fin_exacto_con_hora_tambien_se_excluye(ruta):
    """Con un rango dado con hora completa, la venta del instante final no cuenta."""
    arroz = nuevo_producto(ruta)
    insertar_venta(ruta, "2026-10-31 23:59:59", "c", arroz, 1, 7500, 5000)   # dentro
    insertar_venta(ruta, "2026-11-01 00:00:00", "c", arroz, 5, 7500, 5000)   # justo en el fin: fuera
    resumen = resumen_periodo("2026-10-01 00:00:00", "2026-11-01 00:00:00", ruta=ruta)
    assert resumen["ventas"] == 7500
    assert resumen["costo_ventas"] == 5000