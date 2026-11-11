from dataclasses import dataclass
from datetime import datetime

from src.db import DB_PATH, transaccion

TIPOS_PAGO = ("c", "f")  # c = contado, f = fiado


@dataclass
class LineaVenta:
    producto_id: int
    cantidad: int


def _ahora():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def registrar_venta(
    lineas: list[LineaVenta] = [],
    tipo_pago: str = "c",
    cliente_id: int = None,
    ruta: str = DB_PATH,
):
    """Registra una venta y devuelve su id.

    Args:
        lineas (list[LineaVenta]): productos y cantidades vendidos.
        tipo_pago (str): 'c' contado o 'f' fiado.
        cliente_id (int, optional): obligatorio si el pago es fiado.
        ruta (str, optional): base de datos. Defaults to DB_PATH.

    Raises:
        ValueError: datos inválidos, cliente o producto inexistente,
            o stock insuficiente. En cualquier caso no se guarda nada.
    """
    if not lineas:
        raise ValueError("La venta debe tener al menos una línea.")
    if tipo_pago not in TIPOS_PAGO:
        raise ValueError("Tipo de pago inválido: use 'c' (contado) o 'f' (fiado).")
    if tipo_pago == "f" and cliente_id is None:
        raise ValueError("Una venta a fiado requiere un cliente.")
    for linea in lineas:
        if linea.cantidad <= 0:
            raise ValueError("La cantidad de cada línea debe ser mayor a 0.")

    fecha = _ahora()

    def trabajo(cursor):
        if cliente_id is not None:
            cliente = cursor.execute(
                "SELECT 1 FROM clientes WHERE id = ? AND activo = 1", (cliente_id,)
            ).fetchone()
            if cliente is None:
                raise ValueError("El cliente no existe o está desactivado.")

        cursor.execute(
            "INSERT INTO ventas (cliente_id, fecha, tipo_pago, total) VALUES (?, ?, ?, 0)",
            (cliente_id, fecha, tipo_pago),
        )
        venta_id = cursor.lastrowid

        total = 0
        for linea in lineas:
            # El stock se lee DENTRO de la transacción: si el mismo producto aparece en dos líneas, la segunda ya ve el stock descontado por la primera.
            producto = cursor.execute(
                "SELECT nombre, costo, precio, stock FROM productos WHERE id = ? AND activo = 1",
                (linea.producto_id,),
            ).fetchone()
            if producto is None:
                raise ValueError(
                    f"El producto {linea.producto_id} no existe o está desactivado."
                )
            nombre, costo, precio, stock = producto
            if linea.cantidad > stock:
                raise ValueError(
                    f"Stock insuficiente de '{nombre}': hay {stock} y se pidieron {linea.cantidad}."
                )
            # Precio y costo del momento: no cambian si el producto se edita después.
            cursor.execute(
                """INSERT INTO detalle_venta (venta_id, producto_id, cantidad, precio_unitario, costo_unitario)
                VALUES (?, ?, ?, ?, ?)""",
                (venta_id, linea.producto_id, linea.cantidad, precio, costo),
            )
            cursor.execute(
                "UPDATE productos SET stock = stock - ? WHERE id = ?",
                (linea.cantidad, linea.producto_id),
            )
            cursor.execute(
                """INSERT INTO movimientos_inventario (producto_id, tipo, cantidad, costo_unitario, fecha, nota)
                VALUES (?, 's', ?, ?, ?, ?)""",
                (linea.producto_id, linea.cantidad, costo, fecha, f"Venta #{venta_id}"),
            )
            total += precio * linea.cantidad
        cursor.execute("UPDATE ventas SET total = ? WHERE id = ?", (total, venta_id))
        return venta_id
    return transaccion(trabajo=trabajo, ruta=ruta)
