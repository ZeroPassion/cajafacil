import tkinter as tk
from tkinter import ttk
from src.db import crear_tablas
from src.ui.inventario import PantallaInventario


class CajaFacilApp(tk.Tk):
    def __init__(self):
        super().__init__()
        crear_tablas()

        self.title("CajaFácil - Gestión de Negocio")
        self.geometry("900x550")
        self.minsize(750, 450)

        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")

        self._construir_pestanas()

    def _construir_pestanas(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_inventario = PantallaInventario(notebook)
        notebook.add(self.tab_inventario, text="  Inventario  ")

        for nombre in ["Ventas", "Fiado", "Gastos", "Resumen"]:
            frame = ttk.Frame(notebook, padding=20)
            ttk.Label(
                frame,
                text=f"Módulo de {nombre} (Próximamente)",
                font=("TkDefaultFont", 12, "italic"),
            ).pack(expand=True)
            notebook.add(frame, text=f"  {nombre}  ")
