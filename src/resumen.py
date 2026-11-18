from src.db import DB_PATH, consult
from src.gastos import CATEGORIA_MERCANCIA, validar_rango

"""
    Ventas = todo lo vendido en el período (contado + fiado)
    Costo_ventas = costo de lo vendido (cantidad x costo unitario del momento)
    Ganancia_bruta = ventas - costo_ventas
    Gastos = gastos del período SIN la categoría 'mercancia'
    Ganancia_estimada = ganancia_bruta - gastos
    Cobrado = ventas de contado + abonos recibidos en el período
    Por_cobrar = saldo total del fiado (no depende del período)
"""
"""
La mercancía comprada se resta de la ganancia: ya entra por el costo de lo
vendido, y restarla otra vez la contaría doble.
"""


def _valor(ruta, consulta, parametros=()):
    return consult(ruta=ruta, consulta=consulta, parametros=parametros)[0][0]


def resumen_periodo(desde, hasta, ruta=DB_PATH):
    """Devuelve un diccionario con el resumen del rango [desde, hasta)."""
    validar_rango(desde, hasta)
    rango = (desde, hasta)

    ventas = _valor(
        ruta,
        "SELECT COALESCE(SUM(total), 0) FROM ventas WHERE fecha >= ? AND fecha < ?",
        rango,
    )
    costo_ventas = _valor(
        ruta,
        """SELECT COALESCE(SUM(d.cantidad * d.costo_unitario), 0)
           FROM detalle_venta d JOIN ventas v ON v.id = d.venta_id
           WHERE v.fecha >= ? AND v.fecha < ?""",
        rango,
    )
    gastos = _valor(
        ruta,
        "SELECT COALESCE(SUM(monto), 0) FROM gastos WHERE fecha >= ? AND fecha < ? AND categoria <> ?",
        rango + (CATEGORIA_MERCANCIA,),
    )
    mercancia = _valor(
        ruta,
        "SELECT COALESCE(SUM(monto), 0) FROM gastos WHERE fecha >= ? AND fecha < ? AND categoria = ?",
        rango + (CATEGORIA_MERCANCIA,),
    )
    contado = _valor(
        ruta,
        "SELECT COALESCE(SUM(total), 0) FROM ventas WHERE fecha >= ? AND fecha < ? AND tipo_pago = 'c'",
        rango,
    )
    abonos = _valor(
        ruta,
        "SELECT COALESCE(SUM(monto), 0) FROM abonos WHERE fecha >= ? AND fecha < ?",
        rango,
    )
    por_cobrar = _valor(
        ruta,
        """SELECT COALESCE((SELECT SUM(total) FROM ventas WHERE tipo_pago = 'f'), 0)
                - COALESCE((SELECT SUM(monto) FROM abonos), 0)""",
    )
    bajo_stock = _valor(
        ruta,
        "SELECT COUNT(*) FROM productos WHERE activo = 1 AND stock <= stock_minimo",
    )

    ganancia_bruta = ventas - costo_ventas
    return {
        "ventas": ventas,
        "costo_ventas": costo_ventas,
        "ganancia_bruta": ganancia_bruta,
        "gastos": gastos,
        "ganancia_estimada": ganancia_bruta - gastos,
        "cobrado": contado + abonos,
        "por_cobrar": por_cobrar,
        "mercancia_comprada": mercancia,
        "productos_bajo_stock": bajo_stock,
    }
