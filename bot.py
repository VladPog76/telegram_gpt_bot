"""
Головний файл бота - ініціалізація та запуск
"""
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

from config import TELEGRAM_TOKEN

# Импорт handlers
from handlers.basic import start, help_command
from handlers.gpt_handler import gpt_start, gpt_question, gpt_button_handler, gpt_voice
from handlers.random_handler import random_fact, random_button_handler
from handlers.talk_handler import (
    talk_start, talk_choose_person, talk_conversation, talk_end
)
from handlers.quiz_handler import (
    quiz_start, quiz_choose_theme, quiz_answer, quiz_button_handler
)
from handlers.translate_handler import (
    translate_start, translate_choose_language,
    translate_text, translate_voice, translate_button_handler
)
from handlers.voice_handler import handle_voice

# Импорт констант
from utils.constants import (
    WAITING_GPT_QUESTION, CHOOSING_PERSON, TALKING_WITH_PERSON,
    CHOOSING_QUIZ_THEME, ANSWERING_QUIZ,
    CHOOSING_LANGUAGE, TRANSLATING
)

# 🧩 Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('telegram').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


# 🚨 Глобальный обработчик ошибок
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробляє всі помилки в роботі"""
    logger.error(f"Виникла помилка: {context.error}", exc_info=context.error)

    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "😔 Виникла помилка при обробці запиту.\n"
                "Спробуй знову або використовуй /start"
            )
        except Exception:
            pass


def main():
    """🚀 Запуск боту"""
    logger.info("Запуск боту...")

    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Регистрируем базовые команды
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    gpt_handler = ConversationHandler(
        entry_points=[CommandHandler("gpt", gpt_start)],
        states={
            WAITING_GPT_QUESTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, gpt_question),
                MessageHandler(filters.VOICE, gpt_voice),
                CallbackQueryHandler(gpt_button_handler, pattern="^gpt_")
            ]
        },
        fallbacks=[CommandHandler("start", start)]
    )

    application.add_handler(gpt_handler)

    # Обработчик команды /random
    application.add_handler(CommandHandler("random", random_fact))
    application.add_handler(CallbackQueryHandler(random_button_handler, pattern="^random_"))

    # ConversationHandler для /talk
    talk_handler = ConversationHandler(
        entry_points=[CommandHandler("talk", talk_start)],
        states={
            CHOOSING_PERSON: [
                CallbackQueryHandler(talk_choose_person, pattern="^talk_choose_")
            ],
            TALKING_WITH_PERSON: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, talk_conversation),
                CallbackQueryHandler(talk_end, pattern="^talk_end$")
            ]
        },
        fallbacks=[CommandHandler("start", start)]
    )
    application.add_handler(talk_handler)

    # ConversationHandler для /quiz
    quiz_handler = ConversationHandler(
        entry_points=[CommandHandler("quiz", quiz_start)],
        states={
            CHOOSING_QUIZ_THEME: [
                CallbackQueryHandler(quiz_choose_theme, pattern="^quiz_theme_")
            ],
            ANSWERING_QUIZ: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, quiz_answer),
                CallbackQueryHandler(quiz_button_handler, pattern="^quiz_")
            ]
        },
        fallbacks=[CommandHandler("start", start)]
    )
    application.add_handler(quiz_handler)

    # ConversationHandler для /translate
    translate_handler = ConversationHandler(
        entry_points=[CommandHandler("translate", translate_start)],
        states={
            CHOOSING_LANGUAGE: [
                CallbackQueryHandler(translate_choose_language, pattern="^translate_lang_")
            ],
            TRANSLATING: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, translate_text),
                MessageHandler(filters.VOICE, translate_voice),
                CallbackQueryHandler(translate_button_handler, pattern="^translate_")
            ]
        },
        fallbacks=[CommandHandler("start", start)]
    )
    application.add_handler(translate_handler)

    # Обработчик голосовых сообщений (вне других режимов)
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))

    # Регистрируем обработчик ошибок
    application.add_error_handler(error_handler)

    logger.info("Бот успішно запущений та чекає команди.")
    application.run_polling()


if __name__ == "__main__":
    main()
