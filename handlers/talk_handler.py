"""
Обробник команди /talk - Діалог з відомими особистостями
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from utils.openai_helper import get_chatgpt_response_with_history
from utils.constants import CHOOSING_PERSON, TALKING_WITH_PERSON, PERSONALITIES

logger = logging.getLogger(__name__)


async def talk_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Початок діалогу з особою – вибір персонажа"""
    user = update.effective_user
    logger.info(f"Користувач {user.first_name} ({user.id}) натиснув /talk")

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
                caption="🎭 Діалог з відомою особою\n\nВибери, з ким хочеш поговорити:",
                reply_markup=reply_markup
            )
    except FileNotFoundError:
        await update.message.reply_text(
            "🎭 Діалог з відомою особою\n\nВибери, з ким хочеш поговорити:",
            reply_markup=reply_markup
        )

    return CHOOSING_PERSON


async def talk_choose_person(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Користувач вибрав особу"""
    query = update.callback_query
    user = query.from_user
    await query.answer()

    person_key = query.data.replace("talk_choose_", "")
    person = PERSONALITIES.get(person_key)

    if not person:
        await query.message.reply_text("Помилка вибору особи. Спробуй /Talk знову.")
        return ConversationHandler.END

    context.user_data['person'] = person
    context.user_data['person_key'] = person_key
    context.user_data['conversation_history'] = [
        {"role": "system", "content": person['prompt']}
    ]

    logger.info(f"Користувач {user.first_name} ({user.id}) вибрав {person['name']}")

    keyboard = [[InlineKeyboardButton("❌ Закінчити діалог", callback_data="talk_end")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(
        f"{person['emoji']} Ти почав діалог з {person['name']}!\n\n"
        f"Задавай питання або просто спілкуйся. Я відповідатиму в стилі цієї особи.\n\n"
        f"Для завершення діалогу натисніть кнопку нижче.",
        reply_markup=reply_markup
    )

    return TALKING_WITH_PERSON


async def talk_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробляє повідомлення у діалозі з особою"""
    user = update.effective_user
    user_message = update.message.text

    person = context.user_data.get('person')
    conversation_history = context.user_data.get('conversation_history', [])

    if not person:
        await update.message.reply_text("Помилка: особа не вибрана. Почни заново с /talk")
        return ConversationHandler.END

    logger.info(f"Користувач {user.first_name} ({user.id}) в діалозі з {person['name']}: {user_message}")

    conversation_history.append({"role": "user", "content": user_message})

    await update.message.reply_text("⏳ Думаю...")

    response = get_chatgpt_response_with_history(conversation_history)

    conversation_history.append({"role": "assistant", "content": response})

    context.user_data['conversation_history'] = conversation_history

    keyboard = [[InlineKeyboardButton("❌ Закінчити діалог", callback_data="talk_end")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"{person['emoji']} {response}",
        reply_markup=reply_markup
    )

    logger.info(f"Відповідь надіслано користувачу {user.first_name} ({user.id})")

    return TALKING_WITH_PERSON


async def talk_end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершення діалогу з особою"""
    query = update.callback_query
    user = query.from_user
    await query.answer()

    person = context.user_data.get('person')

    if person:
        logger.info(f"Користувач {user.first_name} ({user.id}) закінчив діалог з {person['name']}")
        await query.message.reply_text(
            f"👋 Діалог з {person['emoji']} {person['name']} закінчено!\n\n"
            f"Використовуйте /talk щоб почати новий діалог або /start для головного меню."
        )
    else:
        await query.message.reply_text("Діалог закінчено! Використовуйте /start для головного меню.")

    context.user_data.clear()

    return ConversationHandler.END
