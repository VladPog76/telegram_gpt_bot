"""
Обработчик команды /talk - Диалог с известными личностями
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from utils.openai_helper import get_chatgpt_response_with_history
from utils.constants import CHOOSING_PERSON, TALKING_WITH_PERSON, PERSONALITIES

logger = logging.getLogger(__name__)


async def talk_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало диалога с личностью - выбор персонажа"""
    user = update.effective_user
    logger.info(f"Пользователь {user.first_name} ({user.id}) вызвал /talk")

    keyboard = []
    for key, person in PERSONALITIES.items():
        keyboard.append([InlineKeyboardButton(
            f"{person['emoji']} {person['name']}",
            callback_data=f"talk_choose_{key}"
        )])

    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        with open('images/talk.jpg', 'rb') as photo:
            await update.message.reply_photo(
                photo=photo,
                caption="🎭 Диалог с известной личностью\n\nВыбери, с кем хочешь поговорить:",
                reply_markup=reply_markup
            )
    except FileNotFoundError:
        await update.message.reply_text(
            "🎭 Диалог с известной личностью\n\nВыбери, с кем хочешь поговорить:",
            reply_markup=reply_markup
        )

    return CHOOSING_PERSON


async def talk_choose_person(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пользователь выбрал личность"""
    query = update.callback_query
    user = query.from_user
    await query.answer()

    person_key = query.data.replace("talk_choose_", "")
    person = PERSONALITIES.get(person_key)

    if not person:
        await query.message.reply_text("Ошибка выбора личности. Попробуй /talk снова.")
        return ConversationHandler.END

    context.user_data['person'] = person
    context.user_data['person_key'] = person_key
    context.user_data['conversation_history'] = [
        {"role": "system", "content": person['prompt']}
    ]

    logger.info(f"Пользователь {user.first_name} ({user.id}) выбрал {person['name']}")

    keyboard = [[InlineKeyboardButton("❌ Закончить диалог", callback_data="talk_end")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(
        f"{person['emoji']} Ты начал диалог с {person['name']}!\n\n"
        f"Задавай вопросы или просто общайся. Я буду отвечать в стиле этой личности.\n\n"
        f"Для завершения диалога нажми кнопку ниже.",
        reply_markup=reply_markup
    )

    return TALKING_WITH_PERSON


async def talk_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает сообщения в диалоге с личностью"""
    user = update.effective_user
    user_message = update.message.text

    person = context.user_data.get('person')
    conversation_history = context.user_data.get('conversation_history', [])

    if not person:
        await update.message.reply_text("Ошибка: личность не выбрана. Начни заново с /talk")
        return ConversationHandler.END

    logger.info(f"Пользователь {user.first_name} ({user.id}) в диалоге с {person['name']}: {user_message}")

    conversation_history.append({"role": "user", "content": user_message})

    await update.message.reply_text("⏳ Думаю...")

    response = get_chatgpt_response_with_history(conversation_history)

    conversation_history.append({"role": "assistant", "content": response})

    context.user_data['conversation_history'] = conversation_history

    keyboard = [[InlineKeyboardButton("❌ Закончить диалог", callback_data="talk_end")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"{person['emoji']} {response}",
        reply_markup=reply_markup
    )

    logger.info(f"Ответ отправлен пользователю {user.first_name} ({user.id})")

    return TALKING_WITH_PERSON


async def talk_end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение диалога с личностью"""
    query = update.callback_query
    user = query.from_user
    await query.answer()

    person = context.user_data.get('person')

    if person:
        logger.info(f"Пользователь {user.first_name} ({user.id}) завершил диалог с {person['name']}")
        await query.message.reply_text(
            f"👋 Диалог с {person['emoji']} {person['name']} завершен!\n\n"
            f"Используй /talk чтобы начать новый диалог или /start для главного меню."
        )
    else:
        await query.message.reply_text("Диалог завершен! Используй /start для главного меню.")

    context.user_data.clear()

    return ConversationHandler.END