import subprocess
import sys
import time
import urllib.request
import socket
from datetime import datetime
import os

LOG_FILE = r"C:\Users\aleks\Desktop\bot\bot_launcher.log"


def log(message):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] {message}\n")
    except Exception as e:
        print(f"Не удалось записать лог: {str(e)}")


def check_internet_connection():
    """Улучшенная проверка интернет-соединения"""
    test_servers = [
        "http://8.8.8.8",  # Google DNS
        "http://1.1.1.1",  # Cloudflare DNS
        "http://ya.ru",  # Яндекс
        "http://google.com",  # Google
    ]

    for server in test_servers:
        try:
            urllib.request.urlopen(server, timeout=3)
            log(f"Соединение с {server} успешно")
            return True
        except Exception as e:
            log(f"Ошибка подключения к {server}: {str(e)}")
            continue

    return False


def wait_for_internet():
    """Ожидание интернета с улучшенной проверкой"""
    log("Начало проверки интернет-соединения")
    while not check_internet_connection():
        log("Интернет не обнаружен, повторная проверка через 5 сек...")
        time.sleep(5)


def main():
    try:
        log("Скрипт запущен")
        wait_for_internet()
        log("Запуск бота...")
        subprocess.Popen(
            [sys.executable, "C:/Users/aleks/Desktop/bot/bot.py"],
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        log("Бот успешно запущен")
    except Exception as e:
        log(f"КРИТИЧЕСКАЯ ОШИБКА: {str(e)}")
        print(f"Ошибка: {str(e)}")


if __name__ == "__main__":
    main()
