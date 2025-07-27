import logging
import subprocess
import platform
import os
from datetime import datetime, timedelta

from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from telegram.ext import ContextTypes, filters
from telegram.helpers import escape_markdown

from keyboards import (
    get_main_keyboard,
    get_monitoring_keyboard,
    get_control_keyboard,
    get_security_keyboard,
    get_confirmation_keyboard,
    get_shutdown_timer_keyboard
)
from utils.decorators import restricted

import handlers.pc_control as pc_control
import handlers.monitoring as monitoring
import handlers.screenshots as screenshots
import handlers.cleanup as cleanup

logger = logging.getLogger(__name__)

# Ваш полученный file_id анимации
ANIMATION_FILE_ID = "CgACAgIAAxkBAAIHzWiEpBDgtAJsQDpT6lPIN4lJVF6QAAI1dgACmrkpSF3sGXuJUNm4NgQ"

@restricted
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start: отправляет GIF по file_id и главное меню."""
    user = update.effective_user
    logger.info(f"Пользователь {user.id} {user.full_name} использовал команду /start")

    # Создаем кнопки главного меню
    reply_markup = get_main_keyboard()

    try:
        # Отправляем анимацию, используя file_id
        await update.message.reply_animation(
            animation=ANIMATION_FILE_ID, # Используем file_id вместо чтения файла
            caption="Приветствую, *Администратор*\\! Выберите действие из меню ниже:",
            parse_mode='MarkdownV2',
            reply_markup=reply_markup # Прикрепляем кнопки к сообщению с GIF
        )
        logger.info(f"GIF-анимация успешно отправлена по file_id: {ANIMATION_FILE_ID}")
    except Exception as e:
        logger.error(f"Ошибка при отправке GIF-анимации по file_id {ANIMATION_FILE_ID}: {e}", exc_info=True)
        # В случае ошибки отправляем только текстовое сообщение с кнопками
        # Используем escape_markdown для безопасного отображения текста ошибки
        await update.message.reply_text(
            f"Произошла ошибка при отправке GIF-анимации: {escape_markdown(str(e), version=2)}. Отправляю только кнопки.",
            reply_markup=reply_markup,
            parse_mode='MarkdownV2'
        )

@restricted
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help"""
    help_text = (
        "📋 *Справка по командам*\n\n"
        "🔌 *Управление питанием:*\n"
        "\\- Выключение: `/shutdown_now` или кнопка 🔌\n"
        "\\- Перезагрузка: `/reboot` или кнопка 🔄\n"
        "\\- Таймер: `/shutdown_timer` \\[время\\] или кнопка ⏰\n\n"
        "📊 *Мониторинг:*\n"
        "\\- Статус: `/status` или кнопка 📊\n"
        "\\- Процессы: `/processes` или кнопка 📋\n"
        "\\- Время работы: `/uptime` или кнопка ⏱\n"
        "\\- Проверить запуск: `/is_running` \\[имя\\_приложения\\]\n"
        "\\- Батарея: `/battery` или кнопка 🔋\n"
        "\\- Авто\\-мониторинг батареи: `/toggle_battery_monitoring`\n\n"
        "🔐 *Безопасность:*\n"
        "\\- Блокировка: `/lock` или кнопка 🔒\n\n"
        "📷 *Скриншот:*\n"
        "\\- `/screenshot` или кнопка 📷\n\n"
        "🧹 *Очистка:*\n"
        "\\- `/clear_temp` или кнопка 🧹\n\n"
        "❌ *Отмена:*\n"
        "\\- `/cancel` \\- отмена запланированного выключения"
    )
    await update.message.reply_text(
        help_text,
        reply_markup=get_main_keyboard(),
        parse_mode='MarkdownV2'
    )

@restricted
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик текстовых кнопок"""
    query = update.message.text

    if query == "🖥 Мониторинг":
        await update.message.reply_text(
            "📊 *Мониторинг системы*",
            reply_markup=get_monitoring_keyboard(),
            parse_mode='MarkdownV2'
        )
    elif query == "⚙️ Управление":
        await update.message.reply_text(
            "⚙️ *Управление компьютером*",
            reply_markup=get_control_keyboard(),
            parse_mode='MarkdownV2'
        )
    elif query == "🔐 Безопасность":
        await update.message.reply_text(
            "🔐 *Безопасность*",
            reply_markup=get_security_keyboard(),
            parse_mode='MarkdownV2'
        )
    elif query == "📷 Скриншот":
        await screenshots.screenshot(update, context)
    elif query == "❓ Помощь":
        await help_command(update, context)
    elif query == "📊 Статус системы":
        await monitoring.system_status(update, context)
    elif query == "⏱ Время работы":
        await monitoring.uptime(update, context)
    elif query == "📋 Список процессов":
        await monitoring.list_processes(update, context)
    elif query == "🔋 Батарея":
        await monitoring.battery_status(update, context)
    elif query == "🔌 Выключить":
        await update.message.reply_text(
            "⚠️ Вы уверены, что хотите выключить компьютер?",
            reply_markup=get_confirmation_keyboard("shutdown")
        )
    elif query == "🔄 Перезагрузить":
        await update.message.reply_text(
            "⚠️ Вы уверены, что хотите перезагрузить компьютер?",
            reply_markup=get_confirmation_keyboard("reboot")
        )
    elif query == "⏰ Таймер выключения":
        await update.message.reply_text(
            "⏰ Выберите время до выключения:",
            reply_markup=get_shutdown_timer_keyboard()
        )
    elif query == "❌ Отмена выключения":
        await pc_control.cancel_shutdown(update, context)
    elif query == "🧹 Очистить Временные файлы":
        await cleanup.clear_all_temp_files(update, context)
    elif query == "🔒 Заблокировать ПК":
        await update.message.reply_text(
            "⚠️ Вы уверены, что хотите заблокировать компьютер?",
            reply_markup=get_confirmation_keyboard("lock")
        )
    elif query == "🔙 Назад":
        await start(update, context)

@restricted
async def inline_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик инлайн-кнопок"""
    query = update.callback_query
    chat_id = query.message.chat_id
    await query.answer()

    data = query.data

    if data.startswith("timer_"):
        minutes = int(query.data.split("_")[1])
        context.user_data['shutdown_minutes'] = minutes
        await query.edit_message_text(
            f"⏳ Компьютер выключится через {minutes} минут\\. Подтвердите:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Подтвердить", callback_data="confirm_timer")],
                [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
            ]),
            parse_mode='MarkdownV2'
        )
    elif data == "confirm_timer":
        minutes = context.user_data.get('shutdown_minutes', 30)
        seconds = minutes * 60

        if 'shutdown_timer' in context.user_data and context.user_data['shutdown_timer'] is not None:
            try:
                if hasattr(context.user_data['shutdown_timer'], 'job'):
                    context.user_data['shutdown_timer'].job.schedule_removal()
                else:
                    context.user_data['shutdown_timer'].schedule_removal()
                logger.info("Предыдущий таймер выключения отменен перед установкой нового.")
            except Exception as e:
                logger.error(f"Не удалось отменить предыдущий таймер: {e}")
            del context.user_data['shutdown_timer']

        job_data = {
            'chat_id': update.effective_chat.id,
            'message_id': query.message.message_id
        }
       
        context.user_data['shutdown_timer'] = context.job_queue.run_once(
            pc_control.shutdown_pc,
            seconds,
            name="shutdown_timer",
            data=job_data
        )

        shutdown_time = (datetime.now() + timedelta(minutes=minutes)).strftime('%H:%M')
        await query.edit_message_text(
            f"⏰ Выключение запланировано на {shutdown_time} \\(через {minutes} минут\\)",
            parse_mode='MarkdownV2'
        )
    elif data.startswith("confirm_"):
        action = query.data.split("_")[1]
        if action == "shutdown":
            await pc_control.shutdown_now(update, context)
        elif action == "reboot":
            await pc_control.reboot(update, context)
        elif action == "lock":
            await pc_control.lock_pc(update, context)
        elif action == "kill":
            pid = context.user_data.get('kill_pid')
            if pid:
                await monitoring.execute_kill_process(update, context, pid)
                del context.user_data['kill_pid']
            else:
                await query.edit_message_text("❌ Ошибка: PID для завершения не найден\\.", parse_mode='MarkdownV2')
        elif action == "clear_temp":
            await cleanup.clear_all_temp_files(update, context)
    elif data == "cancel":
        await query.edit_message_text("Действие отменено")
        if 'shutdown_timer' in context.user_data and context.user_data['shutdown_timer'] is not None:
            try:
                if hasattr(context.user_data['shutdown_timer'], 'job'):
                    context.user_data['shutdown_timer'].job.schedule_removal()
                else:
                    context.user_data['shutdown_timer'].schedule_removal()
                del context.user_data['shutdown_timer']
                if platform.system() == "Windows":
                    subprocess.run(["shutdown", "/a"], check=False)
                await query.message.reply_text('✅ Запланированное выключение отменено')
            except Exception as e:
                logger.error(f"Ошибка при отмене таймера: {e}")
                await query.message.reply_text(f"❌ Не удалось полностью отменить таймер: {escape_markdown(str(e), version=2)}")
        else:
            await query.message.reply_text('ℹ️ Нет активных таймеров выключения для отмены\\.', parse_mode='MarkdownV2')
    else:
        await query.message.reply_text('Неизвестное действие. Возвращаюсь в главное меню.', reply_markup=get_main_keyboard())