# 💻 Telegram Бот для Удаленного Управления ПК

![GIF-анимация приветствия](https://github.com/Dima2024Alekseev/bot_pc/blob/main/preview.gif)

Этот Telegram-бот позволяет удаленно управлять вашим компьютером прямо из мессенджера. Он предоставляет широкий спектр функций: от выключения и перезагрузки до мониторинга системы, запуска игр и выполнения задач по очистке.

---

## ✨ Основные возможности

| Возможность | Описание |
|------------|----------|
| **Управление питанием** | Мгновенное выключение, перезагрузка, установка таймера выключения и его отмена. |
| **Мониторинг системы** | Получение информации о статусе ПК (CPU, RAM, диски), списке запущенных процессов, времени работы (uptime) и состоянии батареи. |
| **Безопасность** | Быстрая блокировка рабочего стола. |
| **Скриншоты** | Создание и отправка скриншотов текущего экрана. |
| **Запуск игр** | Удобный запуск предварительно настроенных игр (только для Windows). |
| **Очистка** | Удаление временных файлов для освобождения места и оптимизации системы. |
| **Автоматический мониторинг батареи** | Уведомления о низком заряде, полной зарядке и других статусах батареи. |
| **AI-помощник** | Интеграция с DeepSeek для получения ответов на ваши вопросы. |

---

## 🚀 Установка

Для развертывания бота на вашем компьютере выполните следующие шаги:

Прежде всего, вам нужно **создать своего Telegram-бота** и получить необходимые данные, а также настроить **API-ключ для DeepSeek (опционально)**:

1. **Создайте бота через BotFather**: Откройте Telegram, найдите [@BotFather](https://t.me/BotFather) и следуйте инструкциям для создания нового бота (`/newbot`). В конце вы получите **токен вашего бота** (например, `123456:ABC-DEF1234ghIkl-zyx57W2v1u123er`). Сохраните его, он понадобится позже.
2. **Узнайте свой ID чата**: Отправьте любое сообщение только что созданному боту. Затем найдите [@userinfobot](https://t.me/userinfobot) в Telegram и отправьте ему команду `/start`. Бот покажет ваш **числовой ID чата** (например, `123456789`). Этот ID нужен, чтобы только вы могли управлять ботом.
3. **Получите API-ключ DeepSeek (для AI-помощника)**: Чтобы узнать, как получить API-ключ DeepSeek, перейдите по ссылке на видео: [Как получить API-ключ DeepSeek](https://youtu.be/j0VfsZxdUEg?si=2wJhjctIDcOZ_I6x). Если вы не планируете использовать AI-помощника, этот шаг можно пропустить.

Теперь, откройте терминал или командную строку и **клонируйте репозиторий**:

```bash
git clone https://github.com/Dima2024Alekseev/bot_pc.git
cd bot_pc
```

Далее установите все необходимые зависимости из уже существующего файла requirements.txt. Выполните в терминале:

```bash
pip install -r requirements.txt
```

Настройте шифрование и config.json. Ваш бот использует шифрование для защиты конфиденциальных данных, таких как токены и ID чата. Сначала сгенерируйте ключ шифрования, создав файл generate_key.py в корневой папке проекта:

```python
# config_generator.py
import os
import json
from cryptography.fernet import Fernet

def generate_key():
    """Генерирует ключ шифрования и сохраняет его в файл."""
    key = Fernet.generate_key()
    with open("encryption_key.key", "wb") as key_file:
        key_file.write(key)
    print("Ключ шифрования сгенерирован и сохранен в 'encryption_key.key'")
    return key

def load_key():
    """Загружает ключ шифрования из файла."""
    try:
        with open("encryption_key.key", "rb") as key_file:
            key = key_file.read()
        return key
    except FileNotFoundError:
        return None # Ключа нет, нужно сгенерировать

def encrypt_data(data, key):
    """Шифрует строку данных."""
    f = Fernet(key)
    return f.encrypt(data.encode()).decode()

def main():
    print("--- Настройка шифрованных данных бота ---")
    # --- 1. Генерация/загрузка ключа шифрования ---
    key = load_key()
    if key is None:
        key = generate_key()
    # --- 2. Шифрование токена и ID чата ---
    bot_token = input("Введите токен вашего Telegram бота (ОБЯЗАТЕЛЬНО): ")
    allowed_chat_id_str = input("Введите ID разрешенного чата (обычно ваш ID пользователя, ОБЯЗАТЕЛЬНО): ")
    deepseek_api_key = input("Введите ваш DeepSeek API Key (ОБЯЗАТЕЛЬНО для AI функционала): ") # ДОБАВЛЕНО
    try:
        allowed_chat_id = int(allowed_chat_id_str)
    except ValueError:
        print("Ошибка: ID чата должен быть числом.")
        return
    encrypted_token = encrypt_data(bot_token, key)
    encrypted_chat_id = encrypt_data(str(allowed_chat_id), key)
    encrypted_deepseek_api_key = encrypt_data(deepseek_api_key, key) # ДОБАВЛЕНО
    config_data = {
        "BOT_TOKEN": encrypted_token,
        "ALLOWED_CHAT_ID": encrypted_chat_id,
        "DEEPSEEK_API_KEY": encrypted_deepseek_api_key # ДОБАВЛЕНО
    }
    # Сохраняем зашифрованные данные в config.json
    with open("config.json", "w") as f:
        json.dump(config_data, f, indent=4)
    print("\nВаши BOT_TOKEN, ALLOWED_CHAT_ID и DEEPSEEK_API_KEY зашифрованы и сохранены в 'config.json'.")
    print("Убедитесь, что файл 'encryption_key.key' добавлен в .gitignore и надежно хранится.")
    print("Вы можете удалить 'config_generator.py' после использования.")

if __name__ == "__main__":
    main()
```

Запустите его из терминала:

```bash
python generate_key.py
```

В результате будет создан файл encryption_key.key. Не потеряйте его! Без этого ключа вы не сможете расшифровать свою конфигурацию.

Затем зашифруйте свои данные и создайте config.json. Создайте файл encrypt_config.py в корневой папке проекта:

```python
# encrypt_config.py
import json
from cryptography.fernet import Fernet
import os

# !!! ОБЯЗАТЕЛЬНО ИЗМЕНИТЕ ЭТОТ ПУТЬ на путь к вашей папке с ботом !!!
PROJECT_DIR = r"C:\Users\aleks\Desktop\bot"
KEY_PATH = os.path.join(PROJECT_DIR, "encryption_key.key")
CONFIG_PATH = os.path.join(PROJECT_DIR, "config.json")

def load_encryption_key():
    with open(KEY_PATH, "rb") as key_file:
        return key_file.read()

def encrypt_data(data: str, key: bytes) -> str:
    f = Fernet(key)
    return f.encrypt(data.encode()).decode()

key = load_encryption_key()

# !!! ЗАМЕНИТЕ ЭТИ ЗНАЧЕНИЯ НА СВОИ АКТУАЛЬНЫЕ ДАННЫЕ !!!
bot_token_raw = "ВАШ_ТОКЕН_БОТА_ЗДЕСЬ" # Получите у @BotFather
allowed_chat_id_raw = "ВАШ_ID_ЧАТА_ЗДЕСЬ" # Получите у @userinfobot (в виде строки)
deepseek_api_key_raw = "ВАШ_DEEPSEEK_API_КЛЮЧ_ЗДЕСЬ" # Ваш API-ключ DeepSeek (оставьте "" если не используете)

encrypted_config = {
    "BOT_TOKEN": encrypt_data(bot_token_raw, key),
    "ALLOWED_CHAT_ID": encrypt_data(allowed_chat_id_raw, key),
    "DEEPSEEK_API_KEY": encrypt_data(deepseek_api_key_raw, key) if deepseek_api_key_raw else "",
}

with open(CONFIG_PATH, "w") as f:
    json.dump(encrypted_config, f, indent=4)

print(f"Конфигурация зашифрована и сохранена в {CONFIG_PATH}")
print("Убедитесь, что переменная PROJECT_DIR в вашем основном файле config.py соответствует этому пути.")
```

Обязательно:
- Измените `PROJECT_DIR` в этом скрипте на реальный путь к вашей папке с ботом (например, `r"C:\Users\aleks\Desktop\bot"`).
- Замените плейсхолдеры (`ВАШ_ТОКЕН_БОТА_ЗДЕСЬ`, `ВАШ_ID_ЧАТА_ЗДЕСЬ`, `ВАШ_DEEPSEEK_API_КЛЮЧ_ЗДЕСЬ`) на ваши фактические данные, которые вы получили ранее.
- Ваш `ALLOWED_CHAT_ID` должен быть передан как строка, даже если это число, чтобы его можно было зашифровать.

Запустите этот скрипт из терминала:

```bash
python encrypt_config.py
```

Он создаст файл config.json с вашими зашифрованными данными.

После этого, проверьте ваш основной файл config.py. Убедитесь, что переменная `PROJECT_DIR` точно указывает на вашу корневую папку с ботом. Это критически важно для правильной загрузки ключа и конфигурации.

```python
PROJECT_DIR = r"C:\Users\aleks\Desktop\bot" # Убедитесь, что это правильный и актуальный путь!
# Остальные пути будут построены относительно PROJECT_DIR
```

Настройте пути к играм (только для Windows). Откройте файл handlers/start_help.py и обновите словарь `GAME_PATHS` с актуальными путями к .lnk файлам или исполняемым файлам ваших игр:

```python
GAME_PATHS = {
    "🚛 Euro Truck Simulator 2": r"C:\Users\aleks\Desktop\GAME\(64х)Euro Truck Simulator 2.lnk",
    "⚔️ Assassins Creed Brotherhood": r"C:\Users\aleks\Desktop\GAME\Assassins Creed Brotherhood.lnk",
    "⚔️ Assassin's Creed Revelations": r"C:\Users\aleks\Desktop\GAME\Assassin's Creed.Revelations.v 1.03 + 6 DLC.lnk",
    # Добавьте другие игры по аналогии
}
```

Наконец, запустите бота. Для наиболее надежного запуска, включая автоматическую проверку интернет-соединения и фоновый режим, используйте скрипт start_bot.py:

```bash
python start_bot.py
```

Примечание: Убедитесь, что пути к файлам в start_bot.py (LOG_FILE и путь к bot.py) соответствуют вашей системе.

Вы также можете запустить бот напрямую через bot.py (но тогда не будет автоматической проверки интернета и возможности фонового запуска):

```bash
python bot.py
```

---

## 🔒 Безопасность

Все данные хранятся в зашифрованном виде. Обязательно добавьте в .gitignore:

```
encryption_key.key
config.json
/venv/
__pycache__/
```

## 🤖 Использование

После запуска бота, откройте приложение Telegram и найдите вашего бота по его имени. Вы можете взаимодействовать с ним, отправляя команды или используя удобное кнопочное меню:

- `/start` - Приветствие и главное меню бота.
- `/help` - Полный список всех доступных команд с кратким описанием.

Используйте кнопки в меню Telegram для навигации по функциям бота и выполнения действий.
