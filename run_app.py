# src/run_app.py
import tkinter as tk
from app import App

def main():
    # Создаем главное окно
    root = tk.Tk()
    root.title("Miner scaner")
    root.geometry("1200x800")  # Установим размер окна по умолчанию

    # Создаем и запускаем приложение
    app = App(root)
    root.mainloop()

if __name__ == "__main__":
    main()
