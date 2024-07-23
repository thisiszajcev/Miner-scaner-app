# src/ping.py
import subprocess

def ping_mikrotik(ip, container_name, update_container_status_callback):
    """Пингуем IP адрес Mikrotik и обновляем статус контейнера."""
    if ip:
        response = subprocess.run(['ping', '-n', '1', ip], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        status = "" if response.returncode == 0 else "red"
        update_container_status_callback(container_name, status)
