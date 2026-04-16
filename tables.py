import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from db_config import get_connection

class TableManager:
    """Универсальный класс для работы с любой таблицей"""
    
    def __init__(self, parent, table_name, columns, display_columns, pk_column=None):
        self.parent = parent
        self.table_name = table_name
        self.columns = columns
        self.display_columns = display_columns
        self.pk_column = pk_column if pk_column else columns[0]
        self.current_page = 0
        self.page_size = 50  # ИЗМЕНЕНО С 20 НА 50
        self.filter_column = ""
        self.filter_value = ""
        self.sort_column = ""
        self.sort_order = "ASC"
        self.search_value = ""
        
        self.create_widgets()
        self.load_data()
    
    def create_widgets(self):
        # Верхняя панель с поиском, фильтром и сортировкой
        top_frame = ttk.Frame(self.parent)
        top_frame.pack(fill='x', padx=5, pady=5)
        
        # Поиск
        ttk.Label(top_frame, text="Поиск:").pack(side='left', padx=(5,0))
        self.search_entry = ttk.Entry(top_frame, width=15)
        self.search_entry.pack(side='left', padx=2)
        ttk.Button(top_frame, text="🔍", width=3, command=self.search).pack(side='left')
        ttk.Button(top_frame, text="✖", width=3, command=self.clear_search).pack(side='left')
        
        # Фильтр
        ttk.Label(top_frame, text="Фильтр поле:").pack(side='left', padx=(10,0))
        self.filter_col_combo = ttk.Combobox(top_frame, values=self.columns, width=12)
        self.filter_col_combo.pack(side='left', padx=2)
        ttk.Label(top_frame, text="значение:").pack(side='left')
        self.filter_val_entry = ttk.Entry(top_frame, width=12)
        self.filter_val_entry.pack(side='left', padx=2)
        ttk.Button(top_frame, text="Фильтр", command=self.apply_filter).pack(side='left')
        ttk.Button(top_frame, text="Сброс", command=self.clear_filter).pack(side='left')
        
        # Сортировка
        ttk.Label(top_frame, text="Сорт. поле:").pack(side='left', padx=(10,0))
        self.sort_col_combo = ttk.Combobox(top_frame, values=self.columns, width=12)
        self.sort_col_combo.pack(side='left', padx=2)
        self.sort_order_var = tk.StringVar(value="ASC")
        ttk.Combobox(top_frame, textvariable=self.sort_order_var, values=["ASC", "DESC"], width=5).pack(side='left')
        ttk.Button(top_frame, text="Сортировать", command=self.apply_sort).pack(side='left')
        
        # Таблица
        tree_frame = ttk.Frame(self.parent)
        tree_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        scroll_y = ttk.Scrollbar(tree_frame, orient='vertical')
        scroll_x = ttk.Scrollbar(tree_frame, orient='horizontal')
        
        self.tree = ttk.Treeview(tree_frame, columns=self.display_columns, show='headings',
                                  yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        scroll_y.config(command=self.tree.yview)
        scroll_x.config(command=self.tree.xview)
        
        scroll_y.pack(side='right', fill='y')
        scroll_x.pack(side='bottom', fill='x')
        self.tree.pack(fill='both', expand=True)
        
        for col in self.display_columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        
        # Кнопки CRUD и пагинации
        btn_frame = ttk.Frame(self.parent)
        btn_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(btn_frame, text="➕ Добавить", command=self.add_record).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="✏️ Изменить", command=self.edit_record).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="🗑 Удалить", command=self.delete_record).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="🔄 Обновить", command=self.load_data).pack(side='left', padx=2)
        
        ttk.Button(btn_frame, text="◀ Пред.", command=self.prev_page).pack(side='right', padx=2)
        self.page_label = ttk.Label(btn_frame, text="Страница 0")
        self.page_label.pack(side='right', padx=5)
        ttk.Button(btn_frame, text="След. ▶", command=self.next_page).pack(side='right', padx=2)
    
    def get_next_id(self):
        """Получает следующий доступный ID для первичного ключа"""
        conn = get_connection()
        if not conn:
            return 1
        cur = conn.cursor()
        cur.execute(f"SELECT COALESCE(MAX({self.pk_column}), 0) + 1 FROM {self.table_name}")
        next_id = cur.fetchone()[0]
        cur.close()
        conn.close()
        return next_id
    
    def get_query(self):
        query = f"SELECT {', '.join(self.columns)} FROM {self.table_name} WHERE 1=1"
        
        # Поиск
        if self.search_value:
            search_conditions = []
            for col in self.columns:
                search_conditions.append(f"CAST({col} AS TEXT) ILIKE '%%{self.search_value}%%'")
            query += f" AND ({' OR '.join(search_conditions)})"
        
        # Фильтр
        if self.filter_column and self.filter_value:
            query += f" AND CAST({self.filter_column} AS TEXT) ILIKE '%%{self.filter_value}%%'"
        
        # Сортировка
        if self.sort_column:
            query += f" ORDER BY {self.sort_column} {self.sort_order}"
        else:
            query += f" ORDER BY {self.pk_column}"
        
        # Пагинация
        query += f" LIMIT {self.page_size} OFFSET {self.current_page * self.page_size}"
        
        return query
    
    def get_count_query(self):
        """Возвращает запрос для подсчета общего количества записей"""
        query = f"SELECT COUNT(*) FROM {self.table_name} WHERE 1=1"
        
        if self.search_value:
            search_conditions = []
            for col in self.columns:
                search_conditions.append(f"CAST({col} AS TEXT) ILIKE '%%{self.search_value}%%'")
            query += f" AND ({' OR '.join(search_conditions)})"
        
        if self.filter_column and self.filter_value:
            query += f" AND CAST({self.filter_column} AS TEXT) ILIKE '%%{self.filter_value}%%'"
        
        return query
    
    def load_data(self):
        conn = get_connection()
        if not conn:
            messagebox.showerror("Ошибка", "Нет подключения к базе данных")
            return
        cur = conn.cursor()
        
        try:
            # Получаем данные
            cur.execute(self.get_query())
            rows = cur.fetchall()
            
            # Получаем общее количество для пагинации
            cur.execute(self.get_count_query())
            total = cur.fetchone()[0]
            
            self.tree.delete(*self.tree.get_children())
            for row in rows:
                self.tree.insert('', 'end', values=row)
            
            total_pages = (total + self.page_size - 1) // self.page_size
            self.page_label.config(text=f"Стр. {self.current_page + 1}/{max(1, total_pages)}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка загрузки данных: {e}")
        finally:
            cur.close()
            conn.close()
    
    def search(self):
        self.search_value = self.search_entry.get()
        self.current_page = 0
        self.load_data()
    
    def clear_search(self):
        self.search_entry.delete(0, tk.END)
        self.search_value = ""
        self.current_page = 0
        self.load_data()
    
    def apply_filter(self):
        self.filter_column = self.filter_col_combo.get()
        self.filter_value = self.filter_val_entry.get()
        self.current_page = 0
        self.load_data()
    
    def clear_filter(self):
        self.filter_col_combo.set('')
        self.filter_val_entry.delete(0, tk.END)
        self.filter_column = ""
        self.filter_value = ""
        self.current_page = 0
        self.load_data()
    
    def apply_sort(self):
        self.sort_column = self.sort_col_combo.get()
        self.sort_order = self.sort_order_var.get()
        self.load_data()
    
    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.load_data()
    
    def next_page(self):
        self.current_page += 1
        self.load_data()
    
    def add_record(self):
        """Добавление новой записи с пошаговым диалогом"""
        
        # Создаем отдельное окно для добавления
        dialog = tk.Toplevel(self.parent)
        dialog.title(f"Добавление записи в {self.table_name}")
        dialog.geometry("400x350")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Поля ввода
        entries = []
        values = []
        
        # Русские названия для полей
        ru_names = {
            'prod_id': 'ID изделия',
            'prod_name': 'Название изделия',
            'selling_price': 'Цена продажи (руб)',
            'comp_id': 'ID комплектующего',
            'comp_name': 'Название комплектующего',
            'unit_price': 'Цена (руб)',
            'tech_process_id': 'ID техпроцесса',
            'mat_id': 'ID материала',
            'mat_name': 'Название материала',
            'op_id': 'ID операции',
            'op_name': 'Название операции',
            'hours_per_unit': 'Часы на операцию',
            'cost_per_hour': 'Стоимость часа (руб)',
            'qty_required': 'Количество',
            'sale_date': 'Дата продажи',
            'quantity': 'Количество',
            'discount': 'Скидка (%)'
        }
        
        # Создаем поля для каждого столбца
        for i, col in enumerate(self.columns):
            # Пропускаем автогенерируемые поля
            if col == 'tp_id' or col == 'sale_id':
                continue
            
            field_name = ru_names.get(col, col)
            
            # Если это первичный ключ, показываем автоматический ID
            if col == self.pk_column:
                next_id = self.get_next_id()
                values.append(next_id)
                info_label = ttk.Label(dialog, text=f"{field_name}: {next_id} (автоматически)", font=('Arial', 10, 'bold'))
                info_label.pack(anchor='w', padx=20, pady=(10,0))
                continue
            
            # Создаем рамку для поля
            frame = ttk.Frame(dialog)
            frame.pack(fill='x', padx=20, pady=5)
            
            label = ttk.Label(frame, text=field_name + ":", width=20, anchor='w')
            label.pack(side='left')
            
            # Для числовых полей
            if col in ['selling_price', 'unit_price', 'hours_per_unit', 'cost_per_hour', 
                       'qty_required', 'quantity', 'discount', 'mat_qty']:
                entry = ttk.Entry(frame)
                entry.pack(side='left', fill='x', expand=True)
            # Для даты
            elif col == 'sale_date':
                entry = ttk.Entry(frame)
                entry.insert(0, "2025-01-01")
                entry.pack(side='left', fill='x', expand=True)
            # Для текстовых полей
            else:
                entry = ttk.Entry(frame)
                entry.pack(side='left', fill='x', expand=True)
            
            entries.append((col, entry))
        
        # Кнопки
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=20)
        
        def save():
            # Собираем значения из полей
            for col, entry in entries:
                val = entry.get().strip()
                if val == "":
                    messagebox.showerror("Ошибка", f"Поле '{ru_names.get(col, col)}' обязательно для заполнения")
                    return
                
                # Преобразование типов
                if col in ['selling_price', 'unit_price', 'hours_per_unit', 'cost_per_hour', 
                           'qty_required', 'quantity', 'discount', 'mat_qty']:
                    try:
                        val = float(val)
                    except ValueError:
                        messagebox.showerror("Ошибка", f"Поле '{ru_names.get(col, col)}' должно быть числом")
                        return
                values.append(val)
            
            # Сохраняем в базу
            conn = get_connection()
            if not conn:
                return
            
            cur = conn.cursor()
            placeholders = ','.join(['%s'] * len(values))
            query = f"INSERT INTO {self.table_name} ({','.join(self.columns[:len(values)])}) VALUES ({placeholders})"
            
            try:
                cur.execute(query, values)
                conn.commit()
                messagebox.showinfo("Успех", "Запись успешно добавлена!")
                dialog.destroy()
                self.load_data()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось добавить запись:\n{str(e)}")
            finally:
                cur.close()
                conn.close()
        
        def cancel():
            dialog.destroy()
        
        ttk.Button(btn_frame, text="✅ Сохранить", command=save, width=15).pack(side='left', padx=10)
        ttk.Button(btn_frame, text="❌ Отмена", command=cancel, width=15).pack(side='left', padx=10)
        
        # Центрируем окно
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        dialog.wait_window()
    
    def edit_record(self):
        """Редактирование выбранной записи"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Ошибка", "Выберите запись для редактирования")
            return
        
        old_values = self.tree.item(selected[0])['values']
        
        # Создаем отдельное окно для редактирования
        dialog = tk.Toplevel(self.parent)
        dialog.title(f"Редактирование записи в {self.table_name}")
        dialog.geometry("400x350")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        entries = []
        new_values = []
        
        ru_names = {
            'prod_id': 'ID изделия',
            'prod_name': 'Название изделия',
            'selling_price': 'Цена продажи (руб)',
            'comp_id': 'ID комплектующего',
            'comp_name': 'Название комплектующего',
            'unit_price': 'Цена (руб)',
            'tech_process_id': 'ID техпроцесса',
            'mat_id': 'ID материала',
            'mat_name': 'Название материала',
            'op_id': 'ID операции',
            'op_name': 'Название операции',
            'hours_per_unit': 'Часы на операцию',
            'cost_per_hour': 'Стоимость часа (руб)',
            'qty_required': 'Количество',
            'sale_date': 'Дата продажи',
            'quantity': 'Количество',
            'discount': 'Скидка (%)'
        }
        
        for i, col in enumerate(self.columns):
            field_name = ru_names.get(col, col)
            
            # ID не редактируем
            if col == self.pk_column:
                info_label = ttk.Label(dialog, text=f"{field_name}: {old_values[i]} (не редактируется)", font=('Arial', 10, 'bold'))
                info_label.pack(anchor='w', padx=20, pady=(10,0))
                new_values.append(old_values[i])
                continue
            
            frame = ttk.Frame(dialog)
            frame.pack(fill='x', padx=20, pady=5)
            
            label = ttk.Label(frame, text=field_name + ":", width=20, anchor='w')
            label.pack(side='left')
            
            entry = ttk.Entry(frame)
            entry.insert(0, str(old_values[i]))
            entry.pack(side='left', fill='x', expand=True)
            entries.append((col, entry))
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=20)
        
        def save():
            for col, entry in entries:
                val = entry.get().strip()
                if val == "":
                    messagebox.showerror("Ошибка", "Все поля должны быть заполнены")
                    return
                
                if col in ['selling_price', 'unit_price', 'hours_per_unit', 'cost_per_hour', 
                           'qty_required', 'quantity', 'discount', 'mat_qty']:
                    try:
                        val = float(val)
                    except ValueError:
                        messagebox.showerror("Ошибка", f"Поле '{ru_names.get(col, col)}' должно быть числом")
                        return
                new_values.append(val)
            
            conn = get_connection()
            if not conn:
                return
            
            cur = conn.cursor()
            set_clause = ','.join([f"{col}=%s" for col, _ in entries])
            query = f"UPDATE {self.table_name} SET {set_clause} WHERE {self.pk_column}=%s"
            
            try:
                cur.execute(query, new_values + [old_values[0]])
                conn.commit()
                messagebox.showinfo("Успех", "Запись успешно изменена!")
                dialog.destroy()
                self.load_data()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось изменить запись:\n{str(e)}")
            finally:
                cur.close()
                conn.close()
        
        ttk.Button(btn_frame, text="✅ Сохранить", command=save, width=15).pack(side='left', padx=10)
        ttk.Button(btn_frame, text="❌ Отмена", command=dialog.destroy, width=15).pack(side='left', padx=10)
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        dialog.wait_window()
    
    def delete_record(self):
        """Удаление выбранной записи"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Ошибка", "Выберите запись для удаления")
            return
        
        pk_value = self.tree.item(selected[0])['values'][0]
        
        if not messagebox.askyesno("Подтверждение", f"Удалить запись с ID = {pk_value}?\nЭто действие нельзя отменить!"):
            return
        
        conn = get_connection()
        if not conn:
            return
        cur = conn.cursor()
        
        try:
            cur.execute(f"DELETE FROM {self.table_name} WHERE {self.pk_column}=%s", (pk_value,))
            conn.commit()
            messagebox.showinfo("Успех", "Запись успешно удалена!")
            self.load_data()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось удалить запись:\n{str(e)}")
        finally:
            cur.close()
            conn.close()
