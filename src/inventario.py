import sqlite3 as sql
from src.db import consult, DB_PATH, ejecutar_transaccion
from dataclasses import dataclass


@dataclass
class DataProducto:
    nombre: str
    categoria: str
    costo: int
    precio: int
    stock_inicial: int = 0
    stock_minimo: int = 0


@dataclass
class DataMovimiento:
    id_producto: int
    tipo: str
    cantidad: int
    costo_unitario: int
    fecha: str
    nota: str = ""


def crear_producto(producto: DataProducto, ruta: str = DB_PATH):
    """Crea productos dentro de la base de datos

    Args:
        nombre (string): Nombre del producto
        categoria (string): Nombre de la categoria en la que se agrupa
        costo (Decimal-2): Costo Unitario
        precio (Decimal-2): Precio Unitario
        stock_inicial (int, optional): Stock Inicial del producto. Defaults to 0.
        stock_minimo (int, optional): Stock minimo para la alerta. Defaults to 0.
        ruta (String, optional): referencia a la base de datos. Defaults to DB_PATH.

    Returns:
        Integer: Idealmente devuelve el ID de la ultima fila para verificar la existencia de las filas.
    """
    sql_querry = """INSERT INTO productos(nombre,categoria,costo,precio,stock,stock_minimo) 
    VALUES (?,?,?,?,?,?)
    """
    values = (
        producto.nombre,
        producto.categoria,
        str(producto.costo),
        str(producto.precio),
        producto.stock_inicial,
        producto.stock_minimo,
    )
    try:
        if producto.nombre.strip() == "":
            raise ValueError("Nombre vacio")
        result = consult(ruta=ruta, consulta=sql_querry, parametros=values)
        return result
    except ValueError as err:
        print(f"Validacion Fallida: {e}")
    return None


def listar_productos(ruta: str = DB_PATH):
    """Devuelve la lista de productos dentro de la base de datos.

    Args:
        ruta (String, optional): Referencia a la base de dato. Defaults to DB_PATH.

    Returns:
        Array->Tuplas: Devuelve un Array con las tuplas de informacion adentro.
    """
    sql_querry = "SELECT * FROM productos WHERE activo = 1"
    result = consult(ruta=ruta, consulta=sql_querry)
    return result


def desactivar_producto(ID, ruta: str = DB_PATH):
    """Desactiva un producto suplementandole el ID

    Args:
        ID (integer): Identificador numerico correspondiente al producto a desactivar
        ruta (string, optional): . Defaults to DB_PATH.

    Raises:
        Exception: Si el valor sobrepsa el numero actual de productos, levanta error.
    """
    sql_querry = """UPDATE productos SET activo = 0 WHERE id = ?"""
    result = consult(ruta=ruta, consulta=sql_querry, parametros=(ID,))
    if result == None:
        raise ValueError("La entrada asociada con el ID no existe.")
    return result


def productos_bajo_stock(ruta: str = DB_PATH):
    """Funcion que deuelve la lista de productos con necesidad de restock

    Args:
        ruta (string, optional): Referente base de datos. Defaults to DB_PATH.

    Raises:
        Exception: Si devuelve un None es error.

    Returns:
        List: Devuelve una lista, este vacia o no, con los resultados.
    """
    sql_querry = (
        """SELECT * FROM productos WHERE stock <= stock_minimo AND activo = 1"""
    )
    result = consult(ruta=ruta, consulta=sql_querry)
    if result == None:
        raise Exception(
            "No existe ningun producto con stock por debajo del minimo actualmente."
        )
    return result


def registrar_entrada(move: DataMovimiento, ruta: str = DB_PATH):
    if move.cantidad <= 0:
        raise ValueError("Cantidad invalida.")

    sql_querry_one = """
    UPDATE productos SET stock = stock + ? WHERE id = ?
    """
    sql_querry_two = """
    INSERT INTO movimientos_inventario (producto_id, tipo, cantidad, costo_unitario, fecha, nota)
    VALUES (?,?,?,?,?,?)
    """
    values = (
        move.id_producto,
        move.tipo,
        move.cantidad,
        move.costo_unitario,
        move.fecha,
        move.nota,
    )
    try:
        ejecutar_transaccion(
            ruta=ruta,
            operaciones=(
                (sql_querry_one, (move.cantidad, move.id_producto)),
                (sql_querry_two, values),
            ),
        )
    except sql.IntegrityError as e:
        raise ValueError("El producto especificado no existe.") from e


def registrar_salida(move: DataMovimiento, ruta: str = DB_PATH):
    """Registra salidas y cambia el stock acorde.

    Args:
        move (DataMovimiento): Dataset para almacenar los datos de la salida.
        ruta (str, optional): Referente a la base de datos. Defaults to DB_PATH.

    Raises:
        ValueError: Cantidad invalida menor o igual que cero.
        ValueError: Handler de IDs no existentes que no cambian nada en la base de datos.
    """    
    if move.cantidad <= 0:
        raise ValueError("Cantidad invalida.")
    sql_querry_one = """
    UPDATE productos SET stock = stock - ? WHERE id = ?
    """
    sql_querry_two = """
    INSERT INTO movimientos_inventario (producto_id, tipo, cantidad, costo_unitario, fecha, nota)
    VALUES (?,?,?,?,?,?)
    """
    values = (
        move.id_producto,
        move.tipo,
        move.cantidad,
        move.costo_unitario,
        move.fecha,
        move.nota,
    )
    try:
        ejecutar_transaccion(
            ruta=ruta,
            operaciones=(
                (sql_querry_one, (move.cantidad, move.id_producto)),
                (sql_querry_two, values),
            ),
        )
    except sql.IntegrityError as e:
        raise ValueError("El producto especificado no existe.") from e


def editar_producto(ID: int, nuevos_valores: dict = {}, ruta: str = DB_PATH):
    """Edita aspectos basicos del producto seleccionado

    Args:
        ID (int): ID del producto en base de datos
        nuevos_valores (dict, optional): Los valores a cambiar del producto.. Defaults to {}.
        ruta (str, optional): Referente a la base de datos.. Defaults to DB_PATH.

    Raises:
        ValueError: Diccionario Vacio
        ValueError: Columna no permitida dentro del diccionario
        ValueError: Producto inexistente
    """
    if not nuevos_valores.keys():
        raise ValueError("Diccionario vacio.")
    columnas_validas = [
        "nombre",
        "categoria",
        "costo",
        "precio",
    ]
    for value in nuevos_valores.keys():
        if value not in columnas_validas:
            raise ValueError(
                "Columna incorrecta dentro del diccionario, revisa por columna invalida."
            )

    columnas = ", ".join([f"{columna} = ?" for columna in nuevos_valores.keys()])
    values = list(nuevos_valores.values()) + [ID]
    sql_querry = f"UPDATE productos SET " + columnas + " WHERE id = ?"
    result = consult(ruta=ruta, consulta=sql_querry, parametros=values)
    if result == 0:
        raise ValueError(f"El producto con ID {ID} no existe.")
