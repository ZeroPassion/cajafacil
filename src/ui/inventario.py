import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from src.ui.helpers import pesos_a_centavos, centavos_a_pesos

from src.inventario import (
    DataProducto,
    DataMovimiento,
    listar_productos,
    crear_producto,
    editar_producto,
    desactivar_producto,
    registrar_entrada,
    registrar_salida,
)


class PantallaInventario(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=15)
        self.productos_cache = {}
        self._construir_ui()
        self.cargar_productos()

    def _construir_ui(self):
        barra = ttk.Frame(self)
        barra.pack(fill="x", pady=(0, 10))

        ttk.Button(barra, text="+ Nuevo Producto", command=self._abrir_modal_crear).pack(side="left", padx=(0, 5))
        ttk.Button(barra, text="Editar", command=self._abrir_modal_editar).pack(side="left", padx=5)
        ttk.Button(barra, text="Desactivar", command=self._desactivar_seleccionado).pack(side="left", padx=5)

        ttk.Separator(barra, orient="vertical").pack(side="left", fill="y", padx=10)

        ttk.Button(barra, text="+ Entrada Stock", command=lambda: self._abrir_modal_movimiento("e")).pack(side="left", padx=5)
        ttk.Button(barra, text="- Salida Stock", command=lambda: self._abrir_modal_movimiento("s")).pack(side="left", padx=5)

        ttk.Button(barra, text="Actualizar", command=self.cargar_productos).pack(side="right")
        
        # Tabla de visualizacion
        style = ttk.Style()
        style.configure("Treeview", rowheight=28, font=("TkDefaultFont", 10))
        style.configure("Treeview.Heading", font=("TkDefaultFont", 10, "bold"), relief="raised", borderwidth=1)

        columnas = ("id", "nombre", "categoria", "costo", "precio", "stock", "stock_min")
        self.tabla = ttk.Treeview(self, columns=columnas, show="headings", selectmode="browse")

        encabezados = {
            "id": ("ID", 50, "center"),
            "nombre": ("Producto", 210, "w"),
            "categoria": ("Categoría", 140, "w"),
            "costo": ("Costo", 100, "e"),
            "precio": ("Precio", 100, "e"),
            "stock": ("Stock", 75, "center"),
            "stock_min": ("Mínimo", 75, "center"),
        }

        for col, (texto, ancho, alineacion) in encabezados.items():
            self.tabla.heading(col, text=texto)
            self.tabla.column(col, width=ancho, anchor=alineacion, stretch=True)

        # Filas alternas y alerta de bajo stock
        self.tabla.tag_configure("par", background="#f7f9fc")
        self.tabla.tag_configure("impar", background="#ffffff")
        self.tabla.tag_configure("bajo_stock", background="#ffd6d6")

        scroll = ttk.Scrollbar(self, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll.set)

        # Barra inferior de estado
        self.lbl_estado = ttk.Label(self, text="Listo.", foreground="#555555")
        self.lbl_estado.pack(side="bottom", anchor="w", pady=(8, 0))

        self.tabla.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def cargar_productos(self):
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)
        self.productos_cache.clear()

        try:
            filas = listar_productos()
            for idx, row in enumerate(filas):
                prod_id, nombre, categoria, costo, precio, stock, stock_min, activo = row
                self.productos_cache[prod_id] = {
                    "id": prod_id,
                    "nombre": nombre,
                    "categoria": categoria,
                    "costo": int(costo),
                    "precio": int(precio),
                    "stock": int(stock),
                    "stock_minimo": int(stock_min),
                }

                if stock <= stock_min:
                    tags = ("bajo_stock",)
                else:
                    tags = ("par",) if idx % 2 == 0 else ("impar",)

                self.tabla.insert(
                    "",
                    "end",
                    values=(
                        prod_id,
                        nombre,
                        categoria,
                        centavos_a_pesos(int(costo)),
                        centavos_a_pesos(int(precio)),
                        stock,
                        stock_min,
                    ),
                    tags=tags,
                )
            self.lbl_estado.config(text=f"Mostrando {len(filas)} productos activos.")
        except Exception as e:
            messagebox.showerror("Error al cargar", str(e))

    def _obtener_producto_seleccionado(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Selecciona un producto de la tabla primero.")
            return None
        valores = self.tabla.item(seleccion[0])["values"]
        prod_id = int(valores[0])
        return self.productos_cache.get(prod_id)

    def _abrir_modal_crear(self):
        self._mostrar_formulario(titulo="Nuevo Producto")

    def _abrir_modal_editar(self):
        producto = self._obtener_producto_seleccionado()
        if producto:
            self._mostrar_formulario(titulo="Editar Producto", producto=producto)

    def _mostrar_formulario(self, titulo: str, producto: dict = None):
        modal = tk.Toplevel(self)
        modal.title(titulo)
        modal.geometry("360x310")
        modal.resizable(False, False)
        modal.transient(self.winfo_toplevel())
        modal.grab_set()

        frame = ttk.Frame(modal, padding=15)
        frame.pack(fill="both", expand=True)

        campos = [
            ("Nombre:", "nombre"),
            ("Categoría:", "categoria"),
            ("Costo ($):", "costo"),
            ("Precio ($):", "precio"),
            ("Stock inicial:", "stock"),
            ("Stock mínimo:", "stock_min"),
        ]
        entries = {}

        for idx, (etiqueta, clave) in enumerate(campos):
            ttk.Label(frame, text=etiqueta).grid(row=idx, column=0, sticky="w", pady=5)
            ent = ttk.Entry(frame, width=28)
            ent.grid(row=idx, column=1, pady=5)
            entries[clave] = ent

        if producto:
            entries["nombre"].insert(0, producto["nombre"])
            entries["categoria"].insert(0, producto["categoria"])
            entries["costo"].insert(0, centavos_a_pesos(producto["costo"], incluir_simbolo=False))
            entries["precio"].insert(0, centavos_a_pesos(producto["precio"], incluir_simbolo=False))
            entries["stock"].insert(0, str(producto["stock"]))
            entries["stock_min"].insert(0, str(producto["stock_minimo"]))

            entries["stock"].configure(state="disabled")
            entries["stock_min"].configure(state="disabled")

        def guardar():
            try:
                nombre = entries["nombre"].get().strip()
                categoria = entries["categoria"].get().strip()
                if not nombre:
                    raise ValueError("El nombre del producto no puede estar vacío.")
                if not categoria:
                    raise ValueError("La categoría no puede estar vacía.")

                costo_centavos = pesos_a_centavos(entries["costo"].get())
                precio_centavos = pesos_a_centavos(entries["precio"].get())

                if producto:
                    nuevos_valores = {
                        "nombre": nombre,
                        "categoria": categoria,
                        "costo": costo_centavos,
                        "precio": precio_centavos,
                    }
                    editar_producto(producto["id"], nuevos_valores)
                else:
                    try:
                        stock_ini = int(entries["stock"].get().strip() or "0")
                        stock_min = int(entries["stock_min"].get().strip() or "0")
                    except ValueError:
                        raise ValueError("El stock inicial y mínimo deben ser números enteros.")

                    if stock_ini < 0 or stock_min < 0:
                        raise ValueError("El stock no puede ser negativo.")

                    nuevo = DataProducto(
                        nombre=nombre,
                        categoria=categoria,
                        costo=costo_centavos,
                        precio=precio_centavos,
                        stock_inicial=stock_ini,
                        stock_minimo=stock_min,
                    )
                    res = crear_producto(nuevo)
                    if res is None:
                        raise ValueError("No se pudo crear el producto. Verifica que el nombre no esté repetido.")

                modal.destroy()
                self.cargar_productos()

            except ValueError as e:
                messagebox.showerror("Error de validación", str(e), parent=modal)
            except Exception as e:
                messagebox.showerror("Error inesperado", str(e), parent=modal)

        ttk.Button(frame, text="Guardar", command=guardar).grid(row=len(campos), column=0, columnspan=2, pady=15)

    def _abrir_modal_movimiento(self, tipo: str):
        producto = self._obtener_producto_seleccionado()
        if not producto:
            return

        titulo = "Registrar Entrada de Stock" if tipo == "e" else "Registrar Salida de Stock"
        modal = tk.Toplevel(self)
        modal.title(titulo)
        modal.geometry("340x210")
        modal.resizable(False, False)
        modal.transient(self.winfo_toplevel())
        modal.grab_set()

        frame = ttk.Frame(modal, padding=15)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text=f"Producto: {producto['nombre']}", font=("TkDefaultFont", 9, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 10)
        )

        ttk.Label(frame, text="Cantidad:").grid(row=1, column=0, sticky="w", pady=5)
        entry_cant = ttk.Entry(frame, width=24)
        entry_cant.grid(row=1, column=1, pady=5)

        ttk.Label(frame, text="Nota (opcional):").grid(row=2, column=0, sticky="w", pady=5)
        entry_nota = ttk.Entry(frame, width=24)
        entry_nota.grid(row=2, column=1, pady=5)

        def confirmar():
            try:
                try:
                    cantidad = int(entry_cant.get().strip())
                except ValueError:
                    raise ValueError("La cantidad debe ser un número entero.")

                movimiento = DataMovimiento(
                    id_producto=producto["id"],
                    tipo=tipo,
                    cantidad=cantidad,
                    costo_unitario=producto["costo"],
                    fecha=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    nota=entry_nota.get().strip(),
                )

                if tipo == "e":
                    registrar_entrada(movimiento)
                else:
                    registrar_salida(movimiento)

                modal.destroy()
                self.cargar_productos()

            except ValueError as e:
                messagebox.showerror("Error de validación", str(e), parent=modal)
            except Exception as e:
                messagebox.showerror("Error en movimiento", str(e), parent=modal)

        ttk.Button(frame, text="Confirmar", command=confirmar).grid(row=3, column=0, columnspan=2, pady=15)

    def _desactivar_seleccionado(self):
        producto = self._obtener_producto_seleccionado()
        if not producto:
            return

        if not messagebox.askyesno("Confirmar", f"¿Desactivar '{producto['nombre']}' del inventario?"):
            return

        try:
            desactivar_producto(producto["id"])
            self.cargar_productos()
            self.lbl_estado.config(text=f"Producto '{producto['nombre']}' desactivado correctamente.")
            messagebox.showinfo("Desactivado", f"El producto '{producto['nombre']}' fue desactivado y retirado de la lista activa.")
        except ValueError as e:
            messagebox.showerror("Error", str(e))
