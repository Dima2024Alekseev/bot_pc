import logging
import psutil
import platform
import subprocess
import asyncio

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown

from utils.decorators import restricted

logger = logging.getLogger(__name__)

# Ваши существующие глобальные переменные для отслеживания состояния уведомлений батареи
# <--- ЭТИ СТРОКИ БЫЛИ УДАЛЕНЫ, ПОСКОЛЬКУ СОСТОЯНИЕ ТЕПЕРЬ ХРАНИТСЯ В context.bot_data
# battery_low_notified = False
# battery_full_notified = False


@restricted
async def system_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет информацию о статусе системы."""
    cpu_percent = psutil.cpu_percent(interval=1)
    virtual_memory = psutil.virtual_memory()
    disk_usage = psutil.disk_usage('/')

    status_text = (
        f"💻 *Статус системы:*\n"
        f"CPU: `{cpu_percent:.1f}%`\n"
        f"RAM: `{virtual_memory.percent:.1f}%` использовано "
        # ИСПРАВЛЕНИЕ: Заменяем `\\))` на `\\)`
        f"\\({escape_markdown(f'{virtual_memory.used / (1024**3):.1f}', version=2)} ГБ из {escape_markdown(f'{virtual_memory.total / (1024**3):.1f}', version=2)} ГБ\\)\n"
        f"Диск C\\: `{disk_usage.percent:.1f}%` использовано "
        f"\\({escape_markdown(f'{disk_usage.used / (1024**3):.1f}', version=2)} ГБ из {escape_markdown(f'{disk_usage.total / (1024**3):.1f}', version=2)} ГБ\\)"
    )

    await update.message.reply_text(status_text, parse_mode='MarkdownV2')


@restricted
async def uptime(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет время работы системы (uptime)."""
    boot_time = psutil.boot_time()
    uptime_seconds = int(psutil.time.time() - boot_time)

    # Вычисляем время работы в днях, часах, минутах, секундах.
    minutes, seconds = divmod(uptime_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)

    uptime_str = f"{days} дней, {hours} часов, {minutes} минут, {seconds} секунд"
    await update.message.reply_text(f"⏱ *Время работы системы:*\n`{escape_markdown(uptime_str, version=2)}`", parse_mode='MarkdownV2')


