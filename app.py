import sys
import tkinter as tk
from tkinter import ttk, font
from PIL import Image, ImageTk
from PIL. Image import Resampling
from MainMenu import MainMenuTab
from DataBase import CheckTab

class TelegramBotSettings:
    def __init__(self, root):
        self.root = root
        self.root.geometry('1200x700')
        self.root.title("Обслуговування боту телеграм")
        self.root.iconphoto(False, tk.PhotoImage(file='image/Telegram.png'))

        style = ttk.Style(self. root)
        style.configure('TNotebook', tabposition='w')
        style.configure('TNotebook.Tab', padding=[2, 5], font=('Helvetica', 10))
        style.map("TNotebook.Tab", background=[("selected", "white")], foreground=[("selected", "white")])
        style.map("TNotebook", background=[("selected", "white")])
        style.configure('TButton', focusthickness=0)

        style.configure('TabButton.TButton', focusthickness=0)
        style.map("TabButton.TButton", foreground=[("disabled", "black"), ("pressed", "black"), ("active", "black")],
        background=[("disabled", "white"), ("pressed", "white"), ("active", "white")])

        self.notebook = ttk.Notebook(self.root, style='TNotebook')
        self.notebook.pack(fill='both', expand=True)
        self.notebook.bind("<<NotebookTabChanged>>", self.remove_focus)

        self.tab_menu = tk.Menu(self.root, tearoff=0)
        self.tab_menu.add_command(label="Головне меню", command=lambda: self.show_tab_content("Головне меню"))
        self.tab_menu.add_command(label="Перегляд БД", command=lambda: self.show_tab_content("Перегляд БД"))

        font_family = "Helvetica"
        font_size = 10
        fixed_font = font.Font(family=font_family, size=font_size)
        max_tab_width = max(fixed_font.measure(tab_name) for tab_name in ["Головне меню", "Перегляд БД"])

        self.main_menu_tab = MainMenuTab(self.notebook, root)
        self.check_tab = CheckTab(self.notebook, root)

        self.add_tab('Головне меню', 'image/button/main_menu.png', max_tab_width, fixed_font, self.main_menu_tab.frame)
        self.add_tab('Перегляд БД', 'image/button/database.png', max_tab_width, fixed_font, self.check_tab.frame)

    def add_tab (self, tab_name, image_path, max_tab_width, fixed_font, tab_frame):
        image = Image.open(image_path)
        image = image.resize((32, 32), Resampling. LANCZOS)
        photo_image = ImageTk.PhotoImage(image)

        button_width = max_tab_width // fixed_font. measure(" ") + 10

        button = ttk.Button(self.notebook, image=photo_image, compound='left', text=tab_name, command=lambda: self.notebook.select(tab_frame), width=button_width, style="TabButton.TButton")
        button.image = photo_image
        self.notebook.add(tab_frame, text='', image=photo_image, compound='left', underline=-1)

    def remove_focus (self, event):
        self.notebook.event_generate("<FocusOut>")

if __name__ == "__main__":
    root = tk. Tk()
    app = TelegramBotSettings (root)
    root. mainloop()
