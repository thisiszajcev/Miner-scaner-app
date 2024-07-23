# src/ui.py
import tkinter as tk
from tkinter import ttk, Toplevel, filedialog, Menu
from ttkbootstrap import Style
import csv
import pandas as pd
import webbrowser

class UI:
    def __init__(self, root, callbacks):
        self.root = root
        self.callbacks = callbacks
        self.style = Style(theme="litera")

        self.setup_menu()
        self.setup_container_frame()
        self.setup_tree_frame()
        self.setup_status_label()

    def setup_menu(self):
        """Настройка меню с необходимыми опциями."""
        self.menu_bar = Menu(self.root)
        self.create_file_menu()
        self.create_theme_menu()
        self.root.config(menu=self.menu_bar)

    def create_file_menu(self):
        """Создание меню файла с опциями экспорта."""
        file_menu = Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="Экспорт в CSV", command=self.callbacks['export_to_csv'])
        file_menu.add_command(label="Экспорт в XLSX", command=self.callbacks['export_to_xlsx'])
        self.menu_bar.add_cascade(label="Файл", menu=file_menu)

    def create_theme_menu(self):
        """Создание меню темы для смены тем."""
        theme_menu = Menu(self.menu_bar, tearoff=0)
        theme_menu.add_command(label="Светлая", command=lambda: self.change_theme("litera"))
        theme_menu.add_command(label="Темная", command=lambda: self.change_theme("darkly"))
        self.menu_bar.add_cascade(label="Тема", menu=theme_menu)

    def setup_container_frame(self):
        """Настройка фрейма управления контейнерами."""
        self.container_frame = tk.Frame(self.root)
        self.container_frame.pack(side="left", padx=10, pady=10, fill="y")

        self.add_container_label = tk.Label(self.container_frame, text="+ Добавить контейнер", fg="blue", cursor="hand2")
        self.add_container_label.pack(pady=5)
        self.add_container_label.bind("<Button-1>", lambda e: self.callbacks['open_add_container_window']())

        self.container_listbox = tk.Listbox(self.container_frame, selectmode=tk.MULTIPLE)
        self.container_listbox.pack(pady=5, fill="y", expand=True)
        self.container_listbox.bind("<Double-1>", self.callbacks['open_container_window'])

        self.search_entry = tk.Entry(self.container_frame)
        self.search_entry.insert(0, 'Поиск')
        self.search_entry.pack(pady=5)
        self.search_entry.bind("<KeyRelease>", self.callbacks['search_tree'])

        self.scan_button = tk.Button(self.container_frame, text="Scan", command=self.callbacks['scan_selected_containers'])
        self.scan_button.pack(side="bottom", pady=10)

    def setup_tree_frame(self):
        """Настройка фрейма с таблицей для отображения данных сканирования."""
        columns = ("IP", "Type", "GHS av", "GHS 5s", "total_freqavg", "miner_version", "Pool", "User", "Elapsed")
        self.tree_frame = tk.Frame(self.root)
        self.tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.tree_scroll_y = tk.Scrollbar(self.tree_frame, orient="vertical")
        self.tree_scroll_y.pack(side="right", fill="y")

        self.tree_scroll_x = tk.Scrollbar(self.tree_frame, orient="horizontal")
        self.tree_scroll_x.pack(side="bottom", fill="x")

        self.tree = ttk.Treeview(self.tree_frame, columns=columns, show="headings", style="Treeview",
                                 yscrollcommand=self.tree_scroll_y.set, xscrollcommand=self.tree_scroll_x.set)
        self.tree.pack(fill="both", expand=True)

        self.tree_scroll_y.config(command=self.tree.yview)
        self.tree_scroll_x.config(command=self.tree.xview)

        for col in columns:
            self.tree.heading(col, text=col, command=lambda _col=col: self.sort_by(_col, False))
            self.tree.column(col, width=100)

        self.tree.bind("<Double-1>", self.callbacks['on_double_click'])
        self.tree.bind("<Control-c>", self.callbacks['copy_selection'])
        self.tree.bind("<Button-3>", self.callbacks['show_context_menu'])

    def setup_status_label(self):
        """Настройка метки статуса в нижней части окна."""
        self.status_label = tk.Label(self.root, text="В сети: 0")
        self.status_label.pack(side="bottom", fill="x")

    def change_theme(self, theme_name):
        """Смена темы приложения."""
        self.style.theme_use(theme_name)

    def open_add_container_window(self):
        """Открыть окно добавления контейнера."""
        if hasattr(self, 'add_container_window') and self.add_container_window.winfo_exists():
            return  # Предотвращение открытия нескольких окон

        self.add_container_window = Toplevel(self.root)
        self.add_container_window.title("Редактировать контейнер")
        self.add_container_window.geometry("300x300")

        tk.Label(self.add_container_window, text="Название:").pack(pady=5)
        self.container_name_entry = tk.Entry(self.add_container_window)
        self.container_name_entry.pack(pady=5)

        tk.Label(self.add_container_window, text="Диапазоны IP (через запятую):").pack(pady=5)
        self.ip_ranges_entry = tk.Entry(self.add_container_window)
        self.ip_ranges_entry.pack(pady=5)

        tk.Label(self.add_container_window, text="IP микротика (если есть):").pack(pady=5)
        self.mikrotik_ip_entry = tk.Entry(self.add_container_window)
        self.mikrotik_ip_entry.pack(pady=5)

        self.save_button = tk.Button(self.add_container_window, text="Сохранить", command=self.save_container)
        self.save_button.pack(pady=10)

    def save_container(self):
        """Сохранить информацию о контейнере."""
        container_name = self.container_name_entry.get()
        ip_ranges = self.ip_ranges_entry.get()
        mikrotik_ip = self.mikrotik_ip_entry.get()

        if container_name and ip_ranges:
            self.callbacks['save_container'](container_name, ip_ranges, mikrotik_ip)
        self.add_container_window.destroy()

    def update_container_status(self, container_name, status):
        """Обновить статус контейнера в списке."""
        try:
            index = self.container_listbox.get(0, "end").index(container_name)
            self.container_listbox.itemconfig(index, {'fg': status})
        except ValueError:
            pass  # Обработка случая, когда container_name не найден

    def update_tree(self, ip, data):
        """Обновить таблицу данными."""
        stats_data = data.get("stats", {}).get("STATS", [{}])
        pools_data = data.get("pools", {}).get("POOLS", [{}])

        stat = stats_data[0] if len(stats_data) > 0 else {}
        stat_s = stats_data[1] if len(stats_data) > 1 else {}
        pool_one = pools_data[0] if len(pools_data) > 0 else {}
        pool_two = pools_data[1] if len(pools_data) > 1 else {}
        pool_three = pools_data[2] if len(pools_data) > 2 else {}

        values = [
            ip,
            stat.get("Type", ""),
            stat_s.get("GHS av", ""),
            stat_s.get("GHS 5s", ""),
            stat_s.get("total_freqavg", ""),
            stat_s.get("miner_version", ""),
            pool_one.get("URL", ""),
            pool_two.get("User", ""),
            stat_s.get("Elapsed", "")
        ]

        self.tree.insert("", "end", values=values)
        self.update_scan_count()

    def clear_tree(self):
        """Очистить таблицу."""
        for item in self.tree.get_children():
            self.tree.delete(item)

    def sort_by(self, col, descending):
        """Сортировка таблицы по указанному столбцу."""
        data = [(self.tree.set(child, col), child) for child in self.tree.get_children()]
        data.sort(reverse=descending)

        for index, item in enumerate(data):
            self.tree.move(item[1], '', index)

        self.tree.heading(col, command=lambda: self.sort_by(col, not descending))

    def on_double_click(self, event):
        """Открытие веб-страницы при двойном клике."""
        item = self.tree.selection()[0]
        url = self.tree.item(item, 'values')[6]
        if url:
            webbrowser.open(url)

    def copy_selection(self, event):
        """Копирование выбранных строк в буфер обмена."""
        selected_items = [self.tree.item(item, 'values') for item in self.tree.selection()]
        if selected_items:
            clipboard_data = "\n".join([",".join(map(str, item)) for item in selected_items])
            self.root.clipboard_clear()
            self.root.clipboard_append(clipboard_data)

    def show_context_menu(self, event):
        """Отображение контекстного меню при правом клике."""
        context_menu = Menu(self.root, tearoff=0)
        context_menu.add_command(label="Копировать", command=lambda: self.copy_selection(event))
        context_menu.post(event.x_root, event.y_root)

    def update_scan_count(self):
        """Обновить количество контейнеров в статусе."""
        count = len(self.container_listbox.get(0, "end"))
        self.status_label.config(text=f"В сети: {count}")
