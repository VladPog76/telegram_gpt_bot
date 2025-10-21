"""
Оброблювач команди /quiz - Квіз
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from utils.openai_helper import get_chatgpt_response
from utils.constants import CHOOSING_QUIZ_THEME, ANSWERING_QUIZ, QUIZ_THEMES

logger = logging.getLogger(__name__)


async def quiz_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Початок квізу - вибір теми"""
    user = update.effective_user
    logger.info(f"Користувач {user.first_name} ({user.id}) натиснув /quiz")

    context.user_data['quiz_score'] = 0
    context.user_data['quiz_total'] = 0

    keyboard = []
    for key, theme in QUIZ_THEMES.items():
        keyboard.append([InlineKeyboardButton(
            f"{theme['emoji']} {theme['name']}",
            callback_data=f"quiz_theme_{key}"
        )])

    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        with open('images/quiz.jpg', 'rb') as photo:
            await update.message.reply_photo(
                photo=photo,
                caption="🎮 Квіз!\n\nВибери тему для запитань:",
                reply_markup=reply_markup
            )
    except FileNotFoundError:
        await update.message.reply_text(
            "🎮 Квіз!\n\nВибери тему для запитань:",
            reply_markup=reply_markup
        )

    return CHOOSING_QUIZ_THEME


async def quiz_choose_theme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Користувач вибрав тему, генеруємо питання"""
    query = update.callback_query
    user = query.from_user
    await query.answer()

    theme_key = query.data.replace("quiz_theme_", "")
    theme = QUIZ_THEMES.get(theme_key)

    if not theme:
        await query.message.reply_text("Помилка вибору теми. Спробуй /quiz знов.")
        return ConversationHandler.END

    context.user_data['quiz_theme'] = theme
    context.user_data['quiz_theme_key'] = theme_key

    logger.info(f"Користувач {user.first_name} ({user.id}) вибрав тему {theme['name']}")

    await query.message.reply_text("⏳ Генерую питання...")

    prompt = f"Придумай одне цікаве питання для квіза на тему '{theme['name']}'. Питання має бути середньої складності. Напиши лише саме запитання, без відповіді."
    question = get_chatgpt_response(prompt)

    context.user_data['quiz_current_question'] = question

    score = context.user_data.get('quiz_score', 0)
    total = context.user_data.get('quiz_total', 0)

    await query.message.reply_text(
        f"{theme['emoji']} Тема: {theme['name']}\n"
        f"📊 Рахунок: {score}/{total}\n\n"
        f"❓ Питання:\n{question}\n\n"
        f"Напиши свою відповідь:"
    )

    return ANSWERING_QUIZ


async def quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Перевіряємо відповідь користувача"""
    user = update.effective_user
    user_answer = update.message.text

    question = context.user_data.get('quiz_current_question')
    theme = context.user_data.get('quiz_theme')

    if not question or not theme:
        await update.message.reply_text("Помилка квиза. Почни заново з /quiz")
        return ConversationHandler.END

    logger.info(f"Користувач {user.first_name} ({user.id}) відповів: {user_answer}")

    await update.message.reply_text("⏳ Перевіряю відповідь...")

    check_prompt = f"Питання квізу: {question}\nВідповідь користувача: {user_answer}\n\nПеревір, чи правильна відповідь. Відповідай ТІЛЬКИ 'Правильно' або 'Неправильно', а потім коротко поясни чому і дай правильну відповідь якщо потрібно."
    result = get_chatgpt_response(check_prompt)

    is_correct = result.lower().startswith("правильно")

    total = context.user_data.get('quiz_total', 0) + 1
    score = context.user_data.get('quiz_score', 0)

    if is_correct:
        score += 1
        emoji = "✅"
    else:
        emoji = "❌"

    context.user_data['quiz_score'] = score
    context.user_data['quiz_total'] = total

    keyboard = [
        [InlineKeyboardButton("➕ Ще питання", callback_data="quiz_more")],
        [InlineKeyboardButton("🔄 Змінити тему", callback_data="quiz_change_theme")],
        [InlineKeyboardButton("❌ Закінчити квіз", callback_data="quiz_end")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"{emoji} {result}\n\n"
        f"📊 Поточний рахунок: {score}/{total}",
        reply_markup=reply_markup
    )

    logger.info(f"Результат для {user.first_name} ({user.id}): {'Правильно' if is_correct else 'Неправильно'}")

    return ANSWERING_QUIZ


async def quiz_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробляє натискання кнопок у квізі"""
    query = update.callback_query
    user = query.from_user
    await query.answer()

    if query.data == "quiz_more":
        theme = context.user_data.get('quiz_theme')

        if not theme:
            await query.message.reply_text("Помилка. Почни квіз заново з /quiz")
            return ConversationHandler.END

        logger.info(f"Користувач {user.first_name} ({user.id}) хоче ще питання")

        await query.message.reply_text("⏳ Генерую нове питання...")

        prompt = f"Придумай одне цікаве питання для квіза на тему '{theme['name']}'. Питання має бути середньої складності. Напиши лише саме запитання, без відповіді."
        question = get_chatgpt_response(prompt)

        context.user_data['quiz_current_question'] = question

        score = context.user_data.get('quiz_score', 0)
        total = context.user_data.get('quiz_total', 0)

        await query.message.reply_text(
            f"{theme['emoji']} Тема: {theme['name']}\n"
            f"📊 Рахунок: {score}/{total}\n\n"
            f"❓ Питання:\n{question}\n\n"
            f"Напиши свою відповідь:"
        )

        return ANSWERING_QUIZ

    elif query.data == "quiz_change_theme":
        logger.info(f"Користувач {user.first_name} ({user.id}) змінює тему квиза")

        keyboard = []
        for key, theme in QUIZ_THEMES.items():
            keyboard.append([InlineKeyboardButton(
                f"{theme['emoji']} {theme['name']}",
                callback_data=f"quiz_theme_{key}"
            )])

        reply_markup = InlineKeyboardMarkup(keyboard)

        score = context.user_data.get('quiz_score', 0)
        total = context.user_data.get('quiz_total', 0)

        await query.message.reply_text(
            f"📊 Текущий счет: {score}/{total}\n\n"
            f"Вибери нову тему:",
            reply_markup=reply_markup
        )

        return CHOOSING_QUIZ_THEME

    elif query.data == "quiz_end":
        score = context.user_data.get('quiz_score', 0)
        total = context.user_data.get('quiz_total', 0)

        logger.info(f"Користувач {user.first_name} ({user.id}) завершив квіз. Рахунок: {score}/{total}")

        if total > 0:
            percentage = (score / total) * 100
            await query.message.reply_text(
                f"🎮 Квіз завершено!\n\n"
                f"📊 Підсумковий рахунок: {score}/{total} ({percentage:.1f}%)\n\n"
                f"Використовуйте /quiz щоб зіграти знову або /start для головного меню."
            )
        else:
            await query.message.reply_text(
                "🎮 Квіз завершено!\n\n"
                "Використовуйте /quiz щоб зіграти або /start для головного меню."
            )

        context.user_data.clear()

        return ConversationHandler.END