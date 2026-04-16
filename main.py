import tkinter as tk
from tkinter import ttk
from db_config import get_connection
from tables import TableManager
from forms import ProductComponentForm
from reports import ReportsView

class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Система управления производством мебели")
        self.root.geometry("1200x700")
        
        # Создаем вкладки
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True)
        
        # 1. Вкладка "Изделия"
        products_frame = ttk.Frame(self.notebook)
        self.notebook.add(products_frame, text="📦 Изделия")
        TableManager(products_frame, "products", 
                     columns=['prod_id', 'prod_name', 'selling_price'],
                     display_columns=['ID', 'Название', 'Цена'],
                     pk_column='prod_id')
        
        # 2. Вкладка "Комплектующие"
        components_frame = ttk.Frame(self.notebook)
        self.notebook.add(components_frame, text="🔧 Комплектующие")
        TableManager(components_frame, "components",
                     columns=['comp_id', 'comp_name', 'unit_price'],
                     display_columns=['ID', 'Название', 'Цена'],
                     pk_column='comp_id')
        
        # 3. Вкладка "Материалы"
        materials_frame = ttk.Frame(self.notebook)
        self.notebook.add(materials_frame, text="📐 Материалы")
        TableManager(materials_frame, "materials",
                     columns=['mat_id', 'mat_name', 'unit_price'],
                     display_columns=['ID', 'Название', 'Цена'],
                     pk_column='mat_id')
        
        # 4. Вкладка "Технологические операции"
        techops_frame = ttk.Frame(self.notebook)
        self.notebook.add(techops_frame, text="⚙️ Тех. операции")
        TableManager(techops_frame, "tech_ops",
                     columns=['op_id', 'op_name', 'hours_per_unit', 'cost_per_hour'],
                     display_columns=['ID', 'Операция', 'Часы', 'Цена/час'],
                     pk_column='op_id')
        
        # 5. Вкладка "Форма 1:М (Изделие + Комплектующие)"
        form_frame = ttk.Frame(self.notebook)
        self.notebook.add(form_frame, text="🔗 Изделие → Комплектующие")
        ProductComponentForm(form_frame)
        
        # 6. Вкладка "Отчеты"
        reports_frame = ttk.Frame(self.notebook)
        self.notebook.add(reports_frame, text="📊 Отчеты")
        ReportsView(reports_frame)
        
        # Статусбар
        self.statusbar = ttk.Label(root, text="Готово", relief='sunken', anchor='w')
        self.statusbar.pack(side='bottom', fill='x')
        
        # Проверка подключения к БД
        self.check_connection()
    
    def check_connection(self):
        conn = get_connection()
        if conn:
            self.statusbar.config(text="✅ Подключено к базе данных furniture_db")
            conn.close()
        else:
            self.statusbar.config(text="❌ Ошибка подключения к базе данных")

if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()
