import sqlite3
import pytest
from src.db import consult, crear_tablas, ejecutar_transaccion

INSERT_PRODUCTO = """INSERT INTO productos (nombre, categoria, costo, precio, stock, stock_minimo)
                     VALUES (?, ?, ?, ?, ?, ?)"""


@pytest.fixture
def ruta(tmp_path):
    r = str(tmp_path / "prueba.db")
    crear_tablas(r)
    return r


def contar_productos(ruta):
    return consult(ruta=ruta, consulta="SELECT COUNT(*) FROM productos")[0][0]


def test_transaccion_exitosa_guarda_todas_las_operaciones(ruta):
    ejecutar_transaccion(
        ruta=ruta,
        operaciones=(
            (INSERT_PRODUCTO, ("Arroz", "Granos", 5000, 7500, 10, 2)),
            (INSERT_PRODUCTO, ("Habichuelas", "Granos", 4000, 6000, 5, 1)),
        ),
    )
    assert contar_productos(ruta) == 2


def test_transaccion_fallida_no_guarda_nada(ruta):
    """El segundo INSERT repite el nombre (UNIQUE) y falla: el primero tampoco debe quedar."""
    with pytest.raises(sqlite3.IntegrityError):
        ejecutar_transaccion(
            ruta=ruta,
            operaciones=(
                (INSERT_PRODUCTO, ("Arroz", "Granos", 5000, 7500, 10, 2)),
                (INSERT_PRODUCTO, ("Arroz", "Granos", 5000, 7500, 10, 2)),
            ),
        )
    assert contar_productos(ruta) == 0


def test_falla_al_conectar_lanza_el_error_real(tmp_path):
    """Con una carpeta inexistente debe llegar OperationalError, no un UnboundLocalError."""
    ruta_mala = str(tmp_path / "no_existe" / "prueba.db")
    with pytest.raises(sqlite3.OperationalError):
        ejecutar_transaccion(
            ruta=ruta_mala,
            operaciones=((INSERT_PRODUCTO, ("Arroz", "Granos", 5000, 7500, 10, 2))),
        )
