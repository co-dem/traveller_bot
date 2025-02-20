from tkinter import messagebox
from pymysql. cursors import DictCursor
import pymysql

import psycopg2

db_host = "127.0.0.1"
db_user = "postgres"
db_password = "JamSpaceSShooter7774"
db_name = "testDB"

def create_connection():
    try:
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port="5432"
        )
        return conn
    except Exception as e:
        messagebox.showerror("Помилка", "Не вдалося підключитися до бази даних. Перевірте параметри підключення.")
        return None