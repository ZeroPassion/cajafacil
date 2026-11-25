import os
from datetime import date, timedelta

from src.db import consult, crear_tablas
from src.fiado import clientes_con_deuda, registrar_abono
from src.gastos import gastos_por_categoria, registrar_gasto
from src.resumen import resumen_periodo
from src.ventas import LineaVenta, registrar_venta

RUTA = "demo_cajafacil.db"

"""No he probado a hacer la interfaz, y creo que eso me anda mordiendo la columna ya. voy algo adelantado en el cronograma 
pero no por ello me puedo atrasar. Las interfaces son complicadas de unirificar, almenos en tkinter."""


def pesos(centavos):
    return f"RD$ {centavos / 100:,.2f}"


def nuevo_producto(nombre, costo, precio, stock, minimo):
    return consult(
        ruta=RUTA,
        consulta="""INSERT INTO productos (nombre, categoria, costo, precio, stock, stock_minimo)
                    VALUES (?, 'Colmado', ?, ?, ?, ?)""",
        parametros=(nombre, costo, precio, stock, minimo),
    )


def main():
    if os.path.exists(RUTA):
        os.remove(RUTA)
    crear_tablas(RUTA)

    arroz = nuevo_producto("Arroz (lb)", 3000, 4500, 500, 10)
    aceite = nuevo_producto("Aceite", 12000, 16000, 100, 5)
    nuevo_producto("Habichuelas (lb)", 5000, 7000, 4, 6)  # stock bajo a propósito
    rosa = consult(
        ruta=RUTA, consulta="INSERT INTO clientes (nombre) VALUES ('Doña Rosa')"
    )

    print("== Ventas ==")
    v1 = registrar_venta([LineaVenta(arroz, 120), LineaVenta(aceite, 25)], ruta=RUTA)
    print(f"Venta #{v1} de contado registrada")
    v2 = registrar_venta(
        [LineaVenta(aceite, 10)], tipo_pago="f", cliente_id=rosa, ruta=RUTA
    )
    print(f"Venta #{v2} a fiado (Doña Rosa) registrada")

    print("\n== Una venta que falla no deja nada a medias ==")
    try:
        registrar_venta([LineaVenta(arroz, 1), LineaVenta(aceite, 999)], ruta=RUTA)
    except ValueError as e:
        print("Rechazada:", e)

    registrar_abono(rosa, 50000, "Pago parcial", ruta=RUTA)
    registrar_gasto("luz", 150000, "Factura", ruta=RUTA)
    registrar_gasto("transporte", 30000, ruta=RUTA)
    registrar_gasto("mercancia", 400000, "Reposición de inventario", ruta=RUTA)

    print("\n== Clientes con deuda ==")
    for _, nombre, saldo in clientes_con_deuda(ruta=RUTA):
        print(f"{nombre}: {pesos(saldo)}")

    # Rango del mes actual: del día 1 hasta el día 1 del mes siguiente (fin exclusivo).
    primero = date.today().replace(day=1)
    desde = primero.isoformat()
    hasta = (primero + timedelta(days=32)).replace(day=1).isoformat()

    print("\n== Gastos por categoría ==")
    for categoria, total in gastos_por_categoria(desde, hasta, ruta=RUTA):
        print(f"{categoria:<12} {pesos(total)}")

    r = resumen_periodo(desde, hasta, ruta=RUTA)
    print("\n== Resumen del mes ==")
    for etiqueta, clave in [
        ("Ventas", "ventas"),
        ("Costo de lo vendido", "costo_ventas"),
        ("Ganancia bruta", "ganancia_bruta"),
        ("Gastos", "gastos"),
        ("GANANCIA ESTIMADA", "ganancia_estimada"),
        ("Cobrado", "cobrado"),
        ("Por cobrar", "por_cobrar"),
        ("Mercancía comprada", "mercancia_comprada"),
    ]:
        print(f"{etiqueta:<22}{pesos(r[clave]):>16}")
    print(f"{'Productos con stock bajo':<22}{r['productos_bajo_stock']:>16}")


if __name__ == "__main__":
    main()
