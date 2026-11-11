import pytest
from src.db import consult, crear_tablas
from src.ventas import LineaVenta, registrar_venta


@pytest.fixture
def ruta(tmp_path):
    r = str(tmp_path / "prueba.db")
    crear_tablas(r)
    return r


# ---------- ayudas (insertan con SQL directo para no depender de otros módulos) ----------
def nuevo_producto(ruta, nombre="Arroz", costo=5000, precio=7500, stock=10, activo=1):
    return consult(
        ruta=ruta,
        consulta="""INSERT INTO productos (nombre, categoria, costo, precio, stock, stock_minimo, activo)
                    VALUES (?, 'General', ?, ?, ?, 0, ?)""",
        parametros=(nombre, costo, precio, stock, activo),
    )


def nuevo_cliente(ruta, nombre="Juan"):
    return consult(
        ruta=ruta,
        consulta="INSERT INTO clientes (nombre) VALUES (?)",
        parametros=(nombre,),
    )


def stock(ruta, producto_id):
    return consult(
        ruta=ruta,
        consulta="SELECT stock FROM productos WHERE id = ?",
        parametros=(producto_id,),
    )[0][0]


def contar(ruta, tabla):
    return consult(ruta=ruta, consulta=f"SELECT COUNT(*) FROM {tabla}")[0][0]


# ---------- ventas válidas ----------
def test_venta_de_contado_baja_el_stock_y_crea_todos_los_registros(ruta):
    arroz = nuevo_producto(ruta)
    venta_id = registrar_venta([LineaVenta(arroz, 3)], ruta=ruta)

    assert stock(ruta, arroz) == 7
    venta = consult(
        ruta=ruta,
        consulta="SELECT tipo_pago, total, cliente_id FROM ventas WHERE id = ?",
        parametros=(venta_id,),
    )[0]
    assert venta == ("c", 22500, None)
    detalle = consult(
        ruta=ruta,
        consulta="SELECT cantidad, precio_unitario, costo_unitario FROM detalle_venta",
    )
    assert detalle == [(3, 7500, 5000)]
    mov = consult(
        ruta=ruta,
        consulta="SELECT tipo, cantidad, costo_unitario FROM movimientos_inventario",
    )
    assert mov == [("s", 3, 5000)]


def test_el_total_suma_todas_las_lineas(ruta):
    arroz = nuevo_producto(ruta, "Arroz", precio=7500)
    habichuelas = nuevo_producto(ruta, "Habichuelas", costo=4000, precio=6000)
    venta_id = registrar_venta(
        [LineaVenta(arroz, 2), LineaVenta(habichuelas, 3)], ruta=ruta
    )
    total = consult(
        ruta=ruta,
        consulta="SELECT total FROM ventas WHERE id = ?",
        parametros=(venta_id,),
    )[0][0]
    assert total == 2 * 7500 + 3 * 6000


def test_venta_a_fiado_guarda_cliente_y_tipo(ruta):
    arroz = nuevo_producto(ruta)
    cliente = nuevo_cliente(ruta)
    venta_id = registrar_venta(
        [LineaVenta(arroz, 1)], tipo_pago="f", cliente_id=cliente, ruta=ruta
    )
    fila = consult(
        ruta=ruta,
        consulta="SELECT tipo_pago, cliente_id FROM ventas WHERE id = ?",
        parametros=(venta_id,),
    )[0]
    assert fila == ("f", cliente)


def test_devuelve_el_id_de_cada_venta(ruta):
    arroz = nuevo_producto(ruta)
    assert registrar_venta([LineaVenta(arroz, 1)], ruta=ruta) == 1
    assert registrar_venta([LineaVenta(arroz, 1)], ruta=ruta) == 2


def test_vender_todo_el_stock_es_valido(ruta):
    arroz = nuevo_producto(ruta, stock=4)
    registrar_venta([LineaVenta(arroz, 4)], ruta=ruta)
    assert stock(ruta, arroz) == 0


def test_cambiar_el_precio_despues_no_altera_la_venta_anterior(ruta):
    arroz = nuevo_producto(ruta, precio=7500)
    venta_id = registrar_venta([LineaVenta(arroz, 2)], ruta=ruta)
    consult(
        ruta=ruta,
        consulta="UPDATE productos SET precio = 9999, costo = 8888 WHERE id = ?",
        parametros=(arroz,),
    )
    detalle = consult(
        ruta=ruta, consulta="SELECT precio_unitario, costo_unitario FROM detalle_venta"
    )
    total = consult(
        ruta=ruta,
        consulta="SELECT total FROM ventas WHERE id = ?",
        parametros=(venta_id,),
    )[0][0]
    assert detalle == [(7500, 5000)]
    assert total == 15000


# ---------- datos inválidos: no debe quedar nada guardado ----------
def assert_nada_guardado(ruta, producto_id, stock_esperado):
    assert stock(ruta, producto_id) == stock_esperado
    for tabla in ("ventas", "detalle_venta", "movimientos_inventario"):
        assert contar(ruta, tabla) == 0, f"quedaron filas en {tabla}"


def test_fiado_sin_cliente_falla(ruta):
    arroz = nuevo_producto(ruta)
    with pytest.raises(ValueError, match="cliente"):
        registrar_venta([LineaVenta(arroz, 1)], tipo_pago="f", ruta=ruta)
    assert_nada_guardado(ruta, arroz, 10)


def test_cliente_inexistente_falla(ruta):
    arroz = nuevo_producto(ruta)
    with pytest.raises(ValueError, match="cliente"):
        registrar_venta(
            [LineaVenta(arroz, 1)], tipo_pago="f", cliente_id=999, ruta=ruta
        )
    assert_nada_guardado(ruta, arroz, 10)


def test_lista_de_lineas_vacia_falla(ruta):
    with pytest.raises(ValueError):
        registrar_venta([], ruta=ruta)
    assert contar(ruta, "ventas") == 0


def test_tipo_de_pago_invalido_falla(ruta):
    arroz = nuevo_producto(ruta)
    with pytest.raises(ValueError, match="pago"):
        registrar_venta([LineaVenta(arroz, 1)], tipo_pago="x", ruta=ruta)
    assert_nada_guardado(ruta, arroz, 10)


@pytest.mark.parametrize("cantidad", [0, -1])
def test_cantidad_invalida_falla(ruta, cantidad):
    arroz = nuevo_producto(ruta)
    with pytest.raises(ValueError, match="cantidad"):
        registrar_venta([LineaVenta(arroz, cantidad)], ruta=ruta)
    assert_nada_guardado(ruta, arroz, 10)


def test_producto_inexistente_falla(ruta):
    with pytest.raises(ValueError, match="no existe"):
        registrar_venta([LineaVenta(999, 1)], ruta=ruta)
    assert contar(ruta, "ventas") == 0


def test_producto_desactivado_no_se_puede_vender(ruta):
    viejo = nuevo_producto(ruta, activo=0)
    with pytest.raises(ValueError, match="desactivado"):
        registrar_venta([LineaVenta(viejo, 1)], ruta=ruta)
    assert_nada_guardado(ruta, viejo, 10)


def test_stock_insuficiente_falla(ruta):
    arroz = nuevo_producto(ruta, stock=2)
    with pytest.raises(ValueError, match="Stock insuficiente"):
        registrar_venta([LineaVenta(arroz, 3)], ruta=ruta)
    assert_nada_guardado(ruta, arroz, 2)


# ---------- la prueba estrella: la transacción ----------
def test_si_una_linea_falla_se_cancela_toda_la_venta(ruta):
    """La 1ra línea es válida y la 2da no tiene stock: no debe quedar NADA, ni la 1ra."""
    arroz = nuevo_producto(ruta, "Arroz", stock=10)
    habichuelas = nuevo_producto(ruta, "Habichuelas", stock=1)
    with pytest.raises(ValueError, match="Habichuelas"):
        registrar_venta([LineaVenta(arroz, 2), LineaVenta(habichuelas, 5)], ruta=ruta)

    assert stock(ruta, arroz) == 10
    assert stock(ruta, habichuelas) == 1
    for tabla in ("ventas", "detalle_venta", "movimientos_inventario"):
        assert contar(ruta, tabla) == 0, f"quedaron filas en {tabla}"


def test_el_mismo_producto_en_dos_lineas_respeta_el_stock_total(ruta):
    arroz = nuevo_producto(ruta, stock=5)
    with pytest.raises(ValueError, match="Stock insuficiente"):
        registrar_venta([LineaVenta(arroz, 3), LineaVenta(arroz, 3)], ruta=ruta)
    assert_nada_guardado(ruta, arroz, 5)
