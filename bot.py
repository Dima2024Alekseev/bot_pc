import logging
import asyncio
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
    JobQueue,
)
from telegram import Update
from config import BOT_TOKEN
from handlers import (
    start_help,
    pc_control,
    monitoring,
    cleanup,
    screenshots,
    ai_responses,
)
from utils.decorators import restricted
from utils.state_manager import load_bot_state, save_bot_state

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

ANIMATION_FILE_ID = (
    "CgACAgIAAxkBAAIHzWiEpBDgtAJsQDpT6lPIN4lJVF6QAAI1dgACmrkpSF3sGXuJUNm4NgQ"
)


@restricted
async def toggle_battery_monitoring(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Включает/выключает автоматический мониторинг батареи."""
    chat_id = update.effective_chat.id
    job_name = f"battery_check_{chat_id}"

    if "battery_monitoring_enabled" not in context.bot_data:
        context.bot_data["battery_monitoring_enabled"] = False

    if "battery_low_notified" not in context.bot_data:
        context.bot_data["battery_low_notified"] = False
    if "battery_full_notified" not in context.bot_data:
        context.bot_data["battery_full_notified"] = False
    if "battery_unavailable_notified" not in context.bot_data:
        context.bot_data["battery_unavailable_notified"] = False
    if "battery_check_error_notified" not in context.bot_data:
        context.bot_data["battery_check_error_notified"] = False

    current_jobs = context.job_queue.get_jobs_by_name(job_name)

    if not current_jobs:
        context.job_queue.run_repeating(
            monitoring.check_battery_level,
            interval=300,
            first=10,
            chat_id=chat_id,
            name=job_name,
            data={"chat_id": chat_id},
        )
        context.bot_data["battery_monitoring_enabled"] = True
        await update.message.reply_text(
            "✅ Автоматический мониторинг батареи *включен* \\(проверка каждые 5 минут\\)\\.",
            parse_mode="MarkdownV2",
        )
        context.bot_data["battery_low_notified"] = False
        context.bot_data["battery_full_notified"] = False
        context.bot_data["battery_unavailable_notified"] = False
        context.bot_data["battery_check_error_notified"] = False
    else:
        for job in current_jobs:
            job.schedule_removal()
        context.bot_data["battery_monitoring_enabled"] = False
        await update.message.reply_text(
            "❌ Автоматический мониторинг батареи *выключен*\\.",
            parse_mode="MarkdownV2",
        )
        context.bot_data["battery_low_notified"] = False
        context.bot_data["battery_full_notified"] = False
        context.bot_data["battery_unavailable_notified"] = False
        context.bot_data["battery_check_error_notified"] = False

    save_bot_state(context.bot_data)


async def post_init(application: Application):
    """Функция, вызываемая после инициализации приложения, для загрузки состояния."""
    logger.info("Загрузка состояния бота после инициализации...")
    state = load_bot_state()
    application.bot_data.update(state)

    if application.bot_data.get("battery_monitoring_enabled"):
        from config import ALLOWED_CHAT_ID

        job_name = f"battery_check_{ALLOWED_CHAT_ID}"

        if not application.job_queue.get_jobs_by_name(job_name):
            application.job_queue.run_repeating(
                monitoring.check_battery_level,
                interval=300,
                first=10,
                chat_id=ALLOWED_CHAT_ID,
                name=job_name,
                data={"chat_id": ALLOWED_CHAT_ID},
            )
            logger.info(
                f"Автоматический мониторинг батареи восстановлен для chat_id: {ALLOWED_CHAT_ID}"
            )

    logger.info("Состояние бота успешно загружено и JobQueue настроен.")


def main() -> None:
    """Запускает бота."""
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    application.add_handler(CommandHandler("start", start_help.start))
    application.add_handler(CommandHandler("help", start_help.help_command))
    application.add_handler(CommandHandler("shutdown_now", pc_control.shutdown_now))
    application.add_handler(CommandHandler("reboot", pc_control.reboot))
    application.add_handler(CommandHandler("shutdown_timer", pc_control.shutdown_timer))
    application.add_handler(CommandHandler("cancel", pc_control.cancel_shutdown))
    application.add_handler(CommandHandler("status", monitoring.system_status))
    application.add_handler(CommandHandler("processes", monitoring.list_processes))
    application.add_handler(CommandHandler("uptime", monitoring.uptime))
    application.add_handler(
        CommandHandler("is_running", monitoring.check_process_running)
    )
    application.add_handler(
        CommandHandler("kill_process", monitoring.kill_process_command)
    )
    application.add_handler(CommandHandler("clear_temp", cleanup.clear_all_temp_files))
    application.add_handler(CommandHandler("screenshot", screenshots.screenshot))
    application.add_handler(CommandHandler("lock", pc_control.lock_pc))
    application.add_handler(CommandHandler("battery", monitoring.battery_status))
    application.add_handler(
        CommandHandler("toggle_battery_monitoring", toggle_battery_monitoring)
    )
    application.add_handler(CommandHandler("ask", ai_responses.ask_deepseek))

    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, start_help.button_handler)
    )

    application.add_handler(CallbackQueryHandler(start_help.inline_button_handler))

    logger.info("Бот запущен. Ожидание сообщений...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
