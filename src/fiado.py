from datetime import datetime
from src.db import DB_PATH, consult, transaccion

SQL_SALDO = """
SELECT COALESCE((SELECT SUM(total) FROM ventas WHERE cliente_id = ? AND tipo_pago = 'f'), 0)
     - COALESCE((SELECT SUM(monto) FROM abonos WHERE cliente_id = ?), 0)
"""


def _ahora():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def saldo_cliente(cliente_id, ruta=DB_PATH):
    """Devuelve lo que el cliente debe. Un cliente sin deuda devuelve 0."""
    existe = consult(
        ruta=ruta,
        consulta="SELECT 1 FROM clientes WHERE id = ?",
        parametros=(cliente_id,),
    )
    if not existe:
        raise ValueError("El cliente no existe.")
    return consult(ruta=ruta, consulta=SQL_SALDO, parametros=(cliente_id, cliente_id))[
        0
    ][0]


def registrar_abono(cliente_id, monto, nota=None, ruta=DB_PATH):
    """Registra un abono y devuelve su id.

    Raises:
        ValueError: monto inválido, cliente inexistente o abono mayor al saldo.
    """
    if monto <= 0:
        raise ValueError("El monto del abono debe ser mayor a 0.")
    fecha = _ahora()

    def trabajo(cursor):
        if (
            cursor.execute(
                "SELECT 1 FROM clientes WHERE id = ?", (cliente_id,)
            ).fetchone()
            is None
        ):
            raise ValueError("El cliente no existe.")
        saldo = cursor.execute(SQL_SALDO, (cliente_id, cliente_id)).fetchone()[0]
        if monto > saldo:
            raise ValueError(f"El abono ({monto}) supera el saldo pendiente ({saldo}).")
        cursor.execute(
            "INSERT INTO abonos (cliente_id, fecha, monto, nota) VALUES (?, ?, ?, ?)",
            (cliente_id, fecha, monto, nota),
        )
        return cursor.lastrowid

    return transaccion(trabajo=trabajo,ruta=ruta)


def clientes_con_deuda(ruta=DB_PATH):
    """Lista de (id, nombre, saldo) de los clientes activos con saldo mayor a 0, de mayor a menor."""
    return consult(
        ruta=ruta,
        consulta="""
        SELECT id, nombre, saldo FROM (
            SELECT c.id AS id, c.nombre AS nombre,
                   COALESCE((SELECT SUM(v.total) FROM ventas v WHERE v.cliente_id = c.id AND v.tipo_pago = 'f'), 0)
                 - COALESCE((SELECT SUM(a.monto) FROM abonos a WHERE a.cliente_id = c.id), 0) AS saldo
            FROM clientes c
            WHERE c.activo = 1
        )
        WHERE saldo > 0
        ORDER BY saldo DESC
        """,
    )
