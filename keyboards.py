from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Основная клавиатура
def get_main_keyboard():
    keyboard = [
        [KeyboardButton("🖥 Мониторинг"), KeyboardButton("⚙️ Управление")],
        [KeyboardButton("🔐 Безопасность"), KeyboardButton("📷 Скриншот")],
        [KeyboardButton("🎮 Игровой режим"), KeyboardButton("❓ Помощь")] # Добавлена новая кнопка
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

# Клавиатура для мониторинга
def get_monitoring_keyboard():
    keyboard = [
        [KeyboardButton("📊 Статус системы"), KeyboardButton("⏱ Время работы")],
        [KeyboardButton("📋 Список процессов"), KeyboardButton("🔋 Батарея")],
        [KeyboardButton("🔙 Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

# Клавиатура для управления
def get_control_keyboard():
    keyboard = [
        [KeyboardButton("🔌 Выключить"), KeyboardButton("🔄 Перезагрузить")],
        [KeyboardButton("⏰ Таймер выключения"), KeyboardButton("❌ Отмена выключения")],
        [KeyboardButton("🧹 Очистить Временные файлы"), KeyboardButton("🔙 Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

# Клавиатура для безопасности
def get_security_keyboard():
    keyboard = [
        [KeyboardButton("🔒 Заблокировать ПК")],
        [KeyboardButton("🔙 Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

# Инлайн-клавиатура для подтверждения действия
def get_confirmation_keyboard(action: str):
    keyboard = [
        [
            InlineKeyboardButton("✅ Да", callback_data=f"confirm_{action}"),
            InlineKeyboardButton("❌ Нет", callback_data="cancel")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# Инлайн-клавиатура для выбора времени таймера выключения
def get_shutdown_timer_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("15 мин", callback_data="timer_15"),
            InlineKeyboardButton("30 мин", callback_data="timer_30"),
            InlineKeyboardButton("1 час", callback_data="timer_60")
        ],
        [
            InlineKeyboardButton("2 часа", callback_data="timer_120"),
            InlineKeyboardButton("3 часа", callback_data="timer_180"),
            InlineKeyboardButton("Отмена", callback_data="cancel")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# НОВАЯ КЛАВИАТУРА ДЛЯ ИГРОВОГО РЕЖИМА
def get_game_keyboard():
    keyboard = [
        [KeyboardButton("🚛 Euro Truck Simulator 2")],
        [KeyboardButton("⚔️ Assassins Creed Brotherhood")],
        [KeyboardButton("⚔️ Assassin's Creed Revelations")],
        [KeyboardButton("🔙 Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)