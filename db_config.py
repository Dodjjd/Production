import psycopg2
import sys
import io

# Принудительно устанавливаем кодировку для вывода
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def get_connection():
    try:
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            database="furniture_db",
            user="postgres",
            password="postgres",  # ваш пароль (даже если с русскими буквами)
            options="-c client_encoding=utf8"  # Явно указываем кодировку
        )
        return conn
    except Exception as e:
        print(f"Ошибка подключения: {e}")
        return None
