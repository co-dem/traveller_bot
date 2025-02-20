from config import create_connection
from tkinter import ttk, messagebox, filedialog
import tkinter as tk
import os
import psycopg2  # Заменяем pymysql на psycopg2
import shutil


class CheckTab:
    def __init__(self, parent, main_app):
        self.parent = parent
        self.main_app = main_app
        self.frame = ttk.Frame(self.parent)
        self.frame.pack(fill='both', expand=True, padx=20, pady=20)
        self.connection = create_connection()
        self.create_widgets()

    def create_widgets(self):
        top_frame = ttk.Frame(self.frame)
        top_frame.pack(side='top', fill='x')

        self.refresh_icon = tk.PhotoImage(file='image/button/refresh.png').subsample(25, 25)
        self.refresh_button = ttk.Button(top_frame, text='Оновити дані', image=self.refresh_icon,
                                        command=self.refresh_data,
                                        style='My.TButton', compound=tk.LEFT)
        self.refresh_button.pack(side='left', padx=5)

        self.table_var = tk.StringVar()
        self.tables = self.get_tables()
        self.table_var.set(self.tables[0] if self.tables else "")
        self.table_menu = ttk.OptionMenu(top_frame, self.table_var, *self.tables, command=self.update_table)
        self.table_menu.pack(side='right', padx=5)

        self.tree = ttk.Treeview(self.frame, columns=('#0',), show='tree')
        self.tree.pack(fill='both', expand=True, pady=10)

        self.update_columns(self.table_var.get())

        bottom_frame = ttk.Frame(self.frame)
        bottom_frame.pack(side='bottom', fill='x', pady=5)

        self.buttons_frame = ttk.Frame(bottom_frame)
        self.buttons_frame.pack(fill='x', padx=5)

        self.edit_icon = tk.PhotoImage(file='image/button/edit_icon.png').subsample(30, 30)
        self.edit_button = ttk.Button(self.buttons_frame, text='Редагувати', image=self.edit_icon, compound=tk.LEFT,
                                     style='Edit.TButton', command=self.edit_reservation)
        self.edit_button.pack(side='left', padx=5)

        self.delete_icon = tk.PhotoImage(file='image/button/remove_icon.png').subsample(30, 30)
        self.delete_button = ttk.Button(self.buttons_frame, text='Видалити', image=self.delete_icon, compound=tk.LEFT,
                                       style='Delete.TButton', command=self.delete_reservation)
        self.delete_button.pack(side='right', padx=5)

    def delete_reservation(self):
        selected_item = self.tree.selection()
        if selected_item:
            table_name = self.table_var.get()
            item_values = self.tree.item(selected_item)['values']
            primary_key_value = item_values[0]

            try:
                with self.connection.cursor() as cursor:
                    # Отключаем проверку внешних ключей (аналог SET FOREIGN_KEY_CHECKS=0 в MySQL)
                    cursor.execute("SET CONSTRAINTS ALL DEFERRED")

                    # Получаем информацию о внешних ключах
                    cursor.execute(f"""
                        SELECT tc.table_name, kcu.column_name 
                        FROM information_schema.table_constraints AS tc 
                        JOIN information_schema.key_column_usage AS kcu
                        ON tc.constraint_name = kcu.constraint_name
                        WHERE tc.constraint_type = 'FOREIGN KEY' 
                        AND tc.table_name = %s
                        ORDER BY tc.table_name DESC;
                    """, (table_name,))
                    foreign_keys = cursor.fetchall()

                    # Удаляем записи из связанных таблиц
                    for referenced_table, referenced_column in foreign_keys:
                        cursor.execute(f"DELETE FROM {referenced_table} WHERE {referenced_column} = %s",
                                      (primary_key_value,))

                    # Удаляем запись из основной таблицы
                    sql = f"DELETE FROM {table_name} WHERE {self.tree['columns'][0]} = %s"
                    cursor.execute(sql, (primary_key_value,))

                    # Включаем проверку внешних ключей
                    cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")

                    self.connection.commit()
                    self.refresh_data()
            except psycopg2.Error as e:
                messagebox.showerror("Помилка", f"Помилка видалення запису: {e}")
                print(f"Помилка: {e}")
                self.connection.rollback()

        else:
            messagebox.showwarning("Не вибрано", "Будь ласка, виберіть запис для видалення.")

    def edit_reservation(self):
        selected_item = self.tree.selection()
        print(f'selected_item: {selected_item}')
        if selected_item:
            table_name = self.table_var.get()
            item_values = self.tree.item(selected_item)['values']
            columns = self.tree['columns']
            edit_window = Edit(self.parent, table_name, columns, item_values, self.connection)
        else:
            messagebox.showwarning("Не вибрано", "Будь ласка, виберіть запис для редагування.")

    def get_tables(self):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE';
                """)
                result = cursor.fetchall()
                print(f"Результат: {result}")
                if result:
                    tables = [row[0] for row in result]
                    print(f"Знайдені таблиці: {tables}")
                    return tables
                else:
                    print("У базі даних не знайдено таблиць.")
                    return []
        except psycopg2.Error as e:  # Заменяем pymysql.Error на psycopg2.Error
            print(f"Помилка отримання таблиць: {e}")
            return []

    def update_table(self, selected_table):
        self.update_columns(selected_table)

    def update_columns(self, table_name):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = %s;
                """, (table_name,))
                result = cursor.fetchall()
                if result:
                    columns = [row[0] for row in result]  # Изменяем доступ к данным
                    self.tree['columns'] = columns
                    self.tree.heading('#0', text='ID')
                    for col in columns:
                        self.tree.heading(col, text=col)
                    self.refresh_data()
                else:
                    print(f"Не знайдено стовпців для таблиці {table_name}")
        except psycopg2.Error as e:  # Заменяем pymysql.Error на psycopg2.Error
            print(f"Помилка оновлення стовпців: {e}")

    def refresh_data(self):
        try:
            with self.connection.cursor() as cursor:
                table_name = self.table_var.get()
                sql = f"SELECT * FROM {table_name}"
                cursor.execute(sql)
                result = cursor.fetchall()
                if result:
                    self.tree.delete(*self.tree.get_children())
                    columns = [col for col in self.tree['columns']]

                    for col_index, col_name in enumerate(columns):
                        self.tree.heading(col_name, text=col_name)

                    for row in result:
                        values = [row[col_index] for col_index, _ in enumerate(columns)]  # Изменяем доступ к данным
                        self.tree.insert('', 'end', values=values)
                else:
                    print(f"Немає даних у таблиці {table_name}")
        except psycopg2.Error as e:  # Заменяем pymysql.Error на psycopg2.Error
            print(f"Помилка оновлення даних: {e}")


class Edit:
    def __init__(self, parent, table_name, columns, item_values, connection):
        self.parent = parent
        self.table_name = table_name
        self.columns = columns
        self.item_values = item_values
        self.connection = connection
        self.edit_window = tk.Toplevel(parent)
        self.edit_window.title(f"Редагувати {table_name}")
        self.edit_window.geometry("500x300")
        self.edit_window.configure(bg="#f0f0f0")

        self.entries = []
        print(columns)
        for i, column in enumerate(columns):
            ttk.Label(self.edit_window, text=column).grid(row=i, column=0, padx=5, pady=5, sticky=tk.E)
            entry = ttk.Entry(self.edit_window, width=40)
            entry.grid(row=i, column=1, padx=5, pady=5)
            print(item_values[i])
            entry.insert(0, item_values[i])
            self.entries.append(entry)

        save_button = ttk.Button(self.edit_window, text="Зберегти", command=self.save_changes)
        save_button.grid(row=len(columns), column=0, columnspan=2, pady=10)
        self.edit_window.grid_columnconfigure(0, weight=1)
        self.edit_window.grid_columnconfigure(1, weight=1)

    def save_changes(self):
        updated_values = [entry.get() for entry in self.entries]
        set_clause = ",".join([f"{col} = %s" for col in self.columns])
        primary_key = self.columns[0]
        primary_value = self.item_values[0]
        sql = f"UPDATE {self.table_name} SET {set_clause} WHERE {primary_key} = %s"

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql, (*updated_values, primary_value))
                self.connection.commit()
                messagebox.showinfo("Успіх", "Запис успішно оновлено")
                self.edit_window.destroy()
        except psycopg2.Error as e:  # Заменяем pymysql.Error на psycopg2.Error
            messagebox.showerror("Помилка", f"Не вдалося оновити запис: {e}")
            print(f"Помилка: {e}")