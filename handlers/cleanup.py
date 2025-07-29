import logging
import os
import shutil
import platform
from telegram import Update
from telegram.ext import ContextTypes
from utils.decorators import restricted

logger = logging.getLogger(__name__)


async def clear_temp_directory(path: str, chat_id: int, bot) -> tuple[int, int]:
    """
    Очищает содержимое указанной временной папки.
    Возвращает кортеж (количество удаленных файлов/папок, количество ошибок).
    """
    deleted_count = 0
    error_count = 0
    if not os.path.exists(path):
        logger.warning(f"Папка не найдена: {path}")
        return 0, 0

    await bot.send_message(
        chat_id=chat_id,
        text=f"🧹 Начинаю очистку папки: `{path}`",
        parse_mode="Markdown",
    )

    for item in os.listdir(path):
        item_path = os.path.join(path, item)
        try:
            if os.path.isfile(item_path):
                os.remove(item_path)
                deleted_count += 1
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
                deleted_count += 1
        except Exception as e:
            logger.error(f"Не удалось удалить {item_path}: {e}")
            error_count += 1

    return deleted_count, error_count


@restricted
async def clear_all_temp_files(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Обработчик для очистки временных файлов."""
    chat_id = update.effective_chat.id
    message_to_edit = None

    if update.message:
        message_to_edit = update.message
    elif update.callback_query and update.callback_query.message:
        message_to_edit = update.callback_query.message

    if message_to_edit:
        await message_to_edit.reply_text("⏳ Запускаю очистку временных файлов...")
    else:
        logger.error(
            "Нет объекта сообщения для отправки ответа в clear_all_temp_files. Отправляю обычное сообщение."
        )
        await context.bot.send_message(
            chat_id=chat_id, text="⏳ Запускаю очистку временных файлов..."
        )

    total_deleted = 0
    total_errors = 0

    user_temp_path = os.getenv("TEMP")
    if user_temp_path:
        deleted, errors = await clear_temp_directory(
            user_temp_path, chat_id, context.bot
        )
        total_deleted += deleted
        total_errors += errors
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"✅ Очистка `{user_temp_path}` завершена. Удалено: {deleted}, Ошибок: {errors}",
            parse_mode="Markdown",
        )
    else:
        await context.bot.send_message(
            chat_id=chat_id, text="❌ Переменная окружения %TEMP% не найдена."
        )

    if platform.system() == "Windows":
        system_temp_path = "C:\\Windows\\Temp"
        await context.bot.send_message(
            chat_id=chat_id,
            text="⚠️ Для очистки `C:\\Windows\\Temp` бот должен быть запущен с правами администратора.",
            parse_mode="Markdown",
        )
        deleted, errors = await clear_temp_directory(
            system_temp_path, chat_id, context.bot
        )
        total_deleted += deleted
        total_errors += errors
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"✅ Очистка `{system_temp_path}` завершена. Удалено: {deleted}, Ошибок: {errors}",
            parse_mode="Markdown",
        )

        prefetch_path = "C:\\Windows\\Prefetch"
        await context.bot.send_message(
            chat_id=chat_id,
            text="⚠️ Для очистки `C:\\Windows\\Prefetch` бот должен быть запущен с правами администратора. Обратите внимание, что это может временно замедлить запуск приложений после очистки.",
            parse_mode="Markdown",
        )
        deleted, errors = await clear_temp_directory(
            prefetch_path, chat_id, context.bot
        )
        total_deleted += deleted
        total_errors += errors
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"✅ Очистка `{prefetch_path}` завершена. Удалено: {deleted}, Ошибок: {errors}",
            parse_mode="Markdown",
        )
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text="ℹ️ Очистка системных временных файлов и папки Prefetch специфична для Windows. Для вашей ОС (Linux/macOS) эта функция не применяется к `C:\\Windows\\Temp` и `C:\\Windows\\Prefetch`.",
        )

    final_message = (
        f"🎉 Очистка временных файлов завершена!\n"
        f"Всего удалено элементов: {total_deleted}\n"
        f"Всего ошибок (файлы в использовании и т.п.): {total_errors}"
    )
    await context.bot.send_message(chat_id=chat_id, text=final_message)
