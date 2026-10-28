from src.db import consult, DB_PATH
from dataclasses import dataclass
from decimal import Decimal

@dataclass
class DataProducto:
    nombre: str
    categoria: str
    costo: Decimal
    precio: Decimal
    stock_inicial: int = 0
    stock_minimo: int = 0


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


def listar_productos(ruta=DB_PATH):
    """Devuelve la lista de productos dentro de la base de datos.

    Args:
        ruta (String, optional): Referencia a la base de dato. Defaults to DB_PATH.

    Returns:
        Array->Tuplas: Devuelve un Array con las tuplas de informacion adentro.
    """
    sql_querry = "SELECT * FROM productos WHERE activo = 1"
    result = consult(ruta=ruta, consulta=sql_querry)
    return result

def desactivar_producto(ID, ruta=DB_PATH):
    """Desactiva un producto suplementandole el ID

    Args:
        ID (integer): Identificador numerico correspondiente al producto a desactivar 
        ruta (string, optional): . Defaults to DB_PATH.

    Raises:
        Exception: Si el valor sobrepsa el numero actual de productos, levanta error.
    """    
    sql_querry="""UPDATE productos SET activo = 0 WHERE id = ?"""
    result = consult(ruta=ruta, consulta=sql_querry, parametros=ID)
    if result == 0:
        raise ValueError("La entrada asociada con el ID no existe.")
    return result

def productos_bajo_stock(ruta=DB_PATH):
    """Funcion que deuelve la lista de productos con necesidad de restock

    Args:
        ruta (string, optional): Referente base de datos. Defaults to DB_PATH.

    Raises:
        ValueError: _description_

    Returns:
        _type_: _description_
    """    
    sql_querry = """SELECT * FROM productos WHERE stock <= stock_minimo"""
    result = consult(ruta=ruta,consulta=sql_querry)
    if len(result) == 0:
        raise Exception("No existe ningun producto con stock por debajo del minimo actualmente.")
    return result