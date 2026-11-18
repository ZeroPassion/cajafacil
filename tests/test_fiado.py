import pytest
from src.db import consult, crear_tablas
from src.ventas import LineaVenta, registrar_venta
from src.fiado import registrar_abono, saldo_cliente, clientes_con_deuda


@pytest.fixture
def ruta(tmp_path):
    r = str(tmp_path / "prueba.db")
    crear_tablas(r)
    return r


@pytest.fixture
def arroz(ruta):
    """Producto con precio 7,500 centavos y stock de sobra."""
    return consult(
        ruta=ruta,
        consulta="""INSERT INTO productos (nombre, categoria, costo, precio, stock, stock_minimo)
                    VALUES ('Arroz', 'General', 5000, 7500, 100, 0)""",
    )


def nuevo_cliente(ruta, nombre="Juan"):
    return consult(
        ruta=ruta,
        consulta="INSERT INTO clientes (nombre) VALUES (?)",
        parametros=(nombre,),
    )


def fiar(ruta, arroz, cliente, cantidad):
    return registrar_venta(
        [LineaVenta(arroz, cantidad)], tipo_pago="f", cliente_id=cliente, ruta=ruta
    )


def contar_abonos(ruta):
    return consult(ruta=ruta, consulta="SELECT COUNT(*) FROM abonos")[0][0]


# ---------- saldo ----------
def test_cliente_sin_movimientos_tiene_saldo_cero(ruta):
    cliente = nuevo_cliente(ruta)
    assert saldo_cliente(cliente, ruta=ruta) == 0


def test_una_venta_a_fiado_aumenta_el_saldo(ruta, arroz):
    cliente = nuevo_cliente(ruta)
    fiar(ruta, arroz, cliente, 3)
    assert saldo_cliente(cliente, ruta=ruta) == 22500


def test_varias_ventas_a_fiado_se_acumulan(ruta, arroz):
    cliente = nuevo_cliente(ruta)
    fiar(ruta, arroz, cliente, 1)
    fiar(ruta, arroz, cliente, 2)
    assert saldo_cliente(cliente, ruta=ruta) == 3 * 7500


def test_una_venta_de_contado_no_cuenta_como_deuda(ruta, arroz):
    cliente = nuevo_cliente(ruta)
    registrar_venta(
        [LineaVenta(arroz, 2)], tipo_pago="c", cliente_id=cliente, ruta=ruta
    )
    assert saldo_cliente(cliente, ruta=ruta) == 0


def test_el_saldo_de_un_cliente_inexistente_falla(ruta):
    with pytest.raises(ValueError, match="cliente"):
        saldo_cliente(999, ruta=ruta)


# ---------- abonos ----------
def test_un_abono_reduce_el_saldo(ruta, arroz):
    cliente = nuevo_cliente(ruta)
    fiar(ruta, arroz, cliente, 3)  # debe 22,500
    registrar_abono(cliente, 10000, ruta=ruta)
    assert saldo_cliente(cliente, ruta=ruta) == 12500


def test_abonar_el_saldo_completo_lo_deja_en_cero(ruta, arroz):
    cliente = nuevo_cliente(ruta)
    fiar(ruta, arroz, cliente, 2)  # debe 15,000
    registrar_abono(cliente, 15000, ruta=ruta)
    assert saldo_cliente(cliente, ruta=ruta) == 0


def test_el_abono_devuelve_su_id_y_guarda_la_nota(ruta, arroz):
    cliente = nuevo_cliente(ruta)
    fiar(ruta, arroz, cliente, 1)
    abono_id = registrar_abono(cliente, 1000, nota="Pago parcial", ruta=ruta)
    fila = consult(
        ruta=ruta,
        consulta="SELECT cliente_id, monto, nota FROM abonos WHERE id = ?",
        parametros=(abono_id,),
    )[0]
    assert fila == (cliente, 1000, "Pago parcial")


def test_un_abono_mayor_al_saldo_falla_y_no_se_guarda(ruta, arroz):
    cliente = nuevo_cliente(ruta)
    fiar(ruta, arroz, cliente, 1)  # debe 7,500
    with pytest.raises(ValueError, match="saldo"):
        registrar_abono(cliente, 7501, ruta=ruta)
    assert contar_abonos(ruta) == 0
    assert saldo_cliente(cliente, ruta=ruta) == 7500


def test_abonar_a_alguien_sin_deuda_falla(ruta):
    cliente = nuevo_cliente(ruta)
    with pytest.raises(ValueError, match="saldo"):
        registrar_abono(cliente, 100, ruta=ruta)
    assert contar_abonos(ruta) == 0


@pytest.mark.parametrize("monto", [0, -100])
def test_un_monto_invalido_falla(ruta, arroz, monto):
    cliente = nuevo_cliente(ruta)
    fiar(ruta, arroz, cliente, 1)
    with pytest.raises(ValueError, match="mayor a 0"):
        registrar_abono(cliente, monto, ruta=ruta)
    assert contar_abonos(ruta) == 0


def test_abonar_a_un_cliente_inexistente_falla(ruta):
    with pytest.raises(ValueError, match="cliente"):
        registrar_abono(999, 100, ruta=ruta)


# ---------- clientes con deuda ----------
def test_clientes_con_deuda_solo_lista_saldos_positivos_de_mayor_a_menor(ruta, arroz):
    ana = nuevo_cliente(ruta, "Ana")  # debe 7,500
    luis = nuevo_cliente(ruta, "Luis")  # debe 22,500
    pago = nuevo_cliente(ruta, "Pedro")  # ya pagó todo
    nuevo_cliente(ruta, "Sin deuda")  # nunca fió

    fiar(ruta, arroz, ana, 1)
    fiar(ruta, arroz, luis, 3)
    fiar(ruta, arroz, pago, 2)
    registrar_abono(pago, 15000, ruta=ruta)

    assert clientes_con_deuda(ruta=ruta) == [(luis, "Luis", 22500), (ana, "Ana", 7500)]


def test_clientes_con_deuda_vacio_si_nadie_debe(ruta):
    nuevo_cliente(ruta)
    assert clientes_con_deuda(ruta=ruta) == []
