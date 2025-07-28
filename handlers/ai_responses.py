# handlers/ai_responses.py
import logging
from telegram import Update
from telegram.ext import ContextTypes
from openai import OpenAI
from openai import OpenAIError, APIStatusError # Импорт специфичных ошибок
from config import DEEPSEEK_API_KEY, ALLOWED_CHAT_ID
from utils.decorators import restricted

logger = logging.getLogger(__name__)

# Инициализация клиента DeepSeek API через OpenRouter
try:
    deepseek_client = OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url="https://openrouter.ai/api/v1" # <--- ИЗМЕНЕНИЕ ЗДЕСЬ! Используем URL OpenRouter
    )
    logger.info("Клиент DeepSeek AI (через OpenRouter) успешно инициализирован.")
except Exception as e:
    logger.error(f"Ошибка при инициализации клиента OpenRouter/DeepSeek AI: {e}", exc_info=True)
    deepseek_client = None


@restricted
async def ask_deepseek(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает запросы к DeepSeek AI через OpenRouter."""
    if deepseek_client is None:
        await update.message.reply_text(
            "Извините, сервис DeepSeek AI не настроен или произошла ошибка инициализации. Пожалуйста, сообщите администратору."
        )
        logger.error("Попытка использования DeepSeek AI, когда клиент не инициализирован.")
        return

    if len(context.args) == 0:
        await update.message.reply_text("Пожалуйста, укажите ваш запрос после команды /ask. Например: `/ask Расскажи анекдот.`")
        return

    user_query = " ".join(context.args)
    logger.info(f"Получен запрос к DeepSeek (через OpenRouter) от {update.effective_user.id}: {user_query}")

    try:
        await update.message.reply_chat_action("typing")
        
        # Важно! Здесь указывается ИМЯ модели, как её видит OpenRouter.
        # Для DeepSeek Chat обычно это "deepseek/deepseek-chat" или "deepseek-ai/deepseek-chat"
        # Уточните точное название модели на сайте OpenRouter.ai (в разделе моделей)
        response = deepseek_client.chat.completions.create(
            model="deepseek/deepseek-chat", # <--- ВАЖНО: имя модели для OpenRouter.ai
            messages=[
                {"role": "system", "content": "Вы умный и полезный помощник. Отвечайте на вопросы четко и по существу."},
                {"role": "user", "content": user_query}
            ],
            temperature=0.7,
            max_tokens=500
        )

        ai_response = response.choices[0].message.content

        logger.info(f"Получен ответ от DeepSeek AI (через OpenRouter): {ai_response[:100]}...")
        await update.message.reply_text(ai_response)

    except APIStatusError as e:
        logger.error(f"Ошибка OpenRouter/DeepSeek API (статус {e.status_code}): {e.response} (Request ID: {e.request_id})")
        await update.message.reply_text(f"Произошла ошибка при обращении к OpenRouter/DeepSeek AI: {e.status_code}. Возможно, проблема с API ключом, лимитами или названием модели. Пожалуйста, сообщите администратору.")
    except OpenAIError as e:
        logger.error(f"Ошибка OpenAI API клиента (через OpenRouter): {e}", exc_info=True)
        await update.message.reply_text("Произошла ошибка при обращении к OpenRouter/DeepSeek AI. Пожалуйста, попробуйте еще раз. (Ошибка API клиента)")
    except Exception as e:
        logger.error(f"Неизвестная ошибка при запросе к OpenRouter/DeepSeek AI: {e}", exc_info=True)
        await update.message.reply_text("Произошла непредвиденная ошибка при обработке вашего запроса к OpenRouter/DeepSeek AI. Пожалуйста, попробуйте еще раз.")