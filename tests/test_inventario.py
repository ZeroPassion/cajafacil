import pytest
from src.db import crear_tablas
from src.inventario import crear_producto, listar_productos, DataProducto, desactivar_producto, productos_bajo_stock
from decimal import Decimal
from dataclasses import replace

@pytest.fixture
def producto_valido():
    return DataProducto(
        nombre="Teclado Mecanico",
        categoria="Electronico",
        costo=Decimal("45.00"),
        precio=Decimal("89.00"),
        stock_inicial=10,
        stock_minimo=2
    )
    
@pytest.fixture
def ruta(tmp_path):
    r = tmp_path / "prueba.db"
    ruta_str = str(r)
    crear_tablas(ruta_str)
    return ruta_str

def test_crear_un_producto(producto_valido, ruta):
    lastrow = crear_producto(ruta=ruta,producto=producto_valido)
    assert lastrow is not None
    assert lastrow > 0

def test_listar_productos(ruta):
    crear_producto(ruta=ruta, producto=producto_valido)
    result = listar_productos(ruta=ruta)
    assert len(result) > 0 
    assert isinstance(result,list)
    assert result[0][0] == 1
    assert result[0][1] == "Teclado Mecanico"

def test_desactivar_productos(ruta,producto_valido):
    prod = crear_producto(ruta=ruta,producto=producto_valido)
    assert len(listar_productos(ruta=ruta)) > 0
    desactivar_producto(prod,ruta=ruta)
    assert len(listar_productos(ruta=ruta)) == 0

def test_productos_bajo_stock(ruta,producto_valido):
    pro1 = crear_producto(ruta=ruta, producto=replace(producto_valido, stock_inicial=1, stock_minimo=2))
    pro2 = crear_producto(ruta=ruta, producto=replace(producto_valido, stock_inicial=10, stock_minimo=2))
    assert len(productos_bajo_stock(ruta=ruta)) == 1