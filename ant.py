# src/ant.py
import socket
import json
import threading

class Ant:
    def __init__(self):
        self.scanned_data = {}
        self.scanned_data_lock = threading.Lock()

    def scan_miner(self, ip):
        """Сканируем аппарат, запрашивая его статистику и пулы."""
        self.scan_command(ip, "stats")
        self.scan_command(ip, "pools")

    def scan_command(self, ip, command):
        """Отправляем команду на аппарат и получаем ответ."""
        try:
            HOST = ip.strip()
            PORT = 4028

            m = {"command": command}
            jdata = json.dumps(m)

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2)
                s.connect((HOST, PORT))
                s.sendall(bytes(jdata, encoding="utf-8"))
                data = ''
                while True:
                    chunk = s.recv(4026)
                    if not chunk:
                        break
                    data += chunk.decode("utf-8")

                datajs = json.loads(data[:-1])

                if command == "stats":
                    self.update_data(HOST, stats=datajs)
                elif command == "pools":
                    self.update_data(HOST, pools=datajs)

        except Exception:
            pass

    def update_data(self, ip, stats=None, pools=None):
        """Обновляем данные об аппарате и вызываем обновление в интерфейсе."""
        with self.scanned_data_lock:
            if ip not in self.scanned_data:
                self.scanned_data[ip] = {"stats": None, "pools": None}

            if stats:
                self.scanned_data[ip]["stats"] = stats
            if pools:
                self.scanned_data[ip]["pools"] = pools

            if self.scanned_data[ip]["stats"] and self.scanned_data[ip]["pools"]:
                self.update_tree(ip, self.scanned_data[ip])
                del self.scanned_data[ip]

    def update_tree(self, ip, data):
        """Формируем данные для отображения и вызываем callback для обновления интерфейса."""
        stats_data = data["stats"].get("STATS", [{}])
        pools_data = data["pools"].get("POOLS", [{}])

        stat = stats_data[0] if len(stats_data) > 0 else {}
        stat_s = stats_data[1] if len(stats_data) > 0 else {}
        pool_one = pools_data[0] if len(pools_data) > 0 else {}
        pool_two = pools_data[1] if len(pools_data) > 0 else {}
        pool_three = pools_data[2] if len(pools_data) > 0 else {}

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

        self.update_tree_callback(ip, values)

    def set_update_tree_callback(self, callback):
        """Устанавливаем callback для обновления интерфейса."""
        self.update_tree_callback = callback
