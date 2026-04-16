import tkinter as tk
from tkinter import ttk, messagebox
from db_config import get_connection

class ReportsView:
    def __init__(self, parent):
        self.parent = parent
        
        notebook = ttk.Notebook(parent)
        notebook.pack(fill='both', expand=True)
        
        # Отчет 1: Себестоимость всех изделий
        frame1 = ttk.Frame(notebook)
        notebook.add(frame1, text="Себестоимость изделий")
        self.create_cost_report(frame1)
        
        # Отчет 2: Полный техпроцесс изделия (по выбору)
        frame2 = ttk.Frame(notebook)
        notebook.add(frame2, text="Техпроцесс изделия")
        self.create_tech_report(frame2)
        
        # Отчет 3: Прибыль от реализации
        frame3 = ttk.Frame(notebook)
        notebook.add(frame3, text="Прибыль от реализации")
        self.create_profit_report(frame3)
    
    # ==================== ОТЧЕТ 1: СЕБЕСТОИМОСТЬ ====================
    def create_cost_report(self, parent):
        # Панель фильтров
        filter_frame = ttk.LabelFrame(parent, text="Фильтры и сортировка")
        filter_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(filter_frame, text="Фильтр по названию:").grid(row=0, column=0, padx=5, pady=5)
        self.cost_name_filter = ttk.Entry(filter_frame)
        self.cost_name_filter.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(filter_frame, text="Сортировать по:").grid(row=0, column=2, padx=5, pady=5)
        self.cost_sort = ttk.Combobox(filter_frame, values=["названию", "себестоимости", "прибыли"], width=15)
        self.cost_sort.grid(row=0, column=3, padx=5, pady=5)
        self.cost_sort.set("названию")
        
        ttk.Label(filter_frame, text="Порядок:").grid(row=0, column=4, padx=5, pady=5)
        self.cost_order = ttk.Combobox(filter_frame, values=["ASC", "DESC"], width=5)
        self.cost_order.grid(row=0, column=5, padx=5, pady=5)
        self.cost_order.set("ASC")
        
        ttk.Button(filter_frame, text="Сформировать отчет", command=self.run_cost_report).grid(row=1, column=0, columnspan=6, pady=10)
        
        # Таблица для отчета
        self.cost_tree = ttk.Treeview(parent, columns=('name', 'selling_price', 'cost', 'profit'), show='headings')
        self.cost_tree.heading('name', text='Изделие')
        self.cost_tree.heading('selling_price', text='Цена продажи (руб)')
        self.cost_tree.heading('cost', text='Себестоимость (руб)')
        self.cost_tree.heading('profit', text='Прибыль (руб)')
        self.cost_tree.column('name', width=200)
        self.cost_tree.column('selling_price', width=120)
        self.cost_tree.column('cost', width=120)
        self.cost_tree.column('profit', width=120)
        self.cost_tree.pack(fill='both', expand=True, padx=10, pady=10)
    
    def run_cost_report(self):
        conn = get_connection()
        if not conn:
            return
        cur = conn.cursor()
        
        name_filter = self.cost_name_filter.get()
        sort_col = self.cost_sort.get()
        order = self.cost_order.get()
        
        query = """
            SELECT 
                p.prod_name,
                p.selling_price,
                COALESCE(SUM(pc.qty_required * c.unit_price), 0) as total_cost,
                p.selling_price - COALESCE(SUM(pc.qty_required * c.unit_price), 0) as profit
            FROM products p
            LEFT JOIN product_components pc ON p.prod_id = pc.prod_id
            LEFT JOIN components c ON pc.comp_id = c.comp_id
            WHERE 1=1
        """
        
        if name_filter:
            query += f" AND p.prod_name ILIKE '%%{name_filter}%%'"
        
        query += " GROUP BY p.prod_name, p.selling_price"
        
        if sort_col == "названию":
            query += f" ORDER BY p.prod_name {order}"
        elif sort_col == "себестоимости":
            query += f" ORDER BY total_cost {order}"
        elif sort_col == "прибыли":
            query += f" ORDER BY profit {order}"
        
        cur.execute(query)
        rows = cur.fetchall()
        
        self.cost_tree.delete(*self.cost_tree.get_children())
        total_cost_sum = 0
        total_profit_sum = 0
        for row in rows:
            self.cost_tree.insert('', 'end', values=row)
            total_cost_sum += row[2]
            total_profit_sum += row[3]
        
        # Итоговая строка
        self.cost_tree.insert('', 'end', values=('ИТОГО:', '', f"{total_cost_sum:.2f}", f"{total_profit_sum:.2f}"))
        
        cur.close()
        conn.close()
    
    # ==================== ОТЧЕТ 2: ТЕХПРОЦЕСС ИЗДЕЛИЯ ====================
    def create_tech_report(self, parent):
        # Панель выбора изделия
        filter_frame = ttk.LabelFrame(parent, text="Выбор изделия")
        filter_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(filter_frame, text="Выберите изделие:").pack(side='left', padx=5)
        self.tech_product_combo = ttk.Combobox(filter_frame, width=30)
        self.tech_product_combo.pack(side='left', padx=5)
        ttk.Button(filter_frame, text="Сформировать отчет", command=self.run_tech_report).pack(side='left', padx=10)
        
        # Загрузка списка изделий
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT prod_id, prod_name FROM products ORDER BY prod_id")
        products = cur.fetchall()
        self.tech_product_combo['values'] = [f"{p[0]} - {p[1]}" for p in products]
        cur.close()
        conn.close()
        
        # Таблица для отчета
        self.tech_tree = ttk.Treeview(parent, columns=('component', 'op_name', 'material', 'mat_qty', 'hours', 'cost'), show='headings')
        self.tech_tree.heading('component', text='Комплектующее')
        self.tech_tree.heading('op_name', text='Операция')
        self.tech_tree.heading('material', text='Материал')
        self.tech_tree.heading('mat_qty', text='Кол-во мат.')
        self.tech_tree.heading('hours', text='Часы')
        self.tech_tree.heading('cost', text='Стоимость (руб)')
        self.tech_tree.column('component', width=180)
        self.tech_tree.column('op_name', width=120)
        self.tech_tree.column('material', width=120)
        self.tech_tree.column('mat_qty', width=80)
        self.tech_tree.column('hours', width=80)
        self.tech_tree.column('cost', width=100)
        self.tech_tree.pack(fill='both', expand=True, padx=10, pady=10)
    
    def run_tech_report(self):
        if not self.tech_product_combo.get():
            messagebox.showerror("Ошибка", "Выберите изделие")
            return
        
        prod_id = int(self.tech_product_combo.get().split(' - ')[0])
        
        conn = get_connection()
        if not conn:
            return
        cur = conn.cursor()
        
        query = """
            SELECT 
                c.comp_name,
                to2.op_name,
                m.mat_name,
                tp.mat_qty,
                to2.hours_per_unit,
                (tp.mat_qty * m.unit_price + to2.hours_per_unit * to2.cost_per_hour) as operation_cost
            FROM products p
            JOIN product_components pc ON p.prod_id = pc.prod_id
            JOIN components c ON pc.comp_id = c.comp_id
            JOIN tech_process tp ON c.comp_id = tp.comp_id
            JOIN materials m ON tp.mat_id = m.mat_id
            JOIN tech_ops to2 ON tp.op_id = to2.op_id
            WHERE p.prod_id = %s
            ORDER BY c.comp_name, tp.op_sequence
        """
        
        cur.execute(query, (prod_id,))
        rows = cur.fetchall()
        
        self.tech_tree.delete(*self.tech_tree.get_children())
        total_cost = 0
        current_comp = ""
        comp_total = 0
        
        for row in rows:
            self.tech_tree.insert('', 'end', values=row)
            total_cost += row[5]
            comp_total += row[5]
            if current_comp != row[0] and current_comp != "":
                self.tech_tree.insert('', 'end', values=(f"└ {current_comp} ИТОГО:", "", "", "", "", f"{comp_total:.2f}"))
                comp_total = 0
            current_comp = row[0]
        
        if current_comp:
            self.tech_tree.insert('', 'end', values=(f"└ {current_comp} ИТОГО:", "", "", "", "", f"{comp_total:.2f}"))
        
        self.tech_tree.insert('', 'end', values=('='*50, '', '', '', '', ''))
        self.tech_tree.insert('', 'end', values=('ОБЩАЯ СЕБЕСТОИМОСТЬ ИЗДЕЛИЯ:', '', '', '', '', f"{total_cost:.2f}"))
        
        cur.close()
        conn.close()
    
    # ==================== ОТЧЕТ 3: ПРИБЫЛЬ ОТ РЕАЛИЗАЦИИ ====================
    def create_profit_report(self, parent):
        # Панель фильтров
        filter_frame = ttk.LabelFrame(parent, text="Фильтры и сортировка")
        filter_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(filter_frame, text="Мин. прибыль (руб):").grid(row=0, column=0, padx=5, pady=5)
        self.profit_min = ttk.Entry(filter_frame)
        self.profit_min.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(filter_frame, text="Макс. прибыль (руб):").grid(row=0, column=2, padx=5, pady=5)
        self.profit_max = ttk.Entry(filter_frame)
        self.profit_max.grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Label(filter_frame, text="Сортировать по:").grid(row=0, column=4, padx=5, pady=5)
        self.profit_sort = ttk.Combobox(filter_frame, values=["названию", "прибыли", "рентабельности"], width=12)
        self.profit_sort.grid(row=0, column=5, padx=5, pady=5)
        self.profit_sort.set("прибыли")
        
        ttk.Label(filter_frame, text="Порядок:").grid(row=0, column=6, padx=5, pady=5)
        self.profit_order = ttk.Combobox(filter_frame, values=["ASC", "DESC"], width=5)
        self.profit_order.grid(row=0, column=7, padx=5, pady=5)
        self.profit_order.set("DESC")
        
        ttk.Button(filter_frame, text="Сформировать отчет", command=self.run_profit_report).grid(row=1, column=0, columnspan=8, pady=10)
        
        # Таблица для отчета
        self.profit_tree = ttk.Treeview(parent, columns=('name', 'selling_price', 'cost', 'profit', 'profit_percent'), show='headings')
        self.profit_tree.heading('name', text='Изделие')
        self.profit_tree.heading('selling_price', text='Цена (руб)')
        self.profit_tree.heading('cost', text='Себестоимость (руб)')
        self.profit_tree.heading('profit', text='Прибыль (руб)')
        self.profit_tree.heading('profit_percent', text='Рентабельность (%)')
        self.profit_tree.column('name', width=200)
        self.profit_tree.column('selling_price', width=100)
        self.profit_tree.column('cost', width=120)
        self.profit_tree.column('profit', width=100)
        self.profit_tree.column('profit_percent', width=100)
        self.profit_tree.pack(fill='both', expand=True, padx=10, pady=10)
    
    def run_profit_report(self):
        conn = get_connection()
        if not conn:
            return
        cur = conn.cursor()
        
        min_profit = self.profit_min.get()
        max_profit = self.profit_max.get()
        sort_col = self.profit_sort.get()
        order = self.profit_order.get()
        
        query = """
            SELECT 
                p.prod_name,
                p.selling_price,
                COALESCE(SUM(pc.qty_required * c.unit_price), 0) as total_cost,
                p.selling_price - COALESCE(SUM(pc.qty_required * c.unit_price), 0) as profit,
                CASE 
                    WHEN COALESCE(SUM(pc.qty_required * c.unit_price), 0) > 0 
                    THEN ((p.selling_price - COALESCE(SUM(pc.qty_required * c.unit_price), 0)) / 
                          COALESCE(SUM(pc.qty_required * c.unit_price), 0)) * 100
                    ELSE 0
                END as profit_percent
            FROM products p
            LEFT JOIN product_components pc ON p.prod_id = pc.prod_id
            LEFT JOIN components c ON pc.comp_id = c.comp_id
            GROUP BY p.prod_name, p.selling_price
            HAVING 1=1
        """
        
        if min_profit:
            query += f" AND (p.selling_price - COALESCE(SUM(pc.qty_required * c.unit_price), 0)) >= {float(min_profit)}"
        if max_profit:
            query += f" AND (p.selling_price - COALESCE(SUM(pc.qty_required * c.unit_price), 0)) <= {float(max_profit)}"
        
        if sort_col == "названию":
            query += f" ORDER BY p.prod_name {order}"
        elif sort_col == "прибыли":
            query += f" ORDER BY profit {order}"
        elif sort_col == "рентабельности":
            query += f" ORDER BY profit_percent {order}"
        
        cur.execute(query)
        rows = cur.fetchall()
        
        self.profit_tree.delete(*self.profit_tree.get_children())
        total_profit = 0
        for row in rows:
            self.profit_tree.insert('', 'end', values=(row[0], f"{row[1]:.2f}", f"{row[2]:.2f}", f"{row[3]:.2f}", f"{row[4]:.1f}%"))
            total_profit += row[3]
        
        # Итоговая строка
        self.profit_tree.insert('', 'end', values=('ИТОГО:', '', '', f"{total_profit:.2f}", ''))
        
        cur.close()
        conn.close()
