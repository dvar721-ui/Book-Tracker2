import tkinter as tk
from tkinter import ttk, messagebox
import json
import os

DATA_FILE = "books.json"

def validate_input(title, author, genre, pages_str):
    """Возвращает (is_valid, сообщение_об_ошибке)."""
    if not title.strip():
        return False, "Название книги не может быть пустым"
    if not author.strip():
        return False, "Автор не может быть пустым"
    if not genre.strip():
        return False, "Жанр не может быть пустым"
    try:
        pages = int(pages_str)
        if pages <= 0:
            return False, "Количество страниц должно быть положительным числом"
    except ValueError:
        return False, "Количество страниц должно быть целым числом"
    return True, ""

class BookTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Book Tracker – Гильманов Адель")
        root.geometry("700x500")
        root.resizable(True, True)

        self.books = []  # список словарей: title, author, genre, pages

        # --- Фрейм ввода данных ---
        input_frame = ttk.LabelFrame(root, text="Добавление книги", padding=10)
        input_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(input_frame, text="Название:").grid(row=0, column=0, sticky="w")
        self.title_entry = ttk.Entry(input_frame, width=30)
        self.title_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")

        ttk.Label(input_frame, text="Автор:").grid(row=1, column=0, sticky="w")
        self.author_entry = ttk.Entry(input_frame, width=30)
        self.author_entry.grid(row=1, column=1, padx=5, pady=2, sticky="ew")

        ttk.Label(input_frame, text="Жанр:").grid(row=2, column=0, sticky="w")
        self.genre_entry = ttk.Entry(input_frame, width=30)
        self.genre_entry.grid(row=2, column=1, padx=5, pady=2, sticky="ew")

        ttk.Label(input_frame, text="Кол-во страниц:").grid(row=3, column=0, sticky="w")
        self.pages_entry = ttk.Entry(input_frame, width=10)
        self.pages_entry.grid(row=3, column=1, padx=5, pady=2, sticky="w")

        btn_add = ttk.Button(input_frame, text="Добавить книгу", command=self.add_book)
        btn_add.grid(row=4, column=0, columnspan=2, pady=5)

        input_frame.columnconfigure(1, weight=1)

        # --- Фрейм фильтрации ---
        filter_frame = ttk.LabelFrame(root, text="Фильтрация", padding=10)
        filter_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(filter_frame, text="По жанру:").grid(row=0, column=0, sticky="w")
        self.filter_genre = ttk.Combobox(filter_frame, values=[], state="normal")
        self.filter_genre.grid(row=0, column=1, padx=5)
        self.filter_genre.bind("<<ComboboxSelected>>", lambda e: self.apply_filters())
        self.filter_genre.set("")

        ttk.Label(filter_frame, text="Страниц >").grid(row=1, column=0, sticky="w")
        self.filter_pages = ttk.Entry(filter_frame, width=6)
        self.filter_pages.grid(row=1, column=1, padx=5, sticky="w")
        self.filter_pages.bind("<KeyRelease>", lambda e: self.apply_filters())

        btn_clear = ttk.Button(filter_frame, text="Сбросить фильтры", command=self.clear_filters)
        btn_clear.grid(row=1, column=2, padx=5)

        # --- Таблица книг (Treeview) ---
        table_frame = ttk.Frame(root)
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ("title", "author", "genre", "pages")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        self.tree.heading("title", text="Название")
        self.tree.heading("author", text="Автор")
        self.tree.heading("genre", text="Жанр")
        self.tree.heading("pages", text="Страниц")
        self.tree.column("title", width=200)
        self.tree.column("author", width=150)
        self.tree.column("genre", width=120)
        self.tree.column("pages", width=80)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # --- Кнопки сохранения/загрузки ---
        button_frame = ttk.Frame(root)
        button_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(button_frame, text="Сохранить в JSON", command=self.save_to_json).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Загрузить из JSON", command=self.load_from_json).pack(side="left", padx=5)

        # Загрузка данных при старте, если файл есть
        self.load_from_json()

    # ---------- Логика ----------
    def add_book(self):
        title = self.title_entry.get()
        author = self.author_entry.get()
        genre = self.genre_entry.get()
        pages_str = self.pages_entry.get()

        valid, msg = validate_input(title, author, genre, pages_str)
        if not valid:
            messagebox.showerror("Ошибка ввода", msg)
            return

        pages = int(pages_str)
        book = {"title": title.strip(), "author": author.strip(),
                "genre": genre.strip(), "pages": pages}
        self.books.append(book)
        self.refresh_table()
        self.update_genre_list()
        self.clear_entries()
        messagebox.showinfo("Успех", "Книга добавлена!")

    def refresh_table(self):
        """Отображает книги с учётом фильтров."""
        # Удаляем все строки
        for row in self.tree.get_children():
            self.tree.delete(row)

        genre_filter = self.filter_genre.get().strip()
        pages_filter_str = self.filter_pages.get().strip()
        min_pages = None
        if pages_filter_str != "":
            try:
                min_pages = int(pages_filter_str)
            except ValueError:
                min_pages = None  # игнорируем некорректный ввод

        for book in self.books:
            if genre_filter and book["genre"].lower() != genre_filter.lower():
                continue
            if min_pages is not None and book["pages"] <= min_pages:
                continue
            self.tree.insert("", "end", values=(
                book["title"], book["author"], book["genre"], book["pages"]))

    def update_genre_list(self):
        """Обновляет выпадающий список уникальных жанров."""
        genres = sorted(list({book["genre"] for book in self.books}))
        self.filter_genre["values"] = genres
        # если текущий выбор больше не существует, сбрасываем
        current = self.filter_genre.get()
        if current and current not in genres:
            self.filter_genre.set("")

    def apply_filters(self):
        # Избегаем ошибок при вводе некорректного числа
        try:
            if self.filter_pages.get().strip():
                int(self.filter_pages.get())
        except ValueError:
            pass  # просто не обновляем, пока пользователь не введёт корректное число
        self.update_genre_list()
        self.refresh_table()

    def clear_filters(self):
        self.filter_genre.set("")
        self.filter_pages.delete(0, "end")
        self.refresh_table()

    def clear_entries(self):
        self.title_entry.delete(0, "end")
        self.author_entry.delete(0, "end")
        self.genre_entry.delete(0, "end")
        self.pages_entry.delete(0, "end")

    # ---------- Работа с JSON ----------
    def save_to_json(self):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.books, f, ensure_ascii=False, indent=4)
            messagebox.showinfo("Сохранение", f"Данные сохранены в {DATA_FILE}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить: {e}")

    def load_from_json(self):
        if not os.path.exists(DATA_FILE):
            return
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                self.books = json.load(f)
            # Базовая проверка структуры
            if not isinstance(self.books, list):
                raise ValueError("Некорректный формат данных")
            # Проверим, что каждый элемент – словарь с нужными ключами
            for book in self.books:
                if not all(k in book for k in ("title", "author", "genre", "pages")):
                    raise ValueError("Повреждённые данные книги")
            self.refresh_table()
            self.update_genre_list()
            messagebox.showinfo("Загрузка", f"Загружено {len(self.books)} книг")
        except Exception as e:
            messagebox.showerror("Ошибка загрузки", f"Не удалось загрузить данные: {e}")
            self.books = []

if __name__ == "__main__":
    root = tk.Tk()
    app = BookTrackerApp(root)
    root.mainloop()