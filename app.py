# src/app.py

import tkinter as tk
from tkinter import messagebox, filedialog
import csv
import pandas as pd
from ui import UI
from ping import ping_mikrotik
from data import load_containers, save_containers
from ant import Ant
from ipaddress import ip_network, ip_address

class App:
    def __init__(self, root):
        self.root = root
        self.ant = Ant()
        self.setup_callbacks()  # Настраиваем callback-функции перед инициализацией UI
        self.initialize_ui()  # Инициализируем UI после настройки callback-функций
        self.containers = load_containers()
        self.update_container_listbox()

    def setup_callbacks(self):
        """Настройка callback-функций для UI."""
        self.callbacks = {
            'open_add_container_window': self.open_add_container_window,
            'save_container': self.save_container,
            'scan_selected_containers': self.scan_selected_containers,
            'search_tree': self.search_tree,
            'open_container_window': self.open_container_window,
            'on_double_click': self.on_double_click,
            'copy_selection': self.copy_selection,
            'show_context_menu': self.show_context_menu,
            'export_to_csv': self.export_to_csv,
            'export_to_xlsx': self.export_to_xlsx,
            'show_info': self.show_info
        }
        if hasattr(self, 'ui') and self.ui:
            self.ant.set_update_tree_callback(self.ui.update_tree)

    def initialize_ui(self):
        """Инициализация UI."""
        self.ui = UI(self.root, self.callbacks)

    def open_add_container_window(self):
        """Открываем окно для добавления нового контейнера."""
        self.ui.open_add_container_window()

    def save_container(self, container_name, ip_ranges, mikrotik_ip):
        """Сохраняем данные о новом контейнере."""
        if container_name and ip_ranges:
            self.containers[container_name] = {
                'ip_ranges': [ip.strip() for ip in ip_ranges.split(',')],
                'mikrotik_ip': mikrotik_ip
            }
            save_containers(self.containers)
            self.update_container_listbox()
            self.ui.update_container_status(container_name, "")
        else:
            messagebox.showwarning("Ошибка", "Заполните все обязательные поля")

    def update_container_listbox(self):
        """Обновляем список контейнеров в UI."""
        self.ui.container_listbox.delete(0, tk.END)
        for container in self.containers:
            self.ui.container_listbox.insert(tk.END, container)

    def scan_selected_containers(self):
        """Сканируем выбранные контейнеры."""
        selected_containers = [self.ui.container_listbox.get(idx) for idx in self.ui.container_listbox.curselection()]
        print(f"Сканирование запущено\nВыбранные контейнеры: {selected_containers}")
        for container_name in selected_containers:
            container_data = self.containers.get(container_name, {})
            ip_ranges = container_data.get('ip_ranges', [])
            mikrotik_ip = container_data.get('mikrotik_ip', None)

            # Пингуем IP Mikrotik
            print(f"Пинг Mikrotik: {mikrotik_ip} для контейнера {container_name}")
            ping_mikrotik(mikrotik_ip, container_name, self.ui.update_container_status)

            # Запускаем сканирование по IP-диапазонам
            for ip_range in ip_ranges:
                expanded_ips = self.expand_ip_range(ip_range)
                print(f"IP диапазон {ip_range} расширен до: {expanded_ips}")
                for ip in expanded_ips:
                    print(f"Сканируем IP: {ip}")
                    self.ant.scan_miner(ip)

    def expand_ip_range(self, ip_range):
        """Расширяем диапазон IP адресов в список."""
        try:
            # Если IP-диапазон имеет формат CIDR, например, 10.4.101.0/24
            if ip_range.endswith('/24'):
                network = ip_network(ip_range, strict=False)
                return [str(ip) for ip in network.hosts()]
            # Если IP-диапазон имеет формат, например, 10.4.101.1-255
            elif '-' in ip_range:
                base_ip, range_part = ip_range.rsplit('.', 1)
                start_ip, end_ip = range_part.split('-')
                start = ip_address(f"{base_ip}.{start_ip}")
                end = ip_address(f"{base_ip}.{end_ip}")
                return [str(ip) for ip in ip_network(f"{base_ip}/{end - start}", strict=False).hosts() if start <= ip <= end]
            # Если IP-диапазон имеет формат, например, 10.4.101 (весь диапазон 10.4.101.1-255)
            elif len(ip_range.split('.')) == 3:
                base_ip = ip_range
                return [f"{base_ip}.{i}" for i in range(1, 256)]
        except ValueError:
            return []
        return []

    def search_tree(self, event):
        """Функция поиска в дереве."""
        search_text = self.ui.search_entry.get().lower()
        for item in self.ui.tree.get_children():
            values = self.ui.tree.item(item, 'values')
            if any(search_text in str(value).lower() for value in values):
                self.ui.tree.selection_add(item)
            else:
                self.ui.tree.selection_remove(item)

    def open_container_window(self, event):
        """Открываем окно с данными выбранного контейнера."""
        selected_items = self.ui.tree.selection()
        for item in selected_items:
            ip = self.ui.tree.item(item, 'values')[0]
            messagebox.showinfo("IP-адрес", f"IP: {ip}")

    def on_double_click(self, event):
        """Действие при двойном клике по элементу дерева."""
        self.open_container_window(event)

    def copy_selection(self, event):
        """Копируем выбранные данные из дерева."""
        selected_items = self.ui.tree.selection()
        if selected_items:
            data = "\n".join([", ".join(self.ui.tree.item(item, 'values')) for item in selected_items])
            self.root.clipboard_clear()
            self.root.clipboard_append(data)
            self.root.update()  # Оба действия (очистка и добавление) должны быть в одном вызове update

    def show_context_menu(self, event):
        """Показываем контекстное меню."""
        self.ui.show_context_menu(event)

    def show_info(self):
        """Отображаем информацию о приложении."""
        messagebox.showinfo("Информация", "Информация о приложении")

    def export_to_csv(self):
        """Экспортируем данные в CSV."""
        file_path = filedialog.asksaveasfilename(defaultextension=".csv",
                                               filetypes=[("CSV файлы", "*.csv")])
        if file_path:
            with open(file_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["IP", "Type", "GHS av", "GHS 5s", "total_freqavg", "miner_version", "Pool", "User", "Elapsed"])
                for item in self.ui.tree.get_children():
                    values = self.ui.tree.item(item, 'values')
                    writer.writerow(values)

    def export_to_xlsx(self):
        """Экспортируем данные в XLSX."""
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                               filetypes=[("Excel файлы", "*.xlsx")])
        if file_path:
            data = [self.ui.tree.item(item, 'values') for item in self.ui.tree.get_children()]
            df = pd.DataFrame(data, columns=["IP", "Type", "GHS av", "GHS 5s", "total_freqavg", "miner_version", "Pool", "User", "Elapsed"])
            df.to_excel(file_path, index=False)

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Мониторинг Контейнеров")
    root.geometry("1200x800")  # Установим размер окна по умолчанию
    app = App(root)
    root.mainloop()
