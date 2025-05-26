import tkinter as tk
from tkinter import ttk, messagebox, font
import sqlite3
import smtplib
import pyperclip
from email.mime.text import MIMEText
from email.utils import formatdate

class ClientDatabaseApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Gestión de Clientes")
        self.root.geometry("1200x800")
    
        
        self.seleccion_persistente = set()  # Para almacenar selecciones persistentes
        self.current_clients = []
        self.categories = []
        
        # Configurar fuente predeterminada
        default_font = font.nametofont("TkDefaultFont")
        default_font.configure(size=10)
        self.root.option_add("*Font", default_font)
        
        # Configuración de la base de datos
        self.conn = sqlite3.connect('clientes.db')
        self.inicializar_base_datos()
        
        # Configurar estilos
        self.style = ttk.Style()
        self.style.configure('TFrame', background='#f0f0f0')
        self.style.configure('TButton', font=('Arial', 11), padding=8)
        self.style.configure('TEntry', font=('Arial', 11), padding=5)
        self.style.configure('TLabel', font=('Arial', 11))
        
        # Crear interfaz
        self.crear_componentes()
        self.cargar_categorias()
        
    def inicializar_base_datos(self):
        """Crear tablas y categoría predeterminada si es necesario"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categorias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL UNIQUE
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS clientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    correo TEXT NOT NULL UNIQUE,
                    telefono TEXT NOT NULL,
                    contacto TEXT NOT NULL,
                    categoria_id INTEGER DEFAULT 1,
                    FOREIGN KEY(categoria_id) REFERENCES categorias(id)
                )
            """)
            # Verificar columnas existentes
            cursor.execute("PRAGMA table_info(clientes)")
            columnas = [columna[1] for columna in cursor.fetchall()]
            if 'contacto' not in columnas:
                cursor.execute("ALTER TABLE clientes ADD COLUMN contacto TEXT NOT NULL DEFAULT ''")
            if 'categoria_id' not in columnas:
                cursor.execute("ALTER TABLE clientes ADD COLUMN categoria_id INTEGER DEFAULT 1")
            
            cursor.execute("""
                INSERT OR IGNORE INTO categorias (id, nombre) VALUES (1, 'Clientes')
            """)
            self.conn.commit()
        except Exception as e:
            messagebox.showerror("Error de Base de Datos", f"Inicialización fallida: {str(e)}")

    def crear_componentes(self):
        """Crear y organizar componentes de la interfaz"""
        marco_principal = ttk.Frame(self.root)
        marco_principal.pack(padx=25, pady=25, fill=tk.BOTH, expand=True)
        
        # Panel Izquierdo
        panel_izquierdo = ttk.Frame(marco_principal, width=300)
        panel_izquierdo.grid(row=0, column=0, padx=15, pady=15, sticky="ns")
        
        # Sección para agregar clientes
        marco_agregar = ttk.LabelFrame(panel_izquierdo, text="Agregar Nuevo Cliente")
        marco_agregar.pack(padx=10, pady=10, fill=tk.X)
        
        ttk.Label(marco_agregar, text="Categoría:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.combo_categorias = ttk.Combobox(marco_agregar, state="readonly")
        self.combo_categorias.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(marco_agregar, text="Nombre:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.entrada_nombre = ttk.Entry(marco_agregar)
        self.entrada_nombre.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(marco_agregar, text="Correo:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.entrada_correo = ttk.Entry(marco_agregar)
        self.entrada_correo.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(marco_agregar, text="Teléfono:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.entrada_telefono = ttk.Entry(marco_agregar)
        self.entrada_telefono.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(marco_agregar, text="Contacto:").grid(row=4, column=0, padx=5, pady=5, sticky="e")
        self.entrada_contacto = ttk.Entry(marco_agregar)
        self.entrada_contacto.grid(row=4, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Button(marco_agregar, text="Agregar Cliente", command=self.agregar_cliente).grid(
            row=5, column=1, pady=10, sticky="e")
        
        # Gestión de categorías
        marco_categorias = ttk.LabelFrame(panel_izquierdo, text="Gestión de Categorías")
        marco_categorias.pack(padx=10, pady=10, fill=tk.X)
        
        ttk.Button(marco_categorias, text="Administrar Categorías", 
                 command=self.gestionar_categorias).pack(pady=5, fill=tk.X)
        
        # Panel Derecho
        panel_derecho = ttk.Frame(marco_principal)
        panel_derecho.grid(row=0, column=1, padx=15, pady=15, sticky="nsew")
        
        # Sección de búsqueda
        marco_busqueda = ttk.LabelFrame(panel_derecho, text="Búsqueda")
        marco_busqueda.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Filtro por nombre/contacto
        marco_filtro_nombre = ttk.Frame(marco_busqueda)
        marco_filtro_nombre.pack(fill=tk.X, pady=5)
        
        ttk.Label(marco_filtro_nombre, text="Buscar por Nombre:").pack(side=tk.LEFT)
        self.variable_busqueda = tk.StringVar()
        entrada_busqueda = ttk.Entry(marco_filtro_nombre, textvariable=self.variable_busqueda, width=40)
        entrada_busqueda.pack(side=tk.LEFT, padx=5)
        entrada_busqueda.bind("<KeyRelease>", self.buscar_clientes)

        # Filtro por categoría
        marco_filtro_categoria = ttk.Frame(marco_busqueda)
        marco_filtro_categoria.pack(fill=tk.X, pady=5)
        
        ttk.Label(marco_filtro_categoria, text="Filtrar por Categoría:").pack(side=tk.LEFT)
        self.variable_categoria = tk.StringVar()
        entrada_categoria = ttk.Entry(marco_filtro_categoria, textvariable=self.variable_categoria, width=40)
        entrada_categoria.pack(side=tk.LEFT, padx=5)
        entrada_categoria.bind("<KeyRelease>", self.buscar_clientes)

        # Treeview para mostrar datos
        self.tabla_clientes = ttk.Treeview(marco_busqueda, 
                                     columns=('Nombre', 'Contacto', 'Teléfono', 'Correo', 'Categoría'), 
                                     show='headings')
        self.tabla_clientes.heading('Nombre', text='Nombre')
        self.tabla_clientes.heading('Contacto', text='Contacto')
        self.tabla_clientes.heading('Teléfono', text='Teléfono')
        self.tabla_clientes.heading('Correo', text='Correo')
        self.tabla_clientes.heading('Categoría', text='Categoría')
        
        # Configurar anchos de columnas
        self.tabla_clientes.column('Nombre', width=150)
        self.tabla_clientes.column('Contacto', width=100)
        self.tabla_clientes.column('Teléfono', width=120)
        self.tabla_clientes.column('Correo', width=180)
        self.tabla_clientes.column('Categoría', width=100)
        
        self.tabla_clientes.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(marco_busqueda, orient="vertical", command=self.tabla_clientes.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tabla_clientes.configure(yscrollcommand=scrollbar.set)

        
        # Botones de acción modificados
        marco_botones = ttk.Frame(panel_derecho)
        marco_botones.pack(pady=10, fill=tk.X)
        
        ttk.Button(marco_botones, text="Añadir a Selección", command=self.anadir_seleccion).pack(side=tk.LEFT, padx=5)
        ttk.Button(marco_botones, text="Copiar Correos", command=self.copiar_correos).pack(side=tk.LEFT, padx=5)
        ttk.Button(marco_botones, text="Limpiar Selección", command=self.limpiar_seleccion).pack(side=tk.LEFT, padx=5)
        # ttk.Button(marco_botones, text="Enviar Correo", command=self.abrir_editor_correo).pack(side=tk.LEFT, padx=5)
        ttk.Button(marco_botones, text="Modificar Cliente", command=self.modificar_cliente).pack(side=tk.LEFT, padx=5)
        ttk.Button(marco_botones, text="Copiar Correos Categoría", 
                 command=self.copiar_correos_categoria).pack(side=tk.RIGHT, padx=5)
        
        marco_principal.grid_columnconfigure(1, weight=1)
        marco_principal.grid_rowconfigure(0, weight=1)

    def cargar_categorias(self):
        """Cargar categorías desde la base de datos"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id, nombre FROM categorias")
            self.categorias = cursor.fetchall()
            self.combo_categorias['values'] = [cat[1] for cat in self.categorias]
            if self.categorias:
                self.combo_categorias.current(0)
        except Exception as e:
            messagebox.showerror("Error de Base de Datos", f"Error al cargar categorías: {e}")

    def gestionar_categorias(self):
        """Abrir ventana de gestión de categorías"""
        dialogo = tk.Toplevel(self.root)
        dialogo.title("Administrar Categorías")
        
        marco_entrada = ttk.Frame(dialogo)
        marco_entrada.pack(padx=10, pady=10, fill=tk.X)
        
        variable_nueva_cat = tk.StringVar()
        ttk.Entry(marco_entrada, textvariable=variable_nueva_cat).pack(side=tk.LEFT, padx=5)
        ttk.Button(marco_entrada, text="Agregar Categoría", 
                 command=lambda: self.agregar_categoria(variable_nueva_cat.get(), dialogo)).pack(side=tk.LEFT)
        
        marco_lista = ttk.Frame(dialogo)
        marco_lista.pack(padx=10, pady=10, fill=tk.BOTH)
        
        self.lista_categorias = tk.Listbox(marco_lista, height=8)
        self.lista_categorias.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        for cat in self.categorias:
            self.lista_categorias.insert(tk.END, cat[1])
        
        marco_botones = ttk.Frame(marco_lista)
        marco_botones.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(marco_botones, text="Eliminar Categoría", 
                 command=lambda: self.eliminar_categoria(dialogo)).pack(pady=5)

    def eliminar_categoria(self, dialogo):
        """Eliminar categoría seleccionada"""
        seleccionado = self.lista_categorias.curselection()
        if not seleccionado:
            messagebox.showwarning("Advertencia", "Seleccione una categoría para eliminar")
            return
            
        nombre_categoria = self.lista_categorias.get(seleccionado)
        if nombre_categoria == "Clientes":
            messagebox.showerror("Error", "No se puede eliminar la categoría por defecto")
            return
            
        confirmacion = messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Está seguro de eliminar la categoría '{nombre_categoria}'?\n"
            "Los clientes serán movidos a la categoría por defecto."
        )
        if not confirmacion:
            return
            
        try:
            cursor = self.conn.cursor()
            
            # Obtener ID de la categoría a eliminar
            cursor.execute("SELECT id FROM categorias WHERE nombre = ?", (nombre_categoria,))
            categoria_id = cursor.fetchone()[0]
            
            # Mover clientes a categoría por defecto
            cursor.execute("UPDATE clientes SET categoria_id = 1 WHERE categoria_id = ?", (categoria_id,))
            
            # Eliminar categoría
            cursor.execute("DELETE FROM categorias WHERE id = ?", (categoria_id,))
            
            self.conn.commit()
            
            # Actualizar interfaz
            self.cargar_categorias()
            self.lista_categorias.delete(seleccionado)
            self.buscar_clientes()
            
            messagebox.showinfo("Éxito", f"Categoría '{nombre_categoria}' eliminada correctamente")
            
        except Exception as e:
            self.conn.rollback()
            messagebox.showerror("Error", f"No se pudo eliminar la categoría: {str(e)}")
        
    def agregar_categoria(self, nombre, dialogo):
        """Agregar nueva categoría a la base de datos"""
        if not nombre:
            messagebox.showwarning("Error de Entrada", "¡El nombre de la categoría no puede estar vacío!")
            return
            
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO categorias (nombre) VALUES (?)", (nombre,))
            self.conn.commit()
            self.cargar_categorias()
            dialogo.destroy()
            messagebox.showinfo("Éxito", "¡Categoría agregada correctamente!")
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "¡La categoría ya existe!")
        except Exception as e:
            messagebox.showerror("Error de Base de Datos", f"Error al agregar categoría: {e}")

    def agregar_cliente(self):
        """Agregar un nuevo cliente a la base de datos"""
        nombre = self.entrada_nombre.get().strip()
        correo = self.entrada_correo.get().strip()
        telefono = self.entrada_telefono.get().strip()
        contacto = self.entrada_contacto.get().strip()
        categoria = self.combo_categorias.get()
        
        if not all([nombre, correo, telefono, contacto, categoria]):
            messagebox.showwarning("Error de Entrada", "¡Todos los campos son obligatorios!")
            return
            
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id FROM categorias WHERE nombre = ?", (categoria,))
            categoria_id = cursor.fetchone()[0]
            
            cursor.execute(
                """INSERT INTO clientes 
                (nombre, correo, telefono, contacto, categoria_id) 
                VALUES (?, ?, ?, ?, ?)""",
                (nombre, correo, telefono, contacto, categoria_id))
            self.conn.commit()
            messagebox.showinfo("Éxito", "¡Cliente agregado correctamente!")
            self.limpiar_campos()
            self.buscar_clientes()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "¡El correo electrónico ya existe en la base de datos!")
        except Exception as e:
            messagebox.showerror("Error de Base de Datos", f"Error al agregar cliente: {e}")

    def limpiar_campos(self):
        """Limpiar campos de entrada"""
        self.entrada_nombre.delete(0, tk.END)
        self.entrada_correo.delete(0, tk.END)
        self.entrada_telefono.delete(0, tk.END)
        self.entrada_contacto.delete(0, tk.END)


    def anadir_seleccion(self):
        """Añadir clientes seleccionados a la selección persistente"""
        correos_actuales = self.obtener_correos_seleccionados()
        self.seleccion_persistente.update(correos_actuales)
        messagebox.showinfo("Éxito", f"Se añadieron {len(correos_actuales)} correos a la selección")

    def limpiar_seleccion(self):
        """Limpiar la selección persistente"""
        self.seleccion_persistente.clear()
        messagebox.showinfo("Información", "Selección limpiada correctamente")

    def copiar_correos(self):
        """Copiar correos de la selección persistente"""
        if self.seleccion_persistente:
            pyperclip.copy(", ".join(self.seleccion_persistente))
            messagebox.showinfo("Éxito", f"¡{len(self.seleccion_persistente)} correos copiados!")
        else:
            messagebox.showwarning("Advertencia", "No hay correos seleccionados")

    def buscar_clientes(self, event=None):
        """Buscar clientes con múltiples filtros"""
        termino_nombre = self.variable_busqueda.get().strip()
        termino_categoria = self.variable_categoria.get().strip()
        
        try:
            cursor = self.conn.cursor()
            query = """
                SELECT c.nombre, c.contacto, c.telefono, c.correo, cat.nombre 
                FROM clientes c
                JOIN categorias cat ON c.categoria_id = cat.id
                WHERE (c.nombre LIKE ? OR c.contacto LIKE ?)
                AND cat.nombre LIKE ?
            """
            params = (
                f"%{termino_nombre}%",
                f"%{termino_nombre}%",
                f"%{termino_categoria}%"
            )
            
            cursor.execute(query, params)
            
            self.tabla_clientes.delete(*self.tabla_clientes.get_children())
            
            # Resaltar selecciones persistentes
            for cliente in cursor.fetchall():
                item = self.tabla_clientes.insert('', tk.END, values=cliente)
                if cliente[3] in self.seleccion_persistente:
                    self.tabla_clientes.item(item, tags=('selected',))
            
            self.tabla_clientes.tag_configure('selected', background='#b0e0e6')
            
        except Exception as e:
            messagebox.showerror("Error de Base de Datos", f"Error en la búsqueda: {e}")

    
    def obtener_correos_seleccionados(self):
        """Obtener correos de clientes seleccionados"""
        seleccionados = self.tabla_clientes.selection()
        return [self.tabla_clientes.item(item)['values'][3] for item in seleccionados]



    def modificar_cliente(self):
        """Modificar datos del cliente seleccionado"""
        seleccionado = self.tabla_clientes.selection()
        if not seleccionado:
            messagebox.showwarning("Advertencia", "Ningún cliente seleccionado")
            return
            
        valores_cliente = self.tabla_clientes.item(seleccionado[0])['values']
        cliente_id = self.obtener_id_cliente(valores_cliente[3])
        self.abrir_dialogo_modificacion(cliente_id, valores_cliente)

    def obtener_id_cliente(self, correo):
        """Obtener ID del cliente desde su correo"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM clientes WHERE correo = ?", (correo,))
        return cursor.fetchone()[0]

    def abrir_dialogo_modificacion(self, cliente_id, valores_cliente):
        """Abrir diálogo de modificación de cliente"""
        dialogo = tk.Toplevel(self.root)
        dialogo.title("Modificar Cliente")
        
        # Obtener categorías actuales
        cursor = self.conn.cursor()
        cursor.execute("SELECT nombre FROM categorias")
        categorias = [fila[0] for fila in cursor.fetchall()]
        
        ttk.Label(dialogo, text="Categoría:").grid(row=0, column=0, padx=10, pady=10)
        combo_categorias = ttk.Combobox(dialogo, values=categorias, state="readonly")
        combo_categorias.grid(row=0, column=1, padx=10, pady=10)
        combo_categorias.set(valores_cliente[4])
        
        ttk.Label(dialogo, text="Nombre:").grid(row=1, column=0, padx=10, pady=10)
        entrada_nombre = ttk.Entry(dialogo, width=35)
        entrada_nombre.grid(row=1, column=1, padx=10, pady=10)
        entrada_nombre.insert(0, valores_cliente[0])
        
        ttk.Label(dialogo, text="Correo:").grid(row=2, column=0, padx=10, pady=10)
        entrada_correo = ttk.Entry(dialogo, width=35)
        entrada_correo.grid(row=2, column=1, padx=10, pady=10)
        entrada_correo.insert(0, valores_cliente[3])
        
        ttk.Label(dialogo, text="Teléfono:").grid(row=3, column=0, padx=10, pady=10)
        entrada_telefono = ttk.Entry(dialogo, width=35)
        entrada_telefono.grid(row=3, column=1, padx=10, pady=10)
        entrada_telefono.insert(0, valores_cliente[2])
        
        ttk.Label(dialogo, text="Contacto:").grid(row=4, column=0, padx=10, pady=10)
        entrada_contacto = ttk.Entry(dialogo, width=35)
        entrada_contacto.grid(row=4, column=1, padx=10, pady=10)
        entrada_contacto.insert(0, valores_cliente[1])
        
        def guardar_cambios():
            nuevo_nombre = entrada_nombre.get().strip()
            nuevo_correo = entrada_correo.get().strip()
            nuevo_telefono = entrada_telefono.get().strip()
            nuevo_contacto = entrada_contacto.get().strip()
            nueva_categoria = combo_categorias.get()
            
            if not all([nuevo_nombre, nuevo_correo, nuevo_telefono, nuevo_contacto, nueva_categoria]):
                messagebox.showwarning("Error de Entrada", "¡Todos los campos son obligatorios!")
                return
                
            try:
                cursor = self.conn.cursor()
                cursor.execute("SELECT id FROM categorias WHERE nombre = ?", (nueva_categoria,))
                categoria_id = cursor.fetchone()[0]
                
                cursor.execute("""
                    UPDATE clientes 
                    SET nombre=?, correo=?, telefono=?, contacto=?, categoria_id=?
                    WHERE id=?
                """, (nuevo_nombre, nuevo_correo, nuevo_telefono, nuevo_contacto, categoria_id, cliente_id))
                self.conn.commit()
                messagebox.showinfo("Éxito", "¡Cliente actualizado correctamente!")
                dialogo.destroy()
                self.buscar_clientes()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "¡El correo electrónico ya existe en la base de datos!")
            except Exception as e:
                messagebox.showerror("Error de Base de Datos", f"Error al actualizar: {e}")
        
        ttk.Button(dialogo, text="Guardar Cambios", command=guardar_cambios).grid(
            row=5, column=1, pady=15, sticky="e")

    def copiar_correos_categoria(self):
        """Copiar todos los correos de la categoría seleccionada"""
        categoria_seleccionada = self.combo_categorias.get()
        if not categoria_seleccionada:
            messagebox.showwarning("Advertencia", "¡Ninguna categoría seleccionada!")
            return
            
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT correo FROM clientes 
                WHERE categoria_id = (
                    SELECT id FROM categorias WHERE nombre = ?
                )
            """, (categoria_seleccionada,))
            correos = [fila[0] for fila in cursor.fetchall()]
            
            if correos:
                pyperclip.copy(", ".join(correos))
                messagebox.showinfo("Éxito", 
                    f"¡{len(correos)} correos copiados de {categoria_seleccionada}!")
            else:
                messagebox.showinfo("Información", f"No hay clientes en {categoria_seleccionada}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al copiar correos: {e}")

    def abrir_editor_correo(self):
        """Abrir editor de correo electrónico"""
        correos = self.obtener_correos_seleccionados()
        if not correos:
            messagebox.showwarning("Advertencia", "Ningún cliente seleccionado")
            return
            
        dialogo = tk.Toplevel(self.root)
        dialogo.title("Redactar Correo")
        
        ttk.Label(dialogo, text="Servidor SMTP:").grid(row=0, column=0, padx=5, pady=5)
        entrada_servidor = ttk.Entry(dialogo)
        entrada_servidor.grid(row=0, column=1, padx=5, pady=5)
        entrada_servidor.insert(0, "smtp.gmail.com")
        
        ttk.Label(dialogo, text="Puerto SMTP:").grid(row=1, column=0, padx=5, pady=5)
        entrada_puerto = ttk.Entry(dialogo)
        entrada_puerto.grid(row=1, column=1, padx=5, pady=5)
        entrada_puerto.insert(0, "587")
        
        ttk.Label(dialogo, text="Tu Correo:").grid(row=2, column=0, padx=5, pady=5)
        entrada_emisor = ttk.Entry(dialogo)
        entrada_emisor.grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(dialogo, text="Contraseña:").grid(row=3, column=0, padx=5, pady=5)
        entrada_password = ttk.Entry(dialogo, show="*")
        entrada_password.grid(row=3, column=1, padx=5, pady=5)
        
        ttk.Label(dialogo, text="Asunto:").grid(row=4, column=0, padx=5, pady=5)
        entrada_asunto = ttk.Entry(dialogo)
        entrada_asunto.grid(row=4, column=1, padx=5, pady=5)
        
        ttk.Label(dialogo, text="Mensaje:").grid(row=5, column=0, padx=5, pady=5)
        cuerpo = tk.Text(dialogo, height=10, width=40)
        cuerpo.grid(row=5, column=1, padx=5, pady=5)
        
        def enviar_correos():
            try:
                mensaje = MIMEText(cuerpo.get("1.0", tk.END))
                mensaje['Subject'] = entrada_asunto.get()
                mensaje['From'] = entrada_emisor.get()
                mensaje['To'] = ", ".join(correos)
                mensaje['Date'] = formatdate(localtime=True)
                
                with smtplib.SMTP(entrada_servidor.get(), int(entrada_puerto.get())) as servidor:
                    servidor.starttls()
                    servidor.login(entrada_emisor.get(), entrada_password.get())
                    servidor.sendmail(entrada_emisor.get(), correos, mensaje.as_string())
                
                messagebox.showinfo("Éxito", "¡Correos enviados correctamente!")
                dialogo.destroy()
            except Exception as e:
                messagebox.showerror("Error de Correo", f"Error al enviar correos: {e}")
        
        ttk.Button(dialogo, text="Enviar", command=enviar_correos).grid(row=6, column=1, pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = ClientDatabaseApp(root)
    root.mainloop()


