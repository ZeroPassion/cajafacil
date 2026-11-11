import sqlite3
import pytest
from src.db import consult, crear_tablas, transaccion

INSERT_CLIENTE = "INSERT INTO clientes (nombre) VALUES (?)"


@pytest.fixture
def ruta(tmp_path):
    r = str(tmp_path / "prueba.db")
    crear_tablas(r)
    return r


def contar_clientes(ruta):
    return consult(ruta=ruta, consulta="SELECT COUNT(*) FROM clientes")[0][0]


def test_exito_guarda_y_devuelve_el_resultado(ruta):
    def trabajo(cursor):
        cursor.execute(INSERT_CLIENTE, ("Ana",))
        cursor.execute(INSERT_CLIENTE, ("Luis",))
        return cursor.lastrowid

    assert transaccion(ruta, trabajo) == 2
    assert contar_clientes(ruta) == 2


def test_un_error_deshace_todo_y_se_propaga(ruta):
    def trabajo(cursor):
        cursor.execute(INSERT_CLIENTE, ("Ana",))
        raise RuntimeError("falló a la mitad")

    with pytest.raises(RuntimeError):
        transaccion(ruta, trabajo)
    assert contar_clientes(ruta) == 0


def test_un_error_de_sqlite_conserva_su_tipo_y_deshace_todo(ruta):
    def trabajo(cursor):
        cursor.execute(
            "INSERT INTO productos (nombre, categoria, costo, precio, stock) VALUES ('A','G',1,1,1)"
        )
        cursor.execute(
            "INSERT INTO productos (nombre, categoria, costo, precio, stock) VALUES ('A','G',1,1,1)"
        )

    with pytest.raises(sqlite3.IntegrityError):
        transaccion(ruta, trabajo)
    assert consult(ruta=ruta, consulta="SELECT COUNT(*) FROM productos")[0][0] == 0