@restricted
async def list_processes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет список наиболее ресурсоемких процессов."""
    chat_id = update.effective_chat.id
    
    # Отправляем первое сообщение-заполнитель и сохраняем его объект.
    # Это сообщение будет отредактировано позже с фактическими данными.
    sent_message = await context.bot.send_message(
        chat_id=chat_id,
        # Экранируем начальное сообщение, т.к. parse_mode='MarkdownV2' используется
        text=escape_markdown("⏳ Собираю данные о процессах... Это может занять несколько секунд при первом запросе.", version=2),
        parse_mode='MarkdownV2'
    )

    try:
        # --- "Разогревочный" вызов для psutil.Process.cpu_percent() ---
        # Проходимся по всем процессам, чтобы psutil мог инициализировать свои внутренние счетчики.
        for p in psutil.process_iter(['pid']):
            try:
                _ = p.cpu_percent(interval=None)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        # Даем небольшую асинхронную паузу.
        await asyncio.sleep(0.5) 

        # --- Теперь собираем реальные данные о процессах ---
        processes = []
        for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
            try:
                if p.status() == psutil.STATUS_ZOMBIE:
                    continue
                p_info = p.info
                processes.append({
                    'pid': p_info['pid'],
                    'name': p_info['name'],
                    'cpu_percent': p_info['cpu_percent'],
                    'memory_percent': p_info['memory_info'].rss / psutil.virtual_memory().total * 100
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        processes.sort(key=lambda x: x['cpu_percent'] + x['memory_percent'], reverse=True)

        message_parts = []
        # Заголовок
        message_parts.append("*Наиболее активные процессы:*\n\n")
        
        # Начинаем многострочный блок кода (` ``` `), который игнорирует большинство правил MarkdownV2 внутри.
        # Это самое надежное решение для отображения табличных или кодовых данных.
        message_parts.append("```\n") 
        for i, p in enumerate(processes[:10]):
            # Внутри тройных кавычек нам по идее НЕ НУЖНО вручную экранировать точки или проценты.
            # Если проблема все еще возникала, это было избыточное, но необходимое экранирование.
            # Оставляем его, чтобы быть на 100% уверенными.
            line = (
                f"{i+1}. PID: {p['pid']}, {escape_markdown(p['name'], version=2)}, " # Экранируем имя процесса, на всякий случай
                f"CPU: {escape_markdown(f'{p['cpu_percent']:.1f}%', version=2)}, "   # Экранируем CPU процент
                f"RAM: {escape_markdown(f'{p['memory_percent']:.1f}%', version=2)}\n" # Экранируем RAM процент
            )
            message_parts.append(line)
        message_parts.append("```\n") # Закрываем многострочный блок кода

        # Инструкция в конце - должна быть экранирована, т.к. не в блоке кода.
        # Квадратные скобки `[` и `]` нужно экранировать в MarkdownV2, если они не являются частью ссылки.
        message_parts.append("_Для завершения процесса используйте_ `/kill_process \\[PID\\]`")

        final_message_text = "".join(message_parts)

        # Редактируем ранее отправленное сообщение-заполнитель с окончательными данными.
        await sent_message.edit_text(final_message_text, parse_mode='MarkdownV2')

    except Exception as e:
        logger.error(f"Ошибка при получении списка процессов: {e}")
        # Здесь также используем escape_markdown, потому что сообщение об ошибке может содержать спецсимволы.
        error_message = f"❌ Произошла ошибка при получении списка процессов: `{escape_markdown(str(e), version=2)}`"
        # В случае возникновения ошибки, пытаемся отредактировать сообщение-заполнитель
        try:
            await sent_message.edit_text(error_message, parse_mode='MarkdownV2')
        except Exception as edit_error:
            logger.error(f"Не удалось отредактировать сообщение с ошибкой: {edit_error}")
            await context.bot.send_message(chat_id=chat_id, text=error_message, parse_mode='MarkdownV2')


@restricted
async def check_process_running(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Проверяет, запущен ли процесс по имени."""
    if not context.args:
        await update.message.reply_text(
            "Пожалуйста, укажите имя процесса: `/is_running` \\[имя\\_процесса\\]",
            parse_mode='MarkdownV2'
        )
        return

    process_name = " ".join(context.args).lower()
    found = False
    for proc in psutil.process_iter(['name']):
        # Проверяем, содержит ли имя процесса (без учета регистра) указанное имя
        if proc.info['name'] and process_name in proc.info['name'].lower():
            await update.message.reply_text(
                f"✅ Процесс `{escape_markdown(proc.info['name'], version=2)}` \\(PID: `{proc.pid}`\\) запущен\\.",
                parse_mode='MarkdownV2'
            )
            found = True
            break
    if not found:
        await update.message.reply_text(
            f"❌ Процесс `{escape_markdown(process_name, version=2)}` не найден\\.",
            parse_mode='MarkdownV2'
        )


@restricted
async def kill_process_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Запрашивает PID для завершения процесса и подтверждение."""
    if not context.args:
        await update.message.reply_text(
            "Пожалуйста, укажите PID процесса для завершения: `/kill_process` \\[PID\\]",
            parse_mode='MarkdownV2'
        )
        return

    try:
        pid_to_kill = int(context.args[0])
        process_name = ""
        try:
            p = psutil.Process(pid_to_kill)
            process_name = p.name()
        except psutil.NoSuchProcess:
            await update.message.reply_text(f"❌ Процесс с PID `{pid_to_kill}` не найден\\.", parse_mode='MarkdownV2')
            return

        # Сохраняем PID в user_data для последующего использования в inline_button_handler.
        context.user_data['kill_pid'] = pid_to_kill
        # Создаем inline-клавиатуру для подтверждения.
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Подтвердить", callback_data="confirm_kill")],
            [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
        ])
        await update.message.reply_text(
            f"⚠️ Вы уверены, что хотите завершить процесс `{escape_markdown(process_name, version=2)}` \\(PID: `{pid_to_kill}`\\)\\?",
            reply_markup=keyboard,
            parse_mode='MarkdownV2'
        )
    except ValueError:
        await update.message.reply_text("❌ Пожалуйста, введите корректный PID \\(число\\)\\.", parse_mode='MarkdownV2')
    except Exception as e:
        logger.error(f"Ошибка в kill_process_command: {e}")
        await update.message.reply_text(f"❌ Произошла ошибка: `{escape_markdown(str(e), version=2)}`", parse_mode='MarkdownV2')

async def execute_kill_process(update: Update, context: ContextTypes.DEFAULT_TYPE, pid_to_kill: int) -> None:
    """Выполняет завершение процесса по PID."""
    try:
        p = psutil.Process(pid_to_kill)
        process_name = p.name()
        p.terminate() # Попытка завершить процесс
        await update.callback_query.edit_message_text(
            f"✅ Процесс `{escape_markdown(process_name, version=2)}` \\(PID: `{pid_to_kill}`\\) успешно завершен\\.",
            parse_mode='MarkdownV2'
        )
    except psutil.NoSuchProcess:
        await update.callback_query.edit_message_text(
            f"❌ Процесс с PID `{pid_to_kill}` уже не существует\\.",
            parse_mode='MarkdownV2'
        )
    except psutil.AccessDenied:
        await update.callback_query.edit_message_text(
            f"❌ Отказано в доступе к завершению процесса с PID `{pid_to_kill}`\\. Возможно, требуются права администратора\\.",
            parse_mode='MarkdownV2'
        )
    except Exception as e:
        logger.error(f"Ошибка при завершении процесса PID {pid_to_kill}: {e}")
        await update.callback_query.edit_message_text(
            f"❌ Не удалось завершить процесс с PID `{pid_to_kill}`: `{escape_markdown(str(e), version=2)}`",
            parse_mode='MarkdownV2'
        )


@restricted
async def battery_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет текущий статус батареи."""
    # Информация о батарее доступна только на Windows через psutil.
    if platform.system() == "Windows":
        try:
            battery = psutil.sensors_battery()
            if battery:
                status_text = f"🔋 *Состояние батареи:*\n" \
                              f"Заряд: `{battery.percent:.1f}%`\n"

                if battery.power_plugged:
                    status_text += "Статус: Заряжается ⚡"
                elif battery.secsleft == psutil.POWER_TIME_UNLIMITED:
                    status_text += "Статус: Полностью заряжен ✅"
                elif battery.secsleft == psutil.POWER_TIME_UNKNOWN:
                    status_text += "Статус: Отключен от сети, оставшееся время неизвестно ⏳"
                else:
                    # Форматируем оставшееся время работы батареи.
                    minutes, seconds = divmod(int(battery.secsleft), 60)
                    hours, minutes = divmod(minutes, 60)
                    time_left_str = f"{hours}ч {minutes}м" if hours > 0 else f"{minutes}м"
                    status_text += f"Статус: Разряжается, осталось примерно `{escape_markdown(time_left_str, version=2)}` 📉"
            else:
                status_text = "❌ Информация о батарее недоступна \\(возможно, это ПК без батареи или нет поддержки\\)\\."
        except Exception as e:
            logger.error(f"Ошибка при получении информации о батарее: {e}")
            status_text = f"❌ Не удалось получить информацию о батарее: `{escape_markdown(str(e), version=2)}`"
    else:
        status_text = "❌ Информация о батарее доступна только для Windows\\."

    # Отправляем сообщение в чат.
    if update.message:
        await update.message.reply_text(status_text, parse_mode='MarkdownV2')
    elif update.callback_query:
        await update.callback_query.message.reply_text(status_text, parse_mode='MarkdownV2')


async def check_battery_level(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Периодически проверяет уровень заряда батареи и отправляет уведомления."""
    # <--- ИЗМЕНЕНО: Теперь получаем значения из context.bot_data
    # Если их нет, используем False по умолчанию
    battery_low_notified = context.bot_data.get('battery_low_notified', False)
    battery_full_notified = context.bot_data.get('battery_full_notified', False)

    chat_id = context.job.data['chat_id']
    
    # Проверка актуальна только для Windows. Если ОС не Windows, отключаем задачу.
    if platform.system() != "Windows":
        if not context.user_data.get('battery_not_windows_notified', False):
            await context.bot.send_message(
                chat_id=chat_id,
                text="ℹ️ Автоматическая проверка батареи доступна только для Windows\\. Отключение функции\\.",
                parse_mode='MarkdownV2'
            )
            context.user_data['battery_not_windows_notified'] = True
        context.job.schedule_removal() # Удаляем задачу, если ОС не Windows
        return

    try:
        battery = psutil.sensors_battery()
        if battery:
            current_percent = battery.percent
            power_plugged = battery.power_plugged

            # Уведомление о низком заряде
            if current_percent <= 20 and not power_plugged and not battery_low_notified:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"🚨 *Внимание: Низкий заряд батареи* `{current_percent:.1f}%`\\! Подключите зарядное устройство\\.",
                    parse_mode='MarkdownV2'
                )
                # <--- ИЗМЕНЕНО: Сохраняем флаги в context.bot_data
                context.bot_data['battery_low_notified'] = True
                context.bot_data['battery_full_notified'] = False # Сбрасываем флаг полной батареи

            # Уведомление о полном заряде
            elif current_percent >= 99 and power_plugged and not battery_full_notified:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"✅ *Батарея полностью заряжена* `{current_percent:.1f}%`\\! Можно отключить зарядное устройство\\.",
                    parse_mode='MarkdownV2'
                )
                # <--- ИЗМЕНЕНО: Сохраняем флаги в context.bot_data
                context.bot_data['battery_full_notified'] = True
                context.bot_data['battery_low_notified'] = False # Сбрасываем флаг низкого заряда

            # Сброс флагов уведомлений, когда условия перестают выполняться
            elif current_percent > 20 and battery_low_notified:
                # <--- ИЗМЕНЕНО: Сбрасываем флаг в context.bot_data
                context.bot_data['battery_low_notified'] = False
            elif current_percent < 99 and battery_full_notified:
                # <--- ИЗМЕНЕНО: Сбрасываем флаг в context.bot_data
                context.bot_data['battery_full_notified'] = False

        else:
            # Если информация о батарее недоступна (например, на десктопе без батареи),
            # уведомляем один раз и отключаем периодическую проверку.
            if not context.user_data.get('battery_unavailable_notified', False):
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="❌ Информация о батарее недоступна\\. Отключение автоматической проверки\\.",
                    parse_mode='MarkdownV2'
                )
                context.user_data['battery_unavailable_notified'] = True
            context.job.schedule_removal() # Удаляем задачу, если батарея недоступна
            logger.warning("Информация о батарее недоступна. Автоматическая проверка отключена.")

    except Exception as e:
        logger.error(f"Ошибка при автоматической проверке батареи: {e}")
        # Уведомляем об ошибке и отключаем мониторинг, чтобы избежать повторяющихся ошибок.
        if not context.user_data.get('battery_check_error_notified', False):
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"⚠️ Произошла ошибка при автоматической проверке батареи: `{escape_markdown(str(e), version=2)}`\\. Отключение функции\\.",
                parse_mode='MarkdownV2'
            )
            context.user_data['battery_check_error_notified'] = True
        context.job.schedule_removal() # Удаляем задачу при ошибке