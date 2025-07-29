import logging
import psutil
import platform
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from utils.decorators import restricted
import time
from telegram.helpers import escape_markdown
from utils.state_manager import save_bot_state

# Проверка доступности модулей для скриншотов
try:
    import pyautogui
    from PIL import Image

    SCREENSHOT_AVAILABLE = True
except ImportError:
    SCREENSHOT_AVAILABLE = False
    logging.warning(
        "Функция скриншотов недоступна - отсутствуют зависимости (pyautogui, Pillow)"
    )

# Проверка доступности модулей для батареи
try:
    import psutil

    BATTERY_AVAILABLE = True
except ImportError:
    BATTERY_AVAILABLE = False
    logging.warning(
        "Функция мониторинга батареи недоступна - отсутствует зависимость (psutil)"
    )


logger = logging.getLogger(__name__)


@restricted
async def system_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет информацию о статусе системы."""
    cpu_percent = psutil.cpu_percent(interval=1)
    virtual_memory = psutil.virtual_memory()
    disk_usage = psutil.disk_usage("/")

    status_text = (
        f"💻 *Статус системы:*\n"
        f"CPU: `{cpu_percent:.1f}%`\n"
        f"RAM: `{virtual_memory.percent:.1f}%` использовано "
        # ИСПРАВЛЕНИЕ: Заменяем `\\))` на `\\)`
        f"\\({escape_markdown(f'{virtual_memory.used / (1024**3):.1f}', version=2)} ГБ из {escape_markdown(f'{virtual_memory.total / (1024**3):.1f}', version=2)} ГБ\\)\n"
        f"Диск C\\: `{disk_usage.percent:.1f}%` использовано "
        f"\\({escape_markdown(f'{disk_usage.used / (1024**3):.1f}', version=2)} ГБ из {escape_markdown(f'{disk_usage.total / (1024**3):.1f}', version=2)} ГБ\\)"
    )

    await update.message.reply_text(status_text, parse_mode="MarkdownV2")


@restricted
async def uptime(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Выводит время работы системы."""
    try:
        boot_time_timestamp = psutil.boot_time()
        boot_time = datetime.fromtimestamp(boot_time_timestamp)
        current_time = datetime.now()
        uptime_delta = current_time - boot_time

        days = uptime_delta.days
        hours, remainder = divmod(uptime_delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        uptime_message = (
            f"⏱ *Время работы системы:*\n"
            f"  `{days}` дней, `{hours:02}`:{minutes:02}:{seconds:02}"
        )
        await update.message.reply_text(uptime_message, parse_mode="MarkdownV2")
    except Exception as e:
        logger.error(f"Ошибка при получении времени работы: {e}")
        await update.message.reply_text(f"❌ Ошибка при получении времени работы: {e}")


@restricted
async def list_processes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет список наиболее ресурсоемких процессов."""
    chat_id = update.effective_chat.id

    sent_message = await context.bot.send_message(
        chat_id=chat_id,
        text=escape_markdown(
            "⏳ Собираю данные о процессах... Это может занять несколько секунд при первом запросе.",
            version=2,
        ),
        parse_mode="MarkdownV2",
    )

    try:
        for p in psutil.process_iter(["pid"]):
            try:
                _ = p.cpu_percent(interval=None)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        await asyncio.sleep(0.5)

        processes = []
        for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info"]):
            try:
                if p.status() == psutil.STATUS_ZOMBIE:
                    continue
                p_info = p.info
                processes.append(
                    {
                        "pid": p_info["pid"],
                        "name": p_info["name"],
                        "cpu_percent": p_info["cpu_percent"],
                        "memory_percent": p_info["memory_info"].rss
                        / psutil.virtual_memory().total
                        * 100,
                    }
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        processes.sort(
            key=lambda x: x["cpu_percent"] + x["memory_percent"], reverse=True
        )

        message_parts = []
        message_parts.append("*Наиболее активные процессы:*\n\n")

        message_parts.append("```\n")
        for i, p in enumerate(processes[:10]):
            line = (
                f"{i+1}. PID: {p['pid']}, {escape_markdown(p['name'], version=2)}, "  # Экранируем имя процесса, на всякий случай
                f"CPU: {escape_markdown(f'{p['cpu_percent']:.1f}%', version=2)}, "  # Экранируем CPU процент
                f"RAM: {escape_markdown(f'{p['memory_percent']:.1f}%', version=2)}\n"  # Экранируем RAM процент
            )
            message_parts.append(line)
        message_parts.append("```\n")

        message_parts.append(
            "_Для завершения процесса используйте_ `/kill_process \\[PID\\]`"
        )

        final_message_text = "".join(message_parts)

        await sent_message.edit_text(final_message_text, parse_mode="MarkdownV2")

    except Exception as e:
        logger.error(f"Ошибка при получении списка процессов: {e}")
        error_message = f"❌ Произошла ошибка при получении списка процессов: `{escape_markdown(str(e), version=2)}`"
        try:
            await sent_message.edit_text(error_message, parse_mode="MarkdownV2")
        except Exception as edit_error:
            logger.error(
                f"Не удалось отредактировать сообщение с ошибкой: {edit_error}"
            )
            await context.bot.send_message(
                chat_id=chat_id, text=error_message, parse_mode="MarkdownV2"
            )


@restricted
async def check_process_running(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Проверяет, запущен ли процесс по имени."""
    if not context.args:
        await update.message.reply_text(
            "Использование: `/is_running <имя_приложения>`", parse_mode="MarkdownV2"
        )
        return

    process_name = " ".join(context.args).lower()
    found = False
    for p in psutil.process_iter(["name"]):
        if process_name in p.info["name"].lower():
            await update.message.reply_text(
                f"✅ Процесс `{p.info['name']}` \\(PID: `{p.pid}`\\) *запущен*\\.",
                parse_mode="MarkdownV2",
            )
            found = True
            break
    if not found:
        await update.message.reply_text(
            f"❌ Процесс `{process_name}` *не найден*\\.", parse_mode="MarkdownV2"
        )


@restricted
async def kill_process_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Завершает процесс по PID с подтверждением."""
    if not context.args:
        await update.message.reply_text(
            "Использование: `/kill_process <PID>`", parse_mode="MarkdownV2"
        )
        return

    try:
        pid = int(context.args[0])
        context.user_data["kill_pid"] = pid

        try:
            process = psutil.Process(pid)
            process_info = f"Процесс: `{process.name()}` \\(PID: `{pid}`\\)"
        except psutil.NoSuchProcess:
            process_info = f"PID: `{pid}` (Процесс не найден или уже завершен)"

        reply_markup = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("✅ Да", callback_data="confirm_kill")],
                [InlineKeyboardButton("❌ Нет", callback_data="cancel")],
            ]
        )
        await update.message.reply_text(
            f"⚠️ Вы уверены, что хотите завершить {process_info}?",
            reply_markup=reply_markup,
            parse_mode="MarkdownV2",
        )

    except ValueError:
        await update.message.reply_text(
            "❌ PID должен быть числом\\.", parse_mode="MarkdownV2"
        )
    except Exception as e:
        logger.error(f"Ошибка при подготовке завершения процесса: {e}")
        await update.message.reply_text(f"❌ Ошибка: {e}")


async def execute_kill_process(
    update: Update, context: ContextTypes.DEFAULT_TYPE, pid: int
) -> None:
    """Выполняет завершение процесса после подтверждения."""
    try:
        process = psutil.Process(pid)
        process_name = process.name()
        process.terminate()
        process.wait(timeout=3)

        if process.is_running():
            process.kill()
            await update.callback_query.edit_message_text(
                f"☠️ Процесс `{process_name}` \\(PID: `{pid}`\\) *был принудительно завершен*\\.",
                parse_mode="MarkdownV2",
            )
            logger.info(f"Процесс {process_name} (PID: {pid}) принудительно завершен.")
        else:
            await update.callback_query.edit_message_text(
                f"✅ Процесс `{process_name}` \\(PID: `{pid}`\\) *успешно завершен*\\.",
                parse_mode="MarkdownV2",
            )
            logger.info(f"Процесс {process_name} (PID: {pid}) успешно завершен.")

    except psutil.NoSuchProcess:
        await update.callback_query.edit_message_text(
            f"❌ Процесс с PID `{pid}` *не найден или уже завершен*\\.",
            parse_mode="MarkdownV2",
        )
        logger.warning(f"Попытка завершить несуществующий процесс PID: {pid}")
    except psutil.AccessDenied:
        await update.callback_query.edit_message_text(
            f"❌ Отказано в доступе для завершения процесса с PID `{pid}`\\.",
            parse_mode="MarkdownV2",
        )
        logger.error(f"Отказано в доступе при завершении процесса PID: {pid}")
    except Exception as e:
        logger.error(f"Ошибка при завершении процесса PID {pid}: {e}")
        await update.callback_query.edit_message_text(
            f"❌ Неизвестная ошибка при завершении процесса `{pid}`: {escape_markdown(str(e), version=2)}",
            parse_mode="MarkdownV2",
        )


@restricted
async def battery_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет текущий статус батареи."""
    # Информация о батарее доступна только на Windows через psutil.
    if platform.system() == "Windows":
        try:
            battery = psutil.sensors_battery()
            if battery:
                status_text = (
                    f"🔋 *Состояние батареи:*\n" f"Заряд: `{battery.percent:.1f}%`\n"
                )

                if battery.power_plugged:
                    status_text += "Статус: Заряжается ⚡"
                elif battery.secsleft == psutil.POWER_TIME_UNLIMITED:
                    status_text += "Статус: Полностью заряжен ✅"
                elif battery.secsleft == psutil.POWER_TIME_UNKNOWN:
                    status_text += (
                        "Статус: Отключен от сети, оставшееся время неизвестно ⏳"
                    )
                else:
                    # Форматируем оставшееся время работы батареи.
                    minutes, seconds = divmod(int(battery.secsleft), 60)
                    hours, minutes = divmod(minutes, 60)
                    time_left_str = (
                        f"{hours}ч {minutes}м" if hours > 0 else f"{minutes}м"
                    )
                    status_text += f"Статус: Разряжается, осталось примерно `{escape_markdown(time_left_str, version=2)}` 📉"
            else:
                status_text = "❌ Информация о батарее недоступна \\(возможно, это ПК без батареи или нет поддержки\\)\\."
        except Exception as e:
            logger.error(f"Ошибка при получении информации о батарее: {e}")
            status_text = f"❌ Не удалось получить информацию о батарее: `{escape_markdown(str(e), version=2)}`"
    else:
        status_text = "❌ Информация о батарее доступна только для Windows\\."

    if update.message:
        await update.message.reply_text(status_text, parse_mode="MarkdownV2")
    elif update.callback_query:
        await update.callback_query.message.reply_text(
            status_text, parse_mode="MarkdownV2"
        )


async def check_battery_level(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Периодическая проверка уровня заряда батареи.
    Отправляет уведомления при низком заряде, полном заряде или недоступности.
    Флаги уведомлений теперь хранятся в context.bot_data.
    """
    chat_id = context.job.data["chat_id"]

    if "battery_low_notified" not in context.bot_data:
        context.bot_data["battery_low_notified"] = False
    if "battery_full_notified" not in context.bot_data:
        context.bot_data["battery_full_notified"] = False
    if "battery_unavailable_notified" not in context.bot_data:
        context.bot_data["battery_unavailable_notified"] = False
    if "battery_check_error_notified" not in context.bot_data:
        context.bot_data["battery_check_error_notified"] = False

    try:
        if not BATTERY_AVAILABLE:
            if not context.bot_data["battery_unavailable_notified"]:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="❌ Автоматический мониторинг батареи: модуль `psutil` не установлен.",
                )
                context.bot_data["battery_unavailable_notified"] = True
                save_bot_state(context.bot_data)
            return

        battery = psutil.sensors_battery()

        if battery is None:
            if not context.bot_data["battery_unavailable_notified"]:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="ℹ️ Автоматический мониторинг батареи: Информация о батарее недоступна. (Настольный ПК?)",
                )
                context.bot_data["battery_unavailable_notified"] = True
                context.bot_data["battery_check_error_notified"] = False
                save_bot_state(context.bot_data)
            return

        context.bot_data["battery_unavailable_notified"] = False
        context.bot_data["battery_check_error_notified"] = False

        if (
            battery.percent < 20
            and not battery.power_plugged
            and not context.bot_data["battery_low_notified"]
        ):
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"⚠️ *Внимание!* Низкий заряд батареи: `{battery.percent:.1f}%`\\. Подключите зарядное устройство\\.",
                parse_mode="MarkdownV2",
            )
            context.bot_data["battery_low_notified"] = True
            context.bot_data["battery_full_notified"] = False
            save_bot_state(context.bot_data)
            logger.info(
                f"Отправлено уведомление о низком заряде батареи: {battery.percent}%"
            )
        elif battery.percent >= 25 and context.bot_data["battery_low_notified"]:
            context.bot_data["battery_low_notified"] = False
            save_bot_state(context.bot_data)

        if (
            battery.percent > 95
            and battery.power_plugged
            and not context.bot_data["battery_full_notified"]
        ):
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"✅ Батарея заряжена до `{battery.percent:.1f}%`\\. Можно отключить зарядное устройство\\.",
                parse_mode="MarkdownV2",
            )
            context.bot_data["battery_full_notified"] = True
            context.bot_data["battery_low_notified"] = False
            save_bot_state(context.bot_data)
            logger.info(
                f"Отправлено уведомление о полном заряде батареи: {battery.percent}%"
            )
        elif battery.percent < 90 and context.bot_data["battery_full_notified"]:
            context.bot_data["battery_full_notified"] = False
            save_bot_state(context.bot_data)

    except Exception as e:
        logger.error(f"Ошибка в автоматической проверке батареи: {e}")
        if not context.bot_data["battery_check_error_notified"]:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"❌ Ошибка при автоматической проверке батареи: {e}",
            )
            context.bot_data["battery_check_error_notified"] = True
            save_bot_state(context.bot_data)
        context.bot_data["battery_low_notified"] = False
        context.bot_data["battery_full_notified"] = False
        context.bot_data["battery_unavailable_notified"] = False
