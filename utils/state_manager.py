# utils/state_manager.py
import json
import os
import logging
from config import BOT_STATE_FILE

logger = logging.getLogger(__name__)

def load_bot_state() -> dict:
    """Загружает состояние бота из JSON-файла."""
    if os.path.exists(BOT_STATE_FILE):
        try:
            with open(BOT_STATE_FILE, 'r', encoding='utf-8') as f:
                state = json.load(f)
                logger.info(f"Состояние бота загружено из {BOT_STATE_FILE}: {state}")
                return state
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка декодирования JSON из {BOT_STATE_FILE}: {e}")
        except Exception as e:
            logger.error(f"Ошибка при загрузке состояния бота из {BOT_STATE_FILE}: {e}")
    else:
        logger.info(f"Файл состояния бота {BOT_STATE_FILE} не найден. Создаю пустое состояние.")
    return {
        'battery_monitoring_enabled': False,
        'battery_low_notified': False,
        'battery_full_notified': False,
        'battery_unavailable_notified': False,
        'battery_check_error_notified': False,
        # Добавляйте сюда другие состояния, которые нужно сохранять
    }

def save_bot_state(state: dict):
    """Сохраняет состояние бота в JSON-файл."""
    try:
        with open(BOT_STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=4, ensure_ascii=False)
        logger.info(f"Состояние бота сохранено в {BOT_STATE_FILE}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении состояния бота в {BOT_STATE_FILE}: {e}")