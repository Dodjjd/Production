# -*- coding: utf-8 -*-
import psycopg2

try:
    conn = psycopg2.connect(
        host="localhost",
        port="5432",
        database="furniture_db",
        user="postgres",
        password="postgres",
        client_encoding="UTF8"
    )
    print("OK - Подключено!")
    
    cur = conn.cursor()
    cur.execute("SELECT 1")
    print("OK - Запрос выполнен")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
