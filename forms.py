import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from db_config import get_connection

class ProductComponentForm:
    """Форма для работы с изделиями и их комплектующими (связь 1:М)"""
    
    def __init__(self, parent):
        self.parent = parent
        self.current_product_id = None
        
        self.create_widgets()
        self.load_products()
    
    def create_widgets(self):
        # Левая панель - список изделий
        left_frame = ttk.LabelFrame(self.parent, text="Изделия", width=350)
        left_frame.pack(side='left', fill='both', expand=False, padx=5, pady=5)
        
        # Кнопки управления изделиями
        product_btn_frame = ttk.Frame(left_frame)
        product_btn_frame.pack(fill='x', padx=5, pady=5)
        ttk.Button(product_btn_frame, text="➕ Добавить изделие", command=self.add_product).pack(side='left', padx=2)
        ttk.Button(product_btn_frame, text="🗑 Удалить изделие", command=self.delete_product).pack(side='left', padx=2)
        
        # Поиск по изделиям
        ttk.Label(left_frame, text="Поиск:").pack(anchor='w', padx=5)
        self.product_search = ttk.Entry(left_frame)
        self.product_search.pack(fill='x', padx=5, pady=2)
        ttk.Button(left_frame, text="Найти", command=self.search_products).pack(pady=2)
        
        # Список изделий
        self.product_tree = ttk.Treeview(left_frame, columns=('id', 'name', 'price'), show='headings', height=15)
        self.product_tree.heading('id', text='ID')
        self.product_tree.heading('name', text='Название')
        self.product_tree.heading('price', text='Цена')
        self.product_tree.column('id', width=40)
        self.product_tree.column('name', width=180)
        self.product_tree.column('price', width=80)
        self.product_tree.pack(fill='both', expand=True, padx=5, pady=5)
        self.product_tree.bind('<<TreeviewSelect>>', self.on_product_select)
        
        # Правая панель - комплектующие
        right_frame = ttk.LabelFrame(self.parent, text="Комплектующие изделия", width=500)
        right_frame.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        
        # Кнопки для комплектующих
        comp_btn_frame = ttk.Frame(right_frame)
        comp_btn_frame.pack(fill='x', padx=5, pady=5)
        ttk.Button(comp_btn_frame, text="➕ Добавить комплектующее", command=self.add_component).pack(side='left', padx=2)
        ttk.Button(comp_btn_frame, text="✏️ Изменить количество", command=self.edit_component).pack(side='left', padx=2)
        ttk.Button(comp_btn_frame, text="🗑 Удалить комплектующее", command=self.delete_component).pack(side='left', padx=2)
        ttk.Button(comp_btn_frame, text="🔄 Обновить", command=self.refresh_components).pack(side='left', padx=2)
        
        # Таблица комплектующих
        self.comp_tree = ttk.Treeview(right_frame, columns=('name', 'qty', 'price', 'total'), show='headings')
        self.comp_tree.heading('name', text='Комплектующее')
        self.comp_tree.heading('qty', text='Кол-во')
        self.comp_tree.heading('price', text='Цена за шт')
        self.comp_tree.heading('total', text='Сумма')
        self.comp_tree.column('name', width=200)
        self.comp_tree.column('qty', width=80)
        self.comp_tree.column('price', width=100)
        self.comp_tree.column('total', width=100)
        self.comp_tree.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Итоговая информация
        self.total_label = ttk.Label(right_frame, text="Общая себестоимость комплектующих: 0 руб.", font=('Arial', 10, 'bold'))
        self.total_label.pack(anchor='e', padx=10, pady=10)
    
    def load_products(self, search=None):
        """Загружает список изделий"""
        conn = get_connection()
        if not conn:
            messagebox.showerror("Ошибка", "Нет подключения к базе данных")
            return
        cur = conn.cursor()
        try:
            query = "SELECT prod_id, prod_name, selling_price FROM products"
            if search:
                query += f" WHERE prod_name ILIKE '%%{search}%%'"
            query += " ORDER BY prod_id"
            cur.execute(query)
            rows = cur.fetchall()
            self.product_tree.delete(*self.product_tree.get_children())
            for row in rows:
                self.product_tree.insert('', 'end', values=row)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка загрузки изделий: {e}")
        finally:
            cur.close()
            conn.close()
    
    def search_products(self):
        self.load_products(self.product_search.get())
    
    def on_product_select(self, event):
        """Выбор изделия"""
        selected = self.product_tree.selection()
        if not selected:
            return
        self.current_product_id = self.product_tree.item(selected[0])['values'][0]
        self.load_components()
    
    def load_components(self):
        """Загружает комплектующие для выбранного изделия"""
        if not self.current_product_id:
            return
        
        conn = get_connection()
        if not conn:
            return
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT c.comp_name, pc.qty_required, c.unit_price, 
                       (pc.qty_required * c.unit_price) as total
                FROM product_components pc
                JOIN components c ON pc.comp_id = c.comp_id
                WHERE pc.prod_id = %s
                ORDER BY c.comp_name
            """, (self.current_product_id,))
            rows = cur.fetchall()
            
            self.comp_tree.delete(*self.comp_tree.get_children())
            total_sum = 0
            for row in rows:
                self.comp_tree.insert('', 'end', values=row)
                total_sum += row[3]
            self.total_label.config(text=f"Общая себестоимость комплектующих: {total_sum:.2f} руб.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка загрузки комплектующих: {e}")
        finally:
            cur.close()
            conn.close()
    
    def refresh_components(self):
        """Обновляет список комплектующих"""
        self.load_components()
    
    def add_product(self):
        """Добавление нового изделия"""
        dialog = tk.Toplevel(self.parent)
        dialog.title("Добавление изделия")
        dialog.geometry("300x200")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Название изделия:").pack(pady=(20,5))
        name_entry = ttk.Entry(dialog, width=30)
        name_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Цена продажи (руб):").pack(pady=5)
        price_entry = ttk.Entry(dialog, width=30)
        price_entry.pack(pady=5)
        
        def save():
            name = name_entry.get().strip()
            price_str = price_entry.get().strip()
            
            if not name:
                messagebox.showerror("Ошибка", "Введите название изделия")
                return
            if not price_str:
                messagebox.showerror("Ошибка", "Введите цену")
                return
            
            try:
                price = float(price_str)
            except ValueError:
                messagebox.showerror("Ошибка", "Цена должна быть числом")
                return
            
            conn = get_connection()
            if not conn:
                return
            
            cur = conn.cursor()
            cur.execute("SELECT COALESCE(MAX(prod_id), 0) + 1 FROM products")
            new_id = cur.fetchone()[0]
            
            try:
                cur.execute("INSERT INTO products (prod_id, prod_name, selling_price) VALUES (%s, %s, %s)",
                            (new_id, name, price))
                conn.commit()
                messagebox.showinfo("Успех", f"Изделие '{name}' добавлено с ID={new_id}")
                dialog.destroy()
                self.load_products()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось добавить изделие:\n{e}")
            finally:
                cur.close()
                conn.close()
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="Сохранить", command=save).pack(side='left', padx=10)
        ttk.Button(btn_frame, text="Отмена", command=dialog.destroy).pack(side='left', padx=10)
    
    def delete_product(self):
        """Удаление изделия"""
        if not self.current_product_id:
            messagebox.showerror("Ошибка", "Выберите изделие")
            return
        
        if messagebox.askyesno("Подтверждение", f"Удалить изделие ID={self.current_product_id} и все его комплектующие?"):
            conn = get_connection()
            if not conn:
                return
            cur = conn.cursor()
            try:
                cur.execute("DELETE FROM products WHERE prod_id = %s", (self.current_product_id,))
                conn.commit()
                messagebox.showinfo("Успех", "Изделие удалено")
                self.current_product_id = None
                self.load_products()
                self.comp_tree.delete(*self.comp_tree.get_children())
                self.total_label.config(text="Общая себестоимость комплектующих: 0 руб.")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить изделие:\n{e}")
            finally:
                cur.close()
                conn.close()
    
    def add_component(self):
        """Добавление комплектующего к изделию"""
        if not self.current_product_id:
            messagebox.showerror("Ошибка", "Сначала выберите изделие")
            return
        
        # Получаем список комплектующих
        conn = get_connection()
        if not conn:
            return
        
        cur = conn.cursor()
        try:
            cur.execute("SELECT comp_id, comp_name, unit_price FROM components ORDER BY comp_name")
            components = cur.fetchall()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка загрузки комплектующих: {e}")
            cur.close()
            conn.close()
            return
        cur.close()
        
        if not components:
            messagebox.showwarning("Внимание", "Нет доступных комплектующих. Сначала добавьте комплектующие на вкладке 'Комплектующие'")
            conn.close()
            return
        
        # Создаем диалог выбора
        dialog = tk.Toplevel(self.parent)
        dialog.title("Выбор комплектующего")
        dialog.geometry("450x400")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Выберите комплектующее:", font=('Arial', 10, 'bold')).pack(pady=10)
        
        # Список комплектующих
        listbox = tk.Listbox(dialog, height=10, width=50)
        listbox.pack(padx=10, pady=5, fill='both', expand=True)
        
        for c in components:
            listbox.insert('end', f"ID:{c[0]} | {c[1]} | Цена: {c[2]} руб.")
        
        ttk.Label(dialog, text="Количество:").pack(pady=(10,0))
        qty_entry = ttk.Entry(dialog, width=20)
        qty_entry.insert(0, "1")
        qty_entry.pack(pady=5)
        
        def confirm():
            selection = listbox.curselection()
            if not selection:
                messagebox.showerror("Ошибка", "Выберите комплектующее")
                return
            
            comp_id = components[selection[0]][0]
            comp_name = components[selection[0]][1]
            
            qty_str = qty_entry.get().strip()
            if not qty_str:
                messagebox.showerror("Ошибка", "Введите количество")
                return
            
            try:
                qty = float(qty_str)
            except ValueError:
                messagebox.showerror("Ошибка", "Количество должно быть числом")
                return
            
            # Проверяем, нет ли уже такого комплектующего у изделия
            cur2 = conn.cursor()
            cur2.execute("SELECT 1 FROM product_components WHERE prod_id = %s AND comp_id = %s",
                         (self.current_product_id, comp_id))
            exists = cur2.fetchone()
            cur2.close()
            
            if exists:
                messagebox.showerror("Ошибка", f"Комплектующее '{comp_name}' уже добавлено к этому изделию!\nИспользуйте 'Изменить количество' для изменения.")
                return
            
            # Добавляем связь
            cur2 = conn.cursor()
            try:
                cur2.execute("INSERT INTO product_components (prod_id, comp_id, qty_required) VALUES (%s, %s, %s)",
                            (self.current_product_id, comp_id, qty))
                conn.commit()
                messagebox.showinfo("Успех", f"Комплектующее '{comp_name}' добавлено к изделию")
                dialog.destroy()
                self.load_components()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось добавить комплектующее:\n{e}")
            finally:
                cur2.close()
                conn.close()
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="✅ Добавить", command=confirm, width=15).pack(side='left', padx=10)
        ttk.Button(btn_frame, text="❌ Отмена", command=dialog.destroy, width=15).pack(side='left', padx=10)
    
    def edit_component(self):
        """Изменение количества комплектующего"""
        selected = self.comp_tree.selection()
        if not selected:
            messagebox.showerror("Ошибка", "Выберите комплектующее")
            return
        
        old_qty = self.comp_tree.item(selected[0])['values'][1]
        comp_name = self.comp_tree.item(selected[0])['values'][0]
        
        new_qty = simpledialog.askfloat("Изменение", f"Новое количество для '{comp_name}':", initialvalue=old_qty)
        if new_qty is None:
            return
        
        conn = get_connection()
        if not conn:
            return
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE product_components 
                SET qty_required = %s 
                WHERE prod_id = %s AND comp_id = (SELECT comp_id FROM components WHERE comp_name = %s)
            """, (new_qty, self.current_product_id, comp_name))
            conn.commit()
            messagebox.showinfo("Успех", "Количество изменено")
            self.load_components()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось изменить количество:\n{e}")
        finally:
            cur.close()
            conn.close()
    
    def delete_component(self):
        """Удаление комплектующего из состава изделия"""
        selected = self.comp_tree.selection()
        if not selected:
            messagebox.showerror("Ошибка", "Выберите комплектующее")
            return
        
        comp_name = self.comp_tree.item(selected[0])['values'][0]
        
        if not messagebox.askyesno("Подтверждение", f"Удалить комплектующее '{comp_name}' из состава изделия?"):
            return
        
        conn = get_connection()
        if not conn:
            return
        cur = conn.cursor()
        try:
            cur.execute("""
                DELETE FROM product_components 
                WHERE prod_id = %s AND comp_id = (SELECT comp_id FROM components WHERE comp_name = %s)
            """, (self.current_product_id, comp_name))
            conn.commit()
            messagebox.showinfo("Успех", "Комплектующее удалено")
            self.load_components()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось удалить комплектующее:\n{e}")
        finally:
            cur.close()
            conn.close()
