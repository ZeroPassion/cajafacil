import sqlite3 as sql
from src.db import consult, DB_PATH, ejecutar_transaccion


def crear_cliente(nombre: str, telefono: str = None, ruta: str = DB_PATH):
    """Crea un cliente dentro de la tabla de clientes.

    Args:
        nombre (str): El nombre que recibira el cliente.
        telefono (str, optional): El telefono que se registrara, puede ser None. Defaults to None.
        ruta (str, optional): Referente a la base de datos. Defaults to DB_PATH.

    Raises:
        ValueError: El unico campo obligatorio es el nombre, por eso no puede estar vacio.

    Returns:
        _type_: _description_
    """
    sql_querry = """INSERT INTO clientes(nombre,telefono) VALUES (?,?)"""
    try:
        if nombre.strip() == "" or nombre == None:
            raise ValueError("Nombre del cliente vacio.")

        return consult(ruta=ruta, consulta=sql_querry, parametros=(nombre, telefono))

    except ValueError as e:
        print(f"Validacion fallida: {e}")
    return None


def listar_clientes(ruta=DB_PATH):
    """Lista los clientes activos dentro de la tabla de clientes.

    Args:
        ruta (str, optional): Referente a la base de datos. Defaults to DB_PATH.

    Returns:
        bool: Si todo fue correcto envia un valor de TRUE. Meramenttet por propositos de debug.
    """
    sql_querry = "SELECT * FROM clientes WHERE activo = 1"
    return consult(ruta=DB_PATH, consulta=sql_querry)


def editar_cliente(ID: int, nuevos_valores: dict = {}, ruta: str = DB_PATH):
    """Edita una fila de clientes para darle nuevos valores.

    Args:
        ID (int): El ID de la fila a editar.
        nuevos_valores (dict, optional): Diccionario con los nuevos valores, deben contener el nombre de la columna y su nuevo valor. Defaults to {}.
        ruta (str, optional): Referente a la base de datos. Defaults to DB_PATH.

    Raises:
        ValueError: El diccionario esta vacio.
        ValueError: El diccionario tiene columnas que no forman parte del esquema de la base de datos.
        ValueError: El ID del cliente que intenta editar no existe.

    Returns:
        _type_: _description_
    """
    if not nuevos_valores.keys():
        raise ValueError("Diccionario Vacio")

    columnas_validas = ["nombre,telefono"]
    for value in nuevos_valores.keys():
        if value not in columnas_validas:
            raise ValueError(f"Columna incorrecta dentro del diccionario:{value}")

    columnas = ", ".join([f"{columna} = ?" for columna in nuevos_valores.keys()])
    values = list(nuevos_valores.values()) + [ID]

    sql_querry = f"UPDATE clientes SET " + columnas + " WHERE id = ?"
    result = consult(ruta=ruta, consulta=sql_querry, parametros=values)
    if result == 0:
        raise ValueError(f"El cliente con ID {ID} no existe.")
    return True


def desactivar_cliente(ID, ruta: str = DB_PATH):
    """Desactiva el estado del cliente especificado con ID

    Args:
        ID (int | str): ID del cliente a modificar
        ruta (str, optional): Referente a la base de datos. Defaults to DB_PATH.

    Raises:
        ValueError: El ID proprocionado no existe en la base de datos.

    Returns:
        int: Por defecto CONSULT devuelve el conteo de rows modificadas.
    """
    sql_querry = """UPDATE clientes SET activo = 0 WHERE id = ?"""
    result = consult(ruta=ruta, consulta=sql_querry, parametros=(ID,))
    if result == None:
        raise ValueError("La entrada asociada con el ID no existe.")
    return result
