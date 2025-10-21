"""
Обработчик команды /quiz - Квиз
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from utils.openai_helper import get_chatgpt_response
from utils.constants import CHOOSING_QUIZ_THEME, ANSWERING_QUIZ, QUIZ_THEMES

logger = logging.getLogger(__name__)


async def quiz_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало квиза - выбор темы"""
    user = update.effective_user
    logger.info(f"Пользователь {user.first_name} ({user.id}) вызвал /quiz")

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
                caption="🎮 Квиз!\n\nВыбери тему для вопросов:",
                reply_markup=reply_markup
            )
    except FileNotFoundError:
        await update.message.reply_text(
            "🎮 Квиз!\n\nВыбери тему для вопросов:",
            reply_markup=reply_markup
        )

    return CHOOSING_QUIZ_THEME


async def quiz_choose_theme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пользователь выбрал тему, генерируем вопрос"""
    query = update.callback_query
    user = query.from_user
    await query.answer()

    theme_key = query.data.replace("quiz_theme_", "")
    theme = QUIZ_THEMES.get(theme_key)

    if not theme:
        await query.message.reply_text("Ошибка выбора темы. Попробуй /quiz снова.")
        return ConversationHandler.END

    context.user_data['quiz_theme'] = theme
    context.user_data['quiz_theme_key'] = theme_key

    logger.info(f"Пользователь {user.first_name} ({user.id}) выбрал тему {theme['name']}")

    await query.message.reply_text("⏳ Генерирую вопрос...")

    prompt = f"Придумай один интересный вопрос для квиза на тему '{theme['name']}'. Вопрос должен быть средней сложности. Напиши только сам вопрос, без ответа."
    question = get_chatgpt_response(prompt)

    context.user_data['quiz_current_question'] = question

    score = context.user_data.get('quiz_score', 0)
    total = context.user_data.get('quiz_total', 0)

    await query.message.reply_text(
        f"{theme['emoji']} Тема: {theme['name']}\n"
        f"📊 Счет: {score}/{total}\n\n"
        f"❓ Вопрос:\n{question}\n\n"
        f"Напиши свой ответ:"
    )

    return ANSWERING_QUIZ


async def quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверяем ответ пользователя"""
    user = update.effective_user
    user_answer = update.message.text

    question = context.user_data.get('quiz_current_question')
    theme = context.user_data.get('quiz_theme')

    if not question or not theme:
        await update.message.reply_text("Ошибка квиза. Начни заново с /quiz")
        return ConversationHandler.END

    logger.info(f"Пользователь {user.first_name} ({user.id}) ответил: {user_answer}")

    await update.message.reply_text("⏳ Проверяю ответ...")

    check_prompt = f"Вопрос квиза: {question}\nОтвет пользователя: {user_answer}\n\nПроверь, правильный ли ответ. Ответь ТОЛЬКО 'Правильно' или 'Неправильно', а затем кратко объясни почему и дай правильный ответ если нужно."
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
        [InlineKeyboardButton("➕ Еще вопрос", callback_data="quiz_more")],
        [InlineKeyboardButton("🔄 Сменить тему", callback_data="quiz_change_theme")],
        [InlineKeyboardButton("❌ Закончить квиз", callback_data="quiz_end")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"{emoji} {result}\n\n"
        f"📊 Текущий счет: {score}/{total}",
        reply_markup=reply_markup
    )

    logger.info(f"Результат для {user.first_name} ({user.id}): {'Правильно' if is_correct else 'Неправильно'}")

    return ANSWERING_QUIZ


async def quiz_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает нажатия на кнопки в квизе"""
    query = update.callback_query
    user = query.from_user
    await query.answer()

    if query.data == "quiz_more":
        theme = context.user_data.get('quiz_theme')

        if not theme:
            await query.message.reply_text("Ошибка. Начни квиз заново с /quiz")
            return ConversationHandler.END

        logger.info(f"Пользователь {user.first_name} ({user.id}) запросил еще вопрос")

        await query.message.reply_text("⏳ Генерирую новый вопрос...")

        prompt = f"Придумай один интересный вопрос для квиза на тему '{theme['name']}'. Вопрос должен быть средней сложности. Напиши только сам вопрос, без ответа."
        question = get_chatgpt_response(prompt)

        context.user_data['quiz_current_question'] = question

        score = context.user_data.get('quiz_score', 0)
        total = context.user_data.get('quiz_total', 0)

        await query.message.reply_text(
            f"{theme['emoji']} Тема: {theme['name']}\n"
            f"📊 Счет: {score}/{total}\n\n"
            f"❓ Вопрос:\n{question}\n\n"
            f"Напиши свой ответ:"
        )

        return ANSWERING_QUIZ

    elif query.data == "quiz_change_theme":
        logger.info(f"Пользователь {user.first_name} ({user.id}) меняет тему квиза")

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
            f"Выбери новую тему:",
            reply_markup=reply_markup
        )

        return CHOOSING_QUIZ_THEME

    elif query.data == "quiz_end":
        score = context.user_data.get('quiz_score', 0)
        total = context.user_data.get('quiz_total', 0)

        logger.info(f"Пользователь {user.first_name} ({user.id}) завершил квиз. Счет: {score}/{total}")

        if total > 0:
            percentage = (score / total) * 100
            await query.message.reply_text(
                f"🎮 Квиз завершен!\n\n"
                f"📊 Итоговый счет: {score}/{total} ({percentage:.1f}%)\n\n"
                f"Используй /quiz чтобы сыграть снова или /start для главного меню."
            )
        else:
            await query.message.reply_text(
                "🎮 Квиз завершен!\n\n"
                "Используй /quiz чтобы сыграть или /start для главного меню."
            )

        context.user_data.clear()

        return ConversationHandler.END