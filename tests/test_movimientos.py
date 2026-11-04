import pytest
from src.db import consult, crear_tablas
from src.inventario import (
    DataProducto,
    DataMovimiento,
    crear_producto,
    registrar_entrada,
    registrar_salida,
    editar_producto,
)

FECHA = "2026-10-29 10:00:00"


@pytest.fixture
def ruta(tmp_path):
    r = str(tmp_path / "prueba.db")
    crear_tablas(r)
    return r


@pytest.fixture
def id_producto(ruta):
    """Producto con stock inicial de 10 unidades."""
    return crear_producto(
        ruta=ruta,
        producto=DataProducto(
            nombre="Arroz",
            categoria="Granos",
            costo=5000,
            precio=7500,
            stock_inicial=10,
            stock_minimo=2,
        ),
    )


def mov(tipo, cantidad, id_producto):
    return DataMovimiento(
        id_producto=id_producto,
        tipo=tipo,
        cantidad=cantidad,
        costo_unitario=5000,
        fecha=FECHA,
        nota="prueba",
    )


def stock(ruta, id_producto):
    return consult(
        ruta=ruta,
        consulta="SELECT stock FROM productos WHERE id = ?",
        parametros=(id_producto,),
    )[0][0]


def num_movimientos(ruta, id_producto):
    return consult(
        ruta=ruta,
        consulta="SELECT COUNT(*) FROM movimientos_inventario WHERE producto_id = ?",
        parametros=(id_producto,),
    )[0][0]


def valor(ruta, id_producto, columna):
    # 'columna' viene de las pruebas, nunca del usuario
    return consult(
        ruta=ruta,
        consulta=f"SELECT {columna} FROM productos WHERE id = ?",
        parametros=(id_producto,),
    )[0][0]


# ---------- Entradas ----------

# 1. TEST EXITOSO: Comprueba que el flujo correcto suma stock y guarda el registro
def test_entrada_sube_el_stock_y_registra_el_movimiento(ruta, id_producto):
    # Aquí NO va pytest.raises porque NO debe fallar
    registrar_entrada(mov("e", 5, id_producto), ruta=ruta)
    
    assert stock(ruta, id_producto) == 15  # 10 iniciales + 5 nuevos
    assert num_movimientos(ruta, id_producto) == 1

# 2. TEST DE FALLO: Comprueba que un producto falso lance la excepción controlada
def test_entrada_de_producto_inexistente_falla(ruta):
    id_falso = 99999
    
    # Aquí SÍ va pytest.raises porque esperas que registrar_entrada lance ValueError
    with pytest.raises(ValueError, match="El producto especificado no existe."):
        registrar_entrada(mov("e", 5, id_falso), ruta=ruta)



@pytest.mark.parametrize("cantidad", [0, -5])
def test_entrada_con_cantidad_invalida_falla(ruta, id_producto, cantidad):
    with pytest.raises(ValueError):
        registrar_entrada(mov("e", cantidad, id_producto), ruta=ruta)
    assert stock(ruta, id_producto) == 10
    assert num_movimientos(ruta, id_producto) == 0


def test_entrada_de_producto_inexistente_falla(ruta):
    with pytest.raises(ValueError):
        registrar_entrada(mov("e", 5, 999), ruta=ruta)


# ---------- Salidas ----------
def test_salida_baja_el_stock_y_registra_el_movimiento(ruta, id_producto):
    # Flujo exitoso: No lleva pytest.raises
    registrar_salida(mov("s", 3, id_producto), ruta=ruta)
    assert stock(ruta, id_producto) == 7  # 10 iniciales - 3 = 7
    assert num_movimientos(ruta, id_producto) == 1


def test_salida_mayor_al_stock_falla_y_no_cambia_nada(ruta, id_producto):
    with pytest.raises(ValueError):
        registrar_salida(mov("s", 11, id_producto), ruta=ruta)
    assert stock(ruta, id_producto) == 10
    assert num_movimientos(ruta, id_producto) == 0


def test_salida_que_deja_el_stock_en_cero_es_valida(ruta, id_producto):
    registrar_salida(mov("s", 10, id_producto), ruta=ruta)
    assert stock(ruta, id_producto) == 0


@pytest.mark.parametrize("cantidad", [0, -5])
def test_salida_con_cantidad_invalida_falla(ruta, id_producto, cantidad):
    # Flujo de error por cantidad: El assert de stock va FUERA del bloque context-manager
    with pytest.raises(ValueError, match="Cantidad invalida."):
        registrar_salida(mov("s", cantidad, id_producto), ruta=ruta)
    
    # Comprobar que el stock quedó intacto
    assert stock(ruta, id_producto) == 10


def test_salida_de_producto_inexistente_falla(ruta):
    id_falso = 99999
    with pytest.raises(ValueError, match="El producto especificado no existe."):
        registrar_salida(mov("s", 3, id_falso), ruta=ruta)


# ---------- Editar ----------
def test_editar_cambia_solo_lo_pedido(ruta, id_producto):
    editar_producto(id_producto, {"precio": 8000}, ruta=ruta)
    assert valor(ruta, id_producto, "precio") == 8000
    assert valor(ruta, id_producto, "nombre") == "Arroz"
    assert valor(ruta, id_producto, "costo") == 5000


def test_editar_puede_cambiar_varios_campos(ruta, id_producto):
    editar_producto(
        id_producto, {"nombre": "Arroz Selecto", "categoria": "Premium"}, ruta=ruta
    )
    assert valor(ruta, id_producto, "nombre") == "Arroz Selecto"
    assert valor(ruta, id_producto, "categoria") == "Premium"


@pytest.mark.parametrize("columna", ["stock", "id", "activo", "precio = 1, nombre"])
def test_editar_rechaza_columnas_no_permitidas(ruta, id_producto, columna):
    with pytest.raises(ValueError):
        editar_producto(id_producto, {columna: 1}, ruta=ruta)
    assert stock(ruta, id_producto) == 10


def test_editar_con_id_inexistente_falla(ruta):
    with pytest.raises(ValueError):
        editar_producto(999, {"precio": 100}, ruta=ruta)


def test_editar_sin_cambios_falla(ruta, id_producto):
    with pytest.raises(ValueError):
        editar_producto(id_producto, {}, ruta=ruta)
