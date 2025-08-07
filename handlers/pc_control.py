import logging
import subprocess
import platform
import ctypes
import asyncio
import re
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from utils.decorators import restricted

logger = logging.getLogger(__name__)


@restricted
async def shutdown_now(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Немедленное выключение"""
    try:
        message_to_edit = None
        if hasattr(update, "callback_query") and update.callback_query.message:
            message_to_edit = update.callback_query.message
        elif update.message:
            message_to_edit = update.message

        if message_to_edit:
            await message_to_edit.reply_text("🔄 Выключаю компьютер...")
        else:
            logger.error("Нет объекта сообщения для отправки ответа.")

        if platform.system() == "Windows":
            subprocess.run(["shutdown", "/s", "/t", "0"])
        else:
            subprocess.run(["shutdown", "-h", "now"])
    except Exception as e:
        error_msg = f"❌ Ошибка: {e}"
        if message_to_edit:
            await message_to_edit.reply_text(error_msg)
        else:
            logger.error(f"Ошибка при выключении, не удалось отправить сообщение: {e}")


@restricted
async def reboot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Перезагрузка компьютера"""
    try:
        message_to_edit = None
        if hasattr(update, "callback_query") and update.callback_query.message:
            message_to_edit = update.callback_query.message
        elif update.message:
            message_to_edit = update.message

        if message_to_edit:
            await message_to_edit.reply_text("🔄 Перезагружаю компьютер...")
        else:
            logger.error("Нет объекта сообщения для отправки ответа.")

        if platform.system() == "Windows":
            subprocess.run(["shutdown", "/r", "/t", "0"])
        else:
            subprocess.run(["reboot"])
    except Exception as e:
        error_msg = f"❌ Ошибка: {e}"
        if message_to_edit:
            await message_to_edit.reply_text(error_msg)
        else:
            logger.error(
                f"Ошибка при перезагрузке, не удалось отправить сообщение: {e}"
            )


@restricted
async def lock_pc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Блокировка рабочего стола"""
    try:
        message_to_edit = None
        if hasattr(update, "callback_query") and update.callback_query.message:
            message_to_edit = update.callback_query.message
        elif update.message:
            message_to_edit = update.message

        if message_to_edit:
            await message_to_edit.reply_text("🔒 Блокирую компьютер...")
        else:
            logger.error("Нет объекта сообщения для отправки ответа.")

        if platform.system() == "Windows":
            subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"])
        elif platform.system() == "Linux":
            try:
                subprocess.run(["loginctl", "lock-session"], check=True)
            except subprocess.CalledProcessError:
                subprocess.run(["gnome-screensaver-command", "-l"], check=True)
        else:
            error_msg = "❌ Блокировка не поддерживается на этой системе"
            if message_to_edit:
                await message_to_edit.reply_text(error_msg)
            else:
                logger.warning(f"Блокировка не поддерживается: {platform.system()}")
            return

        if message_to_edit:
            await message_to_edit.reply_text("✅ Компьютер заблокирован.")

    except FileNotFoundError:
        error_msg = "❌ Команда блокировки не найдена. Убедитесь, что скринсейвер установлен и настроен."
        if message_to_edit:
            await message_to_edit.reply_text(error_msg)
    except Exception as e:
        error_msg = f"❌ Ошибка при блокировке: {e}"
        if message_to_edit:
            await message_to_edit.reply_text(error_msg)


@restricted
async def shutdown_timer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Выключение по таймеру"""
    if not context.args:
        await update.message.reply_text(
            "⏱️ Укажите время:\n"
            "Например:\n"
            "/shutdown_timer 60 - через 60 минут\n"
            f'/shutdown_timer {datetime.now().strftime("%H:%M")} - например, в {datetime.now().strftime("%H:%M")} (по текущему времени)'
        )
        return

    time_arg = " ".join(context.args).strip()

    try:
        seconds = 0
        if ":" in time_arg:
            if not re.fullmatch(r"^(0?[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$", time_arg):
                raise ValueError("Некорректный формат времени. Используйте HH:MM.")

            now = datetime.now()
            shutdown_time_target = datetime.strptime(time_arg, "%H:%M").replace(
                year=now.year, month=now.month, day=now.day, second=0, microsecond=0
            )

            if shutdown_time_target <= now:
                shutdown_time_target += timedelta(days=1)

            seconds = (shutdown_time_target - now).total_seconds()
        else:
            minutes = int(time_arg)
            if minutes <= 0:
                raise ValueError("Время в минутах должно быть положительным числом.")
            seconds = minutes * 60

        if seconds <= 0:
            await update.message.reply_text("⏳ Время должно быть в будущем!")
            return

        if (
            "shutdown_timer" in context.user_data
            and context.user_data["shutdown_timer"] is not None
        ):
            try:
                context.user_data["shutdown_timer"].remove()
                logger.info("Предыдущий таймер выключения отменен.")
            except Exception as e:
                logger.error(f"Не удалось отменить предыдущий таймер: {e}")
            del context.user_data["shutdown_timer"]

        job_data = {
            "chat_id": update.effective_chat.id,
            "message_id": update.message.message_id,
        }

        context.user_data["shutdown_timer"] = context.job_queue.run_once(
            shutdown_pc, seconds, name="shutdown_timer", data=job_data
        )

        shutdown_time_str = (datetime.now() + timedelta(seconds=seconds)).strftime(
            "%H:%M:%S"
        )
        await update.message.reply_text(
            f"⏰ Выключение запланировано на {shutdown_time_str}\n"
            f"(через {int(seconds//3600)} ч. {int((seconds%3600)//60)} мин. {int(seconds%60)} сек.)"
        )

    except ValueError as e:
        await update.message.reply_text(
            f"❌ {str(e)}\n\n"
            "Правильные форматы:\n"
            "• /shutdown_timer 60 - через 60 минут\n"
            f'• /shutdown_timer {datetime.now().strftime("%H:%M")} - например, в {datetime.now().strftime("%H:%M")} (по текущему времени)'
        )
    except Exception as e:
        logger.error(f"Ошибка при планировании таймера: {e}")
        await update.message.reply_text(
            f"❌ Неизвестная ошибка при планировании таймера: {e}"
        )


@restricted
async def cancel_shutdown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отмена запланированного выключения"""
    if (
        "shutdown_timer" in context.user_data
        and context.user_data["shutdown_timer"] is not None
    ):
        try:
            context.user_data["shutdown_timer"].remove()
            del context.user_data["shutdown_timer"]

            if platform.system() == "Windows":
                try:
                    proc = await asyncio.create_subprocess_shell(
                        "shutdown /a",
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        shell=True,
                    )
                    stdout, stderr = await proc.communicate()

                    decoded_stderr = stderr.decode("cp866", errors="replace")

                    if proc.returncode != 0:
                        logger.error(f"Ошибка отмены shutdown /a: {decoded_stderr}")
                except Exception as sub_e:
                    logger.error(f"Ошибка при запуске shutdown /a: {sub_e}")

            await update.message.reply_text("✅ Запланированное выключение отменено")
        except Exception as e:
            logger.error(f"Ошибка при отмене таймера: {e}")
            await update.message.reply_text(f"❌ Ошибка при отмене: {e}")
    else:
        await update.message.reply_text(
            "ℹ️ Нет активных таймеров выключения для отмены."
        )


async def shutdown_pc(context: ContextTypes.DEFAULT_TYPE):
    """Функция для выключения ПК, вызываемая таймером или по подтверждению"""
    chat_id = context.job.data.get("chat_id")
    message_id = context.job.data.get("message_id")

    try:
        if chat_id:
            if message_id:
                try:
                    await context.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=message_id,
                        text="🔌 Выключаю компьютер (таймер)...",
                    )
                except Exception as e:
                    logger.warning(
                        f"Не удалось отредактировать сообщение: {e}. Отправляю новое."
                    )
                    await context.bot.send_message(
                        chat_id=chat_id, text="🔌 Выключаю компьютер (таймер)..."
                    )
            else:
                await context.bot.send_message(
                    chat_id=chat_id, text="🔌 Выключаю компьютер (таймер)..."
                )
        else:
            logger.error("Нет chat_id для отправки ответа в shutdown_pc.")

        if platform.system() == "Windows":
            subprocess.run(["shutdown", "/s", "/t", "0"])
        else:
            subprocess.run(["shutdown", "-h", "now"])
    except Exception as e:
        error_msg = f"❌ Ошибка при выключении: {e}"
        if chat_id:
            await context.bot.send_message(chat_id=chat_id, text=error_msg)
        else:
            logger.error(f"Ошибка при выключении, не удалось отправить сообщение: {e}")


@restricted
async def flip_screen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Шуточная команда для переворота экрана (только Windows)"""
    try:
        if platform.system() != "Windows":
            await update.message.reply_text(
                "❌ Эта функция работает только на Windows!"
            )
            return

        # Инициализация библиотек Windows
        user32 = ctypes.WinDLL("user32")
        gdi32 = ctypes.WinDLL("gdi32")

        # Определяем константы
        DM_ORIENTATION = 0x00000001  # Поле для ориентации в DEVMODE
        CDS_TEST = 0x00000002  # Тестовый режим для проверки настроек
        CDS_UPDATEREGISTRY = 0x00000001  # Сохранить изменения в реестре
        DISP_CHANGE_SUCCESSFUL = 0
        DMDO_0 = 0  # Нормальная ориентация
        DMDO_180 = 2  # Перевернутая на 180 градусов

        # Определяем структуру DEVMODE
        class DEVMODE(ctypes.Structure):
            _fields_ = [
                ("dmDeviceName", ctypes.c_wchar * 32),
                ("dmSpecVersion", ctypes.c_ushort),
                ("dmDriverVersion", ctypes.c_ushort),
                ("dmSize", ctypes.c_ushort),
                ("dmDriverExtra", ctypes.c_ushort),
                ("dmFields", ctypes.c_uint),
                ("dmPositionX", ctypes.c_int),
                ("dmPositionY", ctypes.c_int),
                ("dmDisplayOrientation", ctypes.c_uint),
                ("dmDisplayFixedOutput", ctypes.c_uint),
                # Дополнительные поля для полной структуры DEVMODE
                ("dmColor", ctypes.c_short),
                ("dmDuplex", ctypes.c_short),
                ("dmYResolution", ctypes.c_short),
                ("dmTTOption", ctypes.c_short),
                ("dmCollate", ctypes.c_short),
                ("dmFormName", ctypes.c_wchar * 32),
                ("dmLogPixels", ctypes.c_ushort),
                ("dmBitsPerPel", ctypes.c_uint),
                ("dmPelsWidth", ctypes.c_uint),
                ("dmPelsHeight", ctypes.c_uint),
                ("dmDisplayFlags", ctypes.c_uint),
                ("dmDisplayFrequency", ctypes.c_uint),
            ]

        # Инициализируем DEVMODE
        devmode = DEVMODE()
        devmode.dmSize = ctypes.sizeof(DEVMODE)
        devmode.dmFields = DM_ORIENTATION

        # Получаем текущие настройки дисплея
        if user32.EnumDisplaySettingsW(None, 0, ctypes.byref(devmode)) == 0:
            error_code = ctypes.get_last_error()
            logger.error(f"Ошибка EnumDisplaySettingsW: код {error_code}")
            raise Exception(
                f"Не удалось получить текущие настройки дисплея: код ошибки {error_code}"
            )

        current_orientation = devmode.dmDisplayOrientation
        logger.info(f"Текущая ориентация: {current_orientation}")

        # Определяем новую ориентацию (0 = нормальная, 2 = 180°)
        new_orientation = DMDO_180 if current_orientation != DMDO_180 else DMDO_0
        devmode.dmDisplayOrientation = new_orientation

        await update.message.reply_text(
            f"🔄 {'Переворачиваю' if new_orientation == DMDO_180 else 'Возвращаю'} экран..."
        )

        # Проверяем возможность применения настроек
        result = user32.ChangeDisplaySettingsW(ctypes.byref(devmode), CDS_TEST)
        if result != DISP_CHANGE_SUCCESSFUL:
            logger.error(f"Тест изменения ориентации не удался: код {result}")
            raise Exception(f"Тест изменения ориентации не удался: код {result}")

        # Применяем настройки
        result = user32.ChangeDisplaySettingsW(
            ctypes.byref(devmode), CDS_UPDATEREGISTRY
        )
        if result != DISP_CHANGE_SUCCESSFUL:
            logger.error(f"Не удалось изменить ориентацию: код {result}")
            raise Exception(f"Не удалось изменить ориентацию: код {result}")

        await update.message.reply_text("✅ Экран перевернут.")
    except Exception as e:
        logger.error(f"Ошибка при перевороте экрана: {e}", exc_info=True)
        await update.message.reply_text(
            f"❌ Не удалось перевернуть экран: {e}\n"
            "Попробуйте вручную через настройки дисплея или Ctrl+Alt+стрелки"
        )

