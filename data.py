# src/data.py
import json
import os

def save_containers(containers):
    """Сохраняет данные о контейнерах в файл data.json."""
    with open(os.path.join(os.path.dirname(__file__), "data.json"), "w") as f:
        json.dump(containers, f, indent=4)

def load_containers():
    """Загружает данные о контейнерах из файла data.json."""
    file_path = os.path.join(os.path.dirname(__file__), "data.json")
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    return {}
