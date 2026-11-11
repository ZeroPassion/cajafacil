import sqlite3 as sql
from contextlib import closing

DB_PATH = "cajafacil_database.db"


def consult(ruta: str = DB_PATH, consulta: str = "", parametros: tuple = ()):
    """Funcion maestra para hacer operaciones en la base de datos

    Args:
        consulta (string, requirida): _Se le pasa la consulta a la funcion para ejecutar en la base de datos referida._
        ruta (string, opcional): Base de datos que se quiere modificar, tiene por default el nombre un nombre.
        parametros (tupla, optional): Serie de parametros que se utilizaran en conjunto a la consulta almacenados en tupla. Esta vacia por defecto.
    """
    tipo_querry = consulta.strip().upper()
    with closing(sql.connect(ruta)) as conexion:
        # Activacion de claves foraneas
        conexion.execute("PRAGMA foreign_keys = ON")
        try:
            cursor = conexion.cursor()
            # Ejecutando consulta
            cursor.execute(consulta, parametros)

            if tipo_querry.startswith("SELECT"):
                return cursor.fetchall()

            elif tipo_querry.startswith("INSERT"):
                conexion.commit()
                return cursor.lastrowid
            else:
                conexion.commit()
                return cursor.rowcount

        except sql.Error as err:
            print(f"La consulta ha fallado: {err=}, {type(err)=}")
            raise


def ejecutar_transaccion(ruta: str = DB_PATH, operaciones: tuple = ()):
    """Ejecuta un numero de consultas seguidas, cancelando en casos especificos para no procesar erorres dentro de la base de datos.

    Args:
        ruta (str, optional): Referente a la base de datos. Defaults to DB_PATH.
        operaciones (tuple, optional): Una tupla que contiene las operaciones, se pasa cada una asi: (querry, param). Defaults to ().

    Raises:
        ValueError: Se necesitan operaciones para realizar consultas.
    """
    if not operaciones:
        raise ValueError("La lista de operaciones no puedde estar vacia.")
    with closing(sql.connect(ruta)) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            cursor = conn.cursor()
            for consulta, params in operaciones:
                cursor.execute(consulta, params)
            conn.commit()
        except sql.OperationalError as e:
            print(f"Transaccion fallo: {e}")
            raise
        except sql.IntegrityError as e:
            print(f"Se ha intentado operar sobre un objeto inexistente, Err: {e}")
            raise
        except sql.Error as e:
            print(f"Error general de SQLite: {e}")
            raise


def transaccion(trabajo, ruta: str = DB_PATH):
    """Presta cursor a callback para hacer operaciones especificas con mayor libertad.

    Args:
        trabajo (callback): Funcion a la que se le va a pasar el cursor.
        ruta (str, optional): Referente a la base de datos. Defaults to DB_PATH.

    Returns:
        SQL_RESPONSE: Depende de las operaciones realizadas por callback.
    """
    with closing(sql.connect(ruta)) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        cur = conn.cursor()
        try:
            result = trabajo(cur)
            conn.commit()
            return result
        except Exception:
            conn.rollback()
            raise


# NOTA: Todos el dinero sera puesto en CENTAVOS para evitar errores de redondeo. Dado a que este programa no va dirigido a grandes compañias que
# manejan billones de pesos, considero que esto es lo mejor.


def crear_tablas(ruta=DB_PATH):
    """Funcion para crear las multiples tablas dentro de la base de datos en caso de que no existan"""

    # Productos
    consult(
        ruta=ruta,
        consulta="""CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY, 
            nombre VARCHAR(50) NOT NULL UNIQUE,
            categoria VARCHAR(50) NOT NULL, 
            costo INT NOT NULL DEFAULT 0.00, 
            precio INT NOT NULL DEFAULT 0.00, 
            stock INT NOT NULL DEFAULT 0 CHECK(stock >= 0), 
            stock_minimo INT NOT NULL DEFAULT 0, 
            activo BOOL NOT NULL DEFAULT 1
        )""",
    )
    # Movimientos del inventario
    consult(
        ruta=ruta,
        consulta="""CREATE TABLE IF NOT EXISTS movimientos_inventario (
            id INTEGER PRIMARY KEY,
            producto_id INT NOT NULL,
            tipo CHAR NOT NULL,
            cantidad INT NOT NULL,
            costo_unitario INT,
            fecha DATETIME NOT NULL DEFAULT (datetime('now','localtime')), 
            nota VARCHAR(120),
            CONSTRAINT chk_tipo CHECK (tipo IN ('e','s','a')),
            FOREIGN KEY (producto_id) REFERENCES productos(id)
        )""",
    )
    # Clientes
    consult(
        ruta=ruta,
        consulta="""CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY,
            nombre VARCHAR(50) NOT NULL,
            telefono VARCHAR(20) UNIQUE,
            activo BOOL NOT NULL DEFAULT 1
        )""",
    )
    # Ventas
    consult(
        ruta=ruta,
        consulta="""CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY,
            cliente_id INT NOT NULL,
            fecha DATETIME NOT NULL DEFAULT (datetime('now','localtime')),
            tipo_pago CHAR NOT NULL,
            total INT NOT NULL DEFAULT 0.00,
            CONSTRAINT chk_client_requerido CHECK (tipo_pago IS NOT 'f' OR (cliente_id IS NOT NULL AND cliente_id > 0)),
            CONSTRAINT chk_tipo_pago CHECK (tipo_pago IN ('c','f')),
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        )""",
    )
    # Detalle_ventas
    consult(
        ruta=ruta,
        consulta="""CREATE TABLE IF NOT EXISTS detalle_venta (
            id INTEGER PRIMARY KEY,
            venta_id INT NOT NULL,
            producto_id INT NOT NULL,
            cantidad INT NOT NULL,
            precio_unitario INT NOT NULL,
            costo_unitario INT NOT NULL,
            FOREIGN KEY (venta_id) REFERENCES ventas(id),
            FOREIGN KEY (producto_id) REFERENCES productos(id)
        )""",
    )
    # Abonos
    consult(
        ruta=ruta,
        consulta="""CREATE TABLE IF NOT EXISTS abonos (
            id INTEGER PRIMARY KEY,
            cliente_id INT NOT NULL,
            fecha DATETIME NOT NULL DEFAULT (datetime('now','localtime')), 
            monto INT NOT NULL DEFAULT 0.00,
            nota VARCHAR(120),
            CONSTRAINT chk_monto CHECK (monto > 0),
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        )""",
    )
    # Gastos
    consult(
        ruta=ruta,
        consulta="""CREATE TABLE IF NOT EXISTS gastos (
            id INTEGER PRIMARY KEY,
            fecha DATETIME NOT NULL DEFAULT (datetime('now','localtime')), 
            categoria VARCHAR(50) NOT NULL,
            descripcion VARCHAR(120),
            monto INT NOT NULL DEFAULT 0.00,
            CONSTRAINT chk_monto CHECK (monto > 0)
        )""",
    )
