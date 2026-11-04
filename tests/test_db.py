from src.db import consult, crear_tablas

def test_crear_tablas(tmp_path):
    ruta = tmp_path / "prueba.db"
    crear_tablas(ruta)
    filas = consult(ruta=ruta, consulta="SELECT name FROM sqlite_master WHERE type='table'")
    assert len(filas) == 7
    
def test_nombres_de_tablas(tmp_path):
    ruta = tmp_path / "prueba.db"
    crear_tablas(ruta)
    filas = consult(ruta=ruta, consulta="SELECT name FROM sqlite_master WHERE type='table'")
    assert {f[0] for f in filas} == {"productos", "movimientos_inventario", "clientes", "ventas", "detalle_venta", "abonos", "gastos"}