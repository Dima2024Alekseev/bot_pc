# handlers/screenshots.py

import logging
import os
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from utils.decorators import restricted # Импортируем restricted

# Проверка доступности модулей для скриншотов
try:
    import pyautogui
    from PIL import Image
    SCREENSHOT_AVAILABLE = True
except ImportError:
    SCREENSHOT_AVAILABLE = False
    logging.warning("Функция скриншотов недоступна - отсутствуют зависимости (pyautogui, Pillow)")

logger = logging.getLogger(__name__)

@restricted
async def screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Скриншот экрана с сохранением во временную папку"""
    if not SCREENSHOT_AVAILABLE:
        await update.message.reply_text(
            '❌ Функция скриншотов недоступна. Установите:\n'
            '`pip install pyautogui pillow`',
            parse_mode='Markdown'
        )
        return

    screenshot_path = None
    try:
        await update.message.reply_text('📸 Делаю скриншот...')
        
        temp_dir = os.path.join(os.environ.get('TEMP', os.path.expanduser('~')), 'pc_bot_screenshots')
        os.makedirs(temp_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        screenshot_path = os.path.join(temp_dir, f'screen_{timestamp}.png')
        
        pyautogui.screenshot(screenshot_path)
        
        with open(screenshot_path, 'rb') as photo:
            await update.message.reply_photo(
                photo=photo,
                caption='🖥 Текущий экран'
            )
            
    except Exception as e:
        await update.message.reply_text(f'❌ Ошибка при создании скриншота: {str(e)}')
    finally:
        if screenshot_path and os.path.exists(screenshot_path):
            try:
                os.remove(screenshot_path)
                logger.info(f"Временный файл скриншота удален: {screenshot_path}")
            except Exception as e:
                logger.error(f"Не удалось удалить временный файл скриншота {screenshot_path}: {e}")