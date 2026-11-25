from datetime import datetime
from src.db import DB_PATH, consult

CATEGORIA_MERCANCIA = "mercancia"
CATEGORIAS_GASTO = (
    CATEGORIA_MERCANCIA, "alquiler", "luz", "agua", "internet", "transporte", "salarios", "otros",
)
FORMATO_FECHA = "%Y-%m-%d %H:%M:%S"


def validar_rango(desde, hasta):
    """Comprueba que el rango tenga sentido (desde < hasta)."""
    if desde >= hasta:
        raise ValueError("Rango inválido: 'desde' debe ser anterior a 'hasta'.")


def registrar_gasto(categoria, monto, descripcion=None, fecha=None, ruta=DB_PATH):
    """Registra un gasto y devuelve su id.

    Args:
        categoria (str): una de CATEGORIAS_GASTO.
        monto (int): centavos, mayor a 0.
        descripcion (str, optional): detalle libre.
        fecha (str, optional): 'AAAA-MM-DD' o 'AAAA-MM-DD HH:MM:SS'. Por defecto, ahora.

    Raises:
        ValueError: categoría, monto o fecha inválidos.
    """
    if categoria not in CATEGORIAS_GASTO:
        raise ValueError(f"Categoría inválida: '{categoria}'. Use una de: {', '.join(CATEGORIAS_GASTO)}.")
    if monto <= 0:
        raise ValueError("El monto del gasto debe ser mayor a 0.")
    if fecha is None:
        fecha = datetime.now().strftime(FORMATO_FECHA)
    else:
        try:
            # Se normaliza para que todas las fechas tengan el mismo formato y los rangos funcionen.
            fecha = datetime.fromisoformat(fecha).strftime(FORMATO_FECHA)
        except (TypeError, ValueError) as e:
            raise ValueError("Fecha inválida: use AAAA-MM-DD o AAAA-MM-DD HH:MM:SS.") from e
    return consult(
        ruta=ruta,
        consulta="INSERT INTO gastos (fecha, categoria, descripcion, monto) VALUES (?, ?, ?, ?)",
        parametros=(fecha, categoria, descripcion, monto),
    )


def listar_gastos(desde, hasta, ruta=DB_PATH):
    """Gastos del rango [desde, hasta), el más reciente primero.

    Devuelve tuplas (id, fecha, categoria, descripcion, monto).
    """
    validar_rango(desde, hasta)
    return consult(
        ruta=ruta,
        consulta="""SELECT id, fecha, categoria, descripcion, monto FROM gastos
                    WHERE fecha >= ? AND fecha < ?
                    ORDER BY fecha DESC, id DESC""",
        parametros=(desde, hasta),
    )


def gastos_por_categoria(desde, hasta, ruta=DB_PATH):
    """Total por categoría en [desde, hasta): lista de (categoria, total), de mayor a menor."""
    validar_rango(desde, hasta)
    return consult(
        ruta=ruta,
        consulta="""SELECT categoria, SUM(monto) AS total FROM gastos
                    WHERE fecha >= ? AND fecha < ?
                    GROUP BY categoria
                    ORDER BY total DESC, categoria ASC""",
        parametros=(desde, hasta),
    )