import sqlite3 as sql

DB_PATH = "cajafacil_database.db"


def consult(ruta=DB_PATH, consulta="", parametros=()):
    """Funcion maestra para hacer operaciones en la base de datos

    Args:
        consulta (string, requirida): _Se le pasa la consulta a la funcion para ejecutar en la base de datos referida._
        ruta (string, opcional): Base de datos que se quiere modificar, tiene por default el nombre un nombre.
        parametros (tupla, optional): Serie de parametros que se utilizaran en conjunto a la consulta almacenados en tupla. Esta vacia por defecto.
    """
    tipo_querry = consulta.strip().upper()
    try:
        with sql.connect(ruta) as conexion:
            cursor = conexion.cursor()
            # Activacion de claves foraneas
            cursor.execute("PRAGMA foreign_keys = ON")
            # Ejecutando consulta
            cursor.execute(consulta, parametros)
            
            if tipo_querry.startswith("SELECT"):
                return cursor.fetchall();
            
            elif tipo_querry.startswith("INSERT"):
                conexion.commit()
                return cursor.lastrowid
            else:
                conexion.commit()
                return cursor.rowcount
            
    except sql.Error as e:
        print(f"Error al conectar o ejecutar consulta: {e}")


def crear_tablas(ruta=DB_PATH):
    """Funcion para crear las multiples tablas dentro de la base de datos en caso de que no existan"""

    # Productos
    consult(ruta=ruta,
        consulta="""CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY, 
            nombre VARCHAR(50) NOT NULL UNIQUE,
            categoria VARCHAR(50) NOT NULL, 
            costo DEC(18,2) NOT NULL DEFAULT 0.00, 
            precio DEC(18,2) NOT NULL DEFAULT 0.00, 
            stock INT NOT NULL DEFAULT 0, 
            stock_minimo INT NOT NULL DEFAULT 0, 
            activo BOOL NOT NULL DEFAULT 1
        )"""
    )
    # Movimientos del inventario
    consult(ruta=ruta,
        consulta="""CREATE TABLE IF NOT EXISTS movimientos_inventario (
            id INTEGER PRIMARY KEY,
            producto_id INT NOT NULL,
            tipo CHAR NOT NULL,
            cantidad INT NOT NULL,
            costo_unitario INT NOT NULL,
            fecha DATETIME NOT NULL, 
            nota VARCHAR(120),
            CONSTRAINT chk_tipo CHECK (tipo IN ('e','s','a')),
            FOREIGN KEY (producto_id) REFERENCES productos(id)
        )"""
    )
    # Clientes
    consult(ruta=ruta,
        consulta="""CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY,
            nombre VARCHAR(50) NOT NULL,
            telefono VARCHAR(20) UNIQUE,
            activo BOOL NOT NULL DEFAULT 1
        )"""
    )
    # Ventas
    consult(ruta=ruta,
        consulta="""CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY,
            cliente_id INT NOT NULL,
            fecha DATETIME NOT NULL,
            tipo_pago CHAR NOT NULL,
            total DEC(18,2) NOT NULL DEFAULT 0.00,
            CONSTRAINT chk_tipo_pago CHECK (tipo_pago IN ('c','f')),
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        )"""
    )
    # Detalle_ventas
    consult(ruta=ruta,
        consulta="""CREATE TABLE IF NOT EXISTS detalle_venta (
            id INTEGER PRIMARY KEY,
            venta_id INT NOT NULL,
            producto_id INT NOT NULL,
            cantidad INT NOT NULL,
            precio_unitario DEC(18,2) NOT NULL,
            costo_unitario DEC(18,2) NOT NULL,
            FOREIGN KEY (venta_id) REFERENCES ventas(id),
            FOREIGN KEY (producto_id) REFERENCES productos(id)
        )"""
    )
    # Abonos
    consult(ruta=ruta,
        consulta="""CREATE TABLE IF NOT EXISTS abonos (
            id INTEGER PRIMARY KEY,
            cliente_id INT NOT NULL,
            fecha DATETIME NOT NULL,
            monto DEC(18,2) NOT NULL DEFAULT 0.00,
            nota VARCHAR(120),
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        )"""
    )
    # Gastos
    consult(ruta=ruta,
        consulta="""CREATE TABLE IF NOT EXISTS gastos (
            id INTEGER PRIMARY KEY,
            fecha DATETIME NOT NULL,
            categoria VARCHAR(50) NOT NULL,
            descripcion VARCHAR(120),
            monto DEC(18,2) NOT NULL DEFAULT 0.00
        )"""
    )