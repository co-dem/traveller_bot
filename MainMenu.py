import subprocess
from config import create_connection
from tkinter import ttk, messagebox, filedialog
import tkinter as tk
import os
import psycopg2  # Заменяем pymysql на psycopg2
import shutil


class MainMenuTab:
    def __init__(self, notebook, root):
        self.root = root
        self.conn = create_connection()
        self.cursor = self.conn.cursor()  # Убираем DictCursor, так как в psycopg2 он не используется
        self.bot_process = None

        self.frame = tk.Frame(notebook)
        notebook.add(self.frame, text='Головне меню', padding=10)

        style = ttk.Style()
        style.configure('TMenubutton', font=('Cambria', 10))
        style.configure('TButton', font=('Cambria', 12))
        style.configure('Bot.TButton', font=('Cambria', 20))

        self.add_country_img = tk.PhotoImage(file='image/button/addcountry.png').subsample(25, 25)
        self.save_img = tk.PhotoImage(file='image/button/save.png').subsample(25, 25)
        self.add_image_img = tk.PhotoImage(file='image/button/addimage.png').subsample(25, 25)
        self.add_city_img = tk.PhotoImage(file='image/button/addcity.png').subsample(25, 25)
        self.play_img = tk.PhotoImage(file='image/button/play.png').subsample(25, 25)
        self.exitbot_img = tk.PhotoImage(file='image/button/exitbot.png').subsample(25, 25)
       
        self.top_frame = tk.Frame(self.frame)
        self.top_frame.pack(side=tk.TOP, pady=10)

        self.add_country_button = ttk.Button(self.top_frame, text='Додати країну', image=self.add_country_img,
                                             compound=tk.LEFT, command=self.add_country_window)
        self.add_country_button.pack(side=tk.LEFT, padx=5)

        self.country_var = tk.StringVar()
        self.country_dropdown = ttk.OptionMenu(self.top_frame, self.country_var, 'Виберіть країну')
        self.country_dropdown.pack(side=tk.LEFT, padx=5)

        self.city_entry = ttk.Entry(self.top_frame, font=('Arial', 10))
        self.city_entry.pack(side=tk.LEFT, padx=5)
        self.city_button = ttk.Button(self.top_frame, text='Додати місто', image=self.add_city_img, compound=tk.LEFT,
                                      command=self.add_city)
        self.city_button.pack(side=tk.LEFT, padx=5)

        self.middle_frame = tk.Frame(self.frame)
        self.middle_frame.pack(side=tk.TOP, pady=10)

        self.location_country_var = tk.StringVar()
        self.location_country_var.set('Виберіть місто')
        self.location_country_dropdown = ttk.OptionMenu(self.middle_frame, self.location_country_var, 'Виберіть країну')
        self.location_country_dropdown.grid(row=0, column=0, padx=5, pady=5)
        self.location_country_var.trace('w', lambda *args: self.update_city_dropdown())

        self.location_city_var = tk.StringVar()
        self.location_city_dropdown = ttk.OptionMenu(self.middle_frame, self.location_city_var, 'Виберіть місто')
        self.location_city_dropdown.grid(row=0, column=1, padx=5, pady=5)
        self.update_city_dropdown()
        tk.Label(self.middle_frame, text='Назва локації:', font=('Cambria', 12)).grid(row=1, column=0, padx=5, pady=5,
                                                                                     sticky=tk.E)
        self.location_name_entry = ttk.Entry(self.middle_frame, font=('Arial', 10))
        self.location_name_entry.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(self.middle_frame, text='Опис локації:', font=('Cambria', 12)).grid(row=2, column=0, padx=5, pady=5,
                                                                                     sticky=tk.E)
        self.location_description_entry = ttk.Entry(self.middle_frame, font=('Arial', 10))
        self.location_description_entry.grid(row=2, column=1, padx=5, pady=5)

        self.image_button = ttk.Button(self.middle_frame, text='Додати зображення', image=self.add_image_img,
                                       compound=tk.LEFT, command=self.add_image)
        self.image_button.grid(row=3, column=0, padx=5, pady=5)
        self.image_path_label = tk.Label(self.middle_frame, text='', font=('Arial', 10))
        self.image_path_label.grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)

        self.bottom_frame = tk.Frame(self.frame)
        self.bottom_frame.pack(side=tk.TOP, pady=10)

        self.save_button = ttk.Button(self.bottom_frame, text='Зберегти', image=self.save_img, compound=tk.LEFT,
                                      command=self.save_data)
        self.save_button.pack()

        self.bot_button = ttk.Button(self.frame, text='Запуск бота', image=self.play_img, compound=tk.LEFT,
                                     command=self.toggle_bot)
        self.bot_button.pack(side=tk.TOP, pady=20)

        self.update_country_dropdown()

    def update_country_dropdown(self):
        try:
            sql = 'SELECT * FROM countries;'
            print(f'Executing SQL: {sql}')
            self.cursor.execute(sql)

            countries = self.cursor.fetchall()
            menu = self.country_dropdown['menu']
            menu.delete(0, 'end')
            for country in countries:
                menu.add_command(label=f"{country[0]} - {country[1]}",
                                command=lambda value=f"{country[0]} - {country[1]}": self.country_var.set(value))

            menu = self.location_country_dropdown['menu']
            menu.delete(0, 'end')
            for country in countries:
                menu.add_command(label=f"{country[0]} - {country[1]}",
                                command=lambda value=f"{country[0]} - {country[1]}": self.location_country_var.set(value))
        except Exception as e:
            print(f'Error: {e}')

    def update_city_dropdown(self, event=None):
        country_id = self.location_country_var.get().split(' - ')[0]
        try:
            if country_id == 'Виберіть країну':
                country_id = 1
            sql = 'SELECT id, name FROM cities WHERE country_id = %s'
            print(f'Executing SQL: {sql} with country_id={country_id}')
            self.cursor.execute(sql, (country_id,))
            cities = self.cursor.fetchall()
            menu = self.location_city_dropdown['menu']
            menu.delete(0, 'end')
            print(cities)
            for city in cities:
                menu.add_command(label=city[1],
                                 command=lambda value=city[1]: self.location_city_var.set(value))
        except Exception as e:
            print(f'Error: {e}')

    def add_country_window(self):
        add_country_window = tk.Toplevel(self.root)
        add_country_window.title('Додати країну')
        add_country_window.geometry('300x150')

        frame = tk.Frame(add_country_window, padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text='Назва країни:', font=('Arial', 12)).pack(pady=5)

        country_entry = ttk.Entry(frame, font=('Arial', 12), width=25)
        country_entry.pack(pady=5)

        def add_country():
            country_name = country_entry.get()
            if country_name:
                try:
                    sql = 'INSERT INTO countries (name) VALUES (%s)'
                    print(f'Executing SQL: {sql} with country_name={country_name}')
                    self.cursor.execute(f"INSERT INTO countries (name) VALUES ('{country_name}');")
                    self.conn.commit()
                    messagebox.showinfo('Успіх', f"Країна '{country_name}' додана до бази даних.")
                    self.update_country_dropdown()
                    os.makedirs(os.path.join('places', country_name), exist_ok=True)
                    add_country_window.destroy()
                except psycopg2.IntegrityError as e:  # Заменяем pymysql.err.IntegrityError на psycopg2.IntegrityError
                    print(f'Integrity Error: {e}')
                    messagebox.showerror('Помилка', f"Країна '{country_name}' вже існує в базі даних.")
                except Exception as e:
                    self.conn.rollback()
                    print(f'Error: {e}')
                    messagebox.showerror('Помилка', str(e))
            else:
                messagebox.showerror('Помилка', 'Введіть назву країни.')

        add_country_img = tk.PhotoImage(file='image/button/addcountry.png').subsample(25, 25)

        add_button = ttk.Button(frame, text='Зберегти', image=add_country_img, compound=tk.LEFT, command=add_country)
        add_button.pack(pady=10)

        add_country_window.image = add_country_img
    

    def add_city(self):
        city_name = self.city_entry.get()
        country_id = self.country_var.get().split(' - ')[0]
        if city_name and country_id:
            try:
                sql = 'INSERT INTO cities (name, country_id) VALUES (%s, %s)'
                print(f'Executing SQL: {sql} with city_name={city_name}, country_id={country_id}')
                self.cursor.execute(sql, (city_name, int(country_id)))
                self.conn.commit()
                self.city_entry.delete(0, tk.END)
                messagebox.showinfo('Успіх', f"Місто '{city_name}' додане до бази даних.")
                self.update_city_dropdown()
                os.makedirs(os.path.join('places', self.country_var.get().split(' - ')[1], city_name), exist_ok=True)
            except psycopg2.IntegrityError as e:  # Заменяем pymysql.err.IntegrityError на psycopg2.IntegrityError
                print(f'Integrity Error: {e}')
                messagebox.showerror('Помилка', f"Місто '{city_name}' вже існує в базі даних.")
            except Exception as e:
                print(f'Error: {e}')
                messagebox.showerror('Помилка', str(e))
        else:
            messagebox.showerror('Помилка', 'Введіть назву міста та виберіть країну.')

    def add_image(self):
        file_path = filedialog.askopenfilename(filetypes=[('Image files', '*.jpg;*.jpeg;*.png')])
        if file_path:
            self.image_path = file_path
            self.image_path_label.config(text=os.path.basename(file_path))
            print(f'Image selected: {file_path}')
            messagebox.showinfo('Успіх', f"Зображення '{file_path}' додане.")
        else:
            messagebox.showerror('Помилка', 'Зображення не обране.')

    def save_data(self):
        country_id = self.location_country_var.get().split(' - ')[0] if self.location_country_var.get() != 'Виберіть країну' else None
        city_name = self.location_city_var.get() if self.location_city_var.get() != 'Виберіть місто' else None
        location_name = self.location_name_entry.get()
        location_description = self.location_description_entry.get()
        image_path = getattr(self, 'image_path', None)

        if not country_id:
            messagebox.showerror('Помилка', 'Виберіть країну.')
        elif not city_name:
            messagebox.showerror('Помилка', 'Виберіть місто.')
        elif not location_name:
            messagebox.showerror('Помилка', 'Введіть назву локації.')
        elif not location_description:
            messagebox.showerror('Помилка', 'Введіть опис локації.')
        elif not image_path:
            messagebox.showerror('Помилка', 'Додайте зображення.')
        else:
            try:
                city_id = self.get_city_id_by_name(city_name, country_id)
                relative_image_path = os.path.join('places', self.get_country_name_by_id(country_id), city_name,
                                                  os.path.basename(image_path))
                sql = 'INSERT INTO places (name, description, image, city_id) VALUES (%s, %s, %s, %s)'
                print(f'Executing SQL: {sql} with location_name={location_name}, description={location_description}, image_path={relative_image_path}, city_id={city_id}')
                self.cursor.execute(sql, (location_name, location_description, relative_image_path, city_id))
                self.conn.commit()
                messagebox.showinfo('Успіх', 'Дані успішно збережено.')
                self.copy_image_to_location(country_id, city_name, image_path)
                self.clear_entries()
            except psycopg2.IntegrityError as e:  # Заменяем pymysql.err.IntegrityError на psycopg2.IntegrityError
                print(f'Integrity Error: {e}')
                messagebox.showerror('Помилка', 'Дані вже існують в базі даних.')
            except Exception as e:
                print(f'Error: {e}')
                messagebox.showerror('Помилка', str(e))

    def get_city_id_by_name(self, city_name, country_id):
        try:
            sql = 'SELECT id FROM cities WHERE name = %s AND country_id = %s'
            print(f'Executing SQL: {sql} with city_name={city_name}, country_id={country_id}')
            self.cursor.execute(sql, (city_name, country_id))
            result = self.cursor.fetchone()
            if result:
                return result[0]
            else:
                raise ValueError('Місто не знайдено.')
        except Exception as e:
            print(f'Error: {e}')
            raise

    def copy_image_to_location(self, country_id, city_name, image_path):
        country_name = self.get_country_name_by_id(country_id)
        destination_dir = os.path.join('places', country_name, city_name)
        os.makedirs(destination_dir, exist_ok=True)
        destination_path = os.path.join(destination_dir, os.path.basename(image_path))
        shutil.copy(image_path, destination_path)
        print(f'Image copied to: {destination_path}')

    def get_country_name_by_id(self, country_id):
        try:
            sql = 'SELECT name FROM countries WHERE id = %s'
            print(f'Executing SQL: {sql} with country_id={country_id}')
            self.cursor.execute(sql, (country_id,))
            return self.cursor.fetchone()[0]
        except Exception as e:
            print(f'Error: {e}')

    def clear_entries(self):
        self.location_name_entry.delete(0, tk.END)
        self.location_description_entry.delete(0, tk.END)
        self.location_country_var.set('Виберіть країну')
        self.location_city_var.set('Виберіть місто')
        self.image_path = None
        self.image_path_label.config(text='')

    def toggle_bot(self):
        if self.bot_process is None:
            try:
                self.bot_process = subprocess.Popen(['python', 'main.py'])
                self.bot_button.config(text='Вимкнути бота', image=self.exitbot_img)
                messagebox.showinfo('Успіх', 'Бот запущений.')
            except Exception as e:
                print(f'Error: {e}')
                messagebox.showerror('Помилка', f'Не вдалося запустити бота: {e}')
        else:
            try:
                self.bot_process.terminate()
                self.bot_process = None
                self.bot_button.config(text='Запуск бота', image=self.play_img)
                messagebox.showinfo('Успіх', 'Бот вимкнений.')
            except Exception as e:
                print(f'Error: {e}')
                messagebox.showerror('Помилка', f'Не вдалося вимкнути бота: {e}')