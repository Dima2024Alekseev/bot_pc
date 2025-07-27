# utils/decorators.py

from telegram import Update
from telegram.ext import ContextTypes
import logging
from config import ALLOWED_CHAT_ID # Импортируем из config

logger = logging.getLogger(__name__)

def restricted(func):
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id != ALLOWED_CHAT_ID:
            if update.message:
                await update.message.reply_text('⚠️ Доступ запрещён.')
            elif update.callback_query:
                await update.callback_query.message.reply_text('⚠️ Доступ запрещён.')
            logger.warning(f"Попытка доступа от неавторизованного пользователя: {user_id}")
            return
        return await func(update, context, *args, **kwargs)
    return wrapped