import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
from utils.openai_helper import get_chatgpt_response, get_chatgpt_response_with_history

# Состояния для ConversationHandler
WAITING_GPT_QUESTION = 1
CHOOSING_PERSON = 2
TALKING_WITH_PERSON = 3
CHOOSING_QUIZ_THEME = 4
ANSWERING_QUIZ = 5
CHOOSING_LANGUAGE = 6
TRANSLATING = 7

# Личности для /talk
PERSONALITIES = {
    "einstein": {
        "name": "Альберт Эйнштейн",
        "emoji": "🧑‍🔬",
        "prompt": "Ты Альберт Эйнштейн, великий физик-теоретик. Отвечай в стиле Эйнштейна, используя научные аналогии и философский подход. Будь мудрым и добрым."
    },
    "shakespeare": {
        "name": "Уильям Шекспир",
        "emoji": "🎭",
        "prompt": "Ты Уильям Шекспир, величайший драматург. Отвечай возвышенным языком с элементами поэзии. Используй метафоры и драматические образы."
    },
    "musk": {
        "name": "Илон Маск",
        "emoji": "🚀",
        "prompt": "Ты Илон Маск, предприниматель и изобретатель. Отвечай прямо, амбициозно, с юмором. Говори о будущем, технологиях и инновациях."
    },
    "jobs": {
        "name": "Стив Джобс",
        "emoji": "🍎",
        "prompt": "Ты Стив Джобс, основатель Apple. Отвечай вдохновляюще, говори о дизайне, простоте и совершенстве. Будь харизматичным."
    }
}

# Темы для квиза
QUIZ_THEMES = {
    "history": {"name": "История", "emoji": "📜"},
    "science": {"name": "Наука", "emoji": "🔬"},
    "geography": {"name": "География", "emoji": "🌍"},
    "sport": {"name": "Спорт", "emoji": "⚽"},
    "movies": {"name": "Кино и сериалы", "emoji": "🎬"},
    "music": {"name": "Музыка", "emoji": "🎵"}
}

LANGUAGES = {
    "en": {"name": "Английский", "emoji": "🇬🇧"},
    "es": {"name": "Испанский", "emoji": "🇪🇸"},
    "fr": {"name": "Французский", "emoji": "🇫🇷"},
    "de": {"name": "Немецкий", "emoji": "🇩🇪"},
    "it": {"name": "Итальянский", "emoji": "🇮🇹"},
    "pl": {"name": "Польский", "emoji": "🇵🇱"}
}


# 🧩 Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# 📲 Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logger.info(f"Пользователь {user.first_name} ({user.id}) вызвал /start")
    await update.message.reply_text(
        f"Привет, {user.first_name}! 🤖\n\n"
        "Я бот с ChatGPT!\n"
        "Команды:\n"
        "/start — начать\n"
        "/help — помощь\n"
        "/gpt — задать вопрос ChatGPT\n"
        "/random — случайный интересный факт\n"
        "/talk — поговорить с известной личностью\n"
        "/quiz — сыграть в квиз\n"
        "/translate — переводчик текста и голоса"
    )


# 💬 Команда /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logger.info(f"Пользователь {user.first_name} ({user.id}) вызвал /help")
    await update.message.reply_text(
        "📖 Справка по командам:\n\n"
        "/start — главное меню\n"
        "/help — эта справка\n"
        "/gpt — задать вопрос ChatGPT\n"
        "/random — получить случайный факт\n"
        "/talk — поговорить с известной личностью\n"
        "/quiz — сыграть в квиз\n"
        "/translate — перевести текст или голос\n\n"
        "🎤 Голосовой режим:\n"
        "Просто отправь мне голосовое сообщение (кружочек),\n"
        "и я отвечу тебе голосом!"
    )


# 🤖 Команда /gpt - начало
async def gpt_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало работы с ChatGPT"""
    user = update.effective_user
    logger.info(f"Пользователь {user.first_name} ({user.id}) вызвал /gpt")

    # Отправляем картинку
    try:
        with open('images/gpt.jpg', 'rb') as photo:
            await update.message.reply_photo(
                photo=photo,
                caption="🤖 ChatGPT интерфейс\n\nНапиши свой вопрос, и я отправлю его ChatGPT!"
            )
    except FileNotFoundError:
        await update.message.reply_text(
            "🤖 ChatGPT интерфейс\n\nНапиши свой вопрос, и я отправлю его ChatGPT!"
        )

    # Переходим в состояние ожидания вопроса
    return WAITING_GPT_QUESTION


# 💬 Обработка вопроса для ChatGPT
async def gpt_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получаем вопрос и отправляем в ChatGPT"""
    user = update.effective_user
    user_message = update.message.text

    logger.info(
        f"Пользователь {
            user.first_name} ({
            user.id}) отправил вопрос: {user_message}")

    # Показываем, что бот работает
    await update.message.reply_text("⏳ Обрабатываю запрос...")

    # Получаем ответ от ChatGPT
    response = get_chatgpt_response(user_message)

    # Создаем кнопки
    keyboard = [
        [InlineKeyboardButton("➕ Еще вопрос", callback_data="gpt_more")],
        [InlineKeyboardButton("❌ Закончить", callback_data="gpt_end")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Отправляем ответ пользователю с кнопками
    await update.message.reply_text(response, reply_markup=reply_markup)

    logger.info(f"Ответ отправлен пользователю {user.first_name} ({user.id})")

    # НЕ завершаем диалог, ждем нажатия кнопки
    return WAITING_GPT_QUESTION


# 🔘 Обработка кнопок /gpt
async def gpt_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает нажатия на кнопки в /gpt"""
    query = update.callback_query
    user = query.from_user
    await query.answer()

    if query.data == "gpt_more":
        # Кнопка "Еще вопрос"
        logger.info(f"Пользователь {user.first_name} ({user.id}) хочет задать еще вопрос")

        await query.message.reply_text(
            "🤖 ChatGPT готов к новому вопросу!\n\n"
            "Напиши свой вопрос:"
        )

        return WAITING_GPT_QUESTION

    elif query.data == "gpt_end":
        # Кнопка "Закончить"
        logger.info(f"Пользователь {user.first_name} ({user.id}) закончил /gpt")

        await query.message.reply_text(
            "👋 Возвращайся с вопросами еще!\n\n"
            "Используй /start для главного меню."
        )

        return ConversationHandler.END


# 🎲 Команда /random - случайный факт
async def random_fact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет случайный факт от ChatGPT"""
    user = update.effective_user
    logger.info(f"Пользователь {user.first_name} ({user.id}) вызвал /random")

    # Показываем, что бот работает
    await update.message.reply_text("⏳ Генерирую интересный факт...")

    # Получаем случайный факт от ChatGPT
    prompt = "Расскажи один интересный случайный факт на любую тему. Будь краток (2-3 предложения) и интересен."
    fact = get_chatgpt_response(prompt)

    # Отправляем картинку с фактом
    try:
        with open('images/random.jpg', 'rb') as photo:
            # Создаем кнопки
            keyboard = [
                [InlineKeyboardButton("🎲 Хочу еще факт", callback_data="random_more")],
                [InlineKeyboardButton("❌ Закончить", callback_data="random_end")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_photo(
                photo=photo,
                caption=f"🎲 Случайный факт:\n\n{fact}",
                reply_markup=reply_markup
            )
    except FileNotFoundError:
        # Если картинки нет, отправляем просто текст
        keyboard = [
            [InlineKeyboardButton("🎲 Хочу еще факт", callback_data="random_more")],
            [InlineKeyboardButton("❌ Закончить", callback_data="random_end")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"🎲 Случайный факт:\n\n{fact}",
            reply_markup=reply_markup
        )

    logger.info(f"Факт отправлен пользователю {user.first_name} ({user.id})")


# 🔘 Обработка нажатий на кнопки /random
async def random_button_handler(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает нажатия на кнопки в /random"""
    query = update.callback_query
    user = query.from_user

    # Подтверждаем нажатие кнопки (убирает "часики" на кнопке)
    await query.answer()

    if query.data == "random_more":
        # Кнопка "Хочу еще факт"
        logger.info(
            f"Пользователь {
                user.first_name} ({
                user.id}) запросил еще факт")

        await query.message.reply_text("⏳ Генерирую еще один факт...")

        # Получаем новый факт
        prompt = "Расскажи один интересный случайный факт на любую тему. Будь краток (2-3 предложения) и интересен."
        fact = get_chatgpt_response(prompt)

        # Создаем кнопки снова
        keyboard = [
            [InlineKeyboardButton("🎲 Хочу еще факт", callback_data="random_more")],
            [InlineKeyboardButton("❌ Закончить", callback_data="random_end")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.reply_text(
            f"🎲 Случайный факт:\n\n{fact}",
            reply_markup=reply_markup
        )

    elif query.data == "random_end":
        # Кнопка "Закончить"
        logger.info(
            f"Пользователь {
                user.first_name} ({
                user.id}) закончил /random")
        await query.message.reply_text("👋 Возвращайся за фактами еще!\n\nИспользуй /start для начала.")


# 🎭 Команда /talk - начало
async def talk_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало диалога с личностью - выбор персонажа"""
    user = update.effective_user
    logger.info(f"Пользователь {user.first_name} ({user.id}) вызвал /talk")

    # Создаем кнопки с личностями
    keyboard = []
    for key, person in PERSONALITIES.items():
        keyboard.append([InlineKeyboardButton(
            f"{person['emoji']} {person['name']}",
            callback_data=f"talk_choose_{key}"
        )])

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Отправляем картинку с выбором
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


# 🎭 Обработка выбора личности
async def talk_choose_person(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE):
    """Пользователь выбрал личность"""
    query = update.callback_query
    user = query.from_user
    await query.answer()

    # Получаем выбранную личность из callback_data
    person_key = query.data.replace("talk_choose_", "")
    person = PERSONALITIES.get(person_key)

    if not person:
        await query.message.reply_text("Ошибка выбора личности. Попробуй /talk снова.")
        return ConversationHandler.END

    # Сохраняем выбранную личность и инициализируем историю диалога
    context.user_data['person'] = person
    context.user_data['person_key'] = person_key
    context.user_data['conversation_history'] = [
        {"role": "system", "content": person['prompt']}
    ]

    logger.info(
        f"Пользователь {
            user.first_name} ({
            user.id}) выбрал {
                person['name']}")

    # Создаем кнопку "Закончить"
    keyboard = [[InlineKeyboardButton(
        "❌ Закончить диалог", callback_data="talk_end")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(
        f"{person['emoji']} Ты начал диалог с {person['name']}!\n\n"
        f"Задавай вопросы или просто общайся. Я буду отвечать в стиле этой личности.\n\n"
        f"Для завершения диалога нажми кнопку ниже.",
        reply_markup=reply_markup
    )

    return TALKING_WITH_PERSON


# 💬 Обработка сообщений в диалоге с личностью
async def talk_conversation(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает сообщения в диалоге с личностью"""
    user = update.effective_user
    user_message = update.message.text

    # Получаем данные о текущем диалоге
    person = context.user_data.get('person')
    conversation_history = context.user_data.get('conversation_history', [])

    if not person:
        await update.message.reply_text("Ошибка: личность не выбрана. Начни заново с /talk")
        return ConversationHandler.END

    logger.info(
        f"Пользователь {
            user.first_name} ({
            user.id}) в диалоге с {
                person['name']}: {user_message}")

    # Добавляем сообщение пользователя в историю
    conversation_history.append({"role": "user", "content": user_message})

    # Показываем, что бот работает
    await update.message.reply_text("⏳ Думаю...")

    # Получаем ответ от ChatGPT с историей
    response = get_chatgpt_response_with_history(conversation_history)

    # Добавляем ответ в историю
    conversation_history.append({"role": "assistant", "content": response})

    # Сохраняем обновленную историю
    context.user_data['conversation_history'] = conversation_history

    # Создаем кнопку "Закончить"
    keyboard = [[InlineKeyboardButton(
        "❌ Закончить диалог", callback_data="talk_end")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Отправляем ответ
    await update.message.reply_text(
        f"{person['emoji']} {response}",
        reply_markup=reply_markup
    )

    logger.info(f"Ответ отправлен пользователю {user.first_name} ({user.id})")

    return TALKING_WITH_PERSON


# 🔘 Обработка кнопки "Закончить диалог"
async def talk_end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение диалога с личностью"""
    query = update.callback_query
    user = query.from_user
    await query.answer()

    person = context.user_data.get('person')

    if person:
        logger.info(
            f"Пользователь {
                user.first_name} ({
                user.id}) завершил диалог с {
                person['name']}")
        await query.message.reply_text(
            f"👋 Диалог с {person['emoji']} {person['name']} завершен!\n\n"
            f"Используй /talk чтобы начать новый диалог или /start для главного меню."
        )
    else:
        await query.message.reply_text("Диалог завершен! Используй /start для главного меню.")

    # Очищаем данные пользователя
    context.user_data.clear()

    return ConversationHandler.END


# 🎮 Команда /quiz - начало
async def quiz_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало квиза - выбор темы"""
    user = update.effective_user
    logger.info(f"Пользователь {user.first_name} ({user.id}) вызвал /quiz")

    # Инициализируем счет
    context.user_data['quiz_score'] = 0
    context.user_data['quiz_total'] = 0

    # Создаем кнопки с темами
    keyboard = []
    for key, theme in QUIZ_THEMES.items():
        keyboard.append([InlineKeyboardButton(
            f"{theme['emoji']} {theme['name']}",
            callback_data=f"quiz_theme_{key}"
        )])

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Отправляем картинку с выбором темы
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


# 🎮 Обработка выбора темы и генерация вопроса
async def quiz_choose_theme(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE):
    """Пользователь выбрал тему, генерируем вопрос"""
    query = update.callback_query
    user = query.from_user
    await query.answer()

    # Получаем выбранную тему
    theme_key = query.data.replace("quiz_theme_", "")
    theme = QUIZ_THEMES.get(theme_key)

    if not theme:
        await query.message.reply_text("Ошибка выбора темы. Попробуй /quiz снова.")
        return ConversationHandler.END

    # Сохраняем тему
    context.user_data['quiz_theme'] = theme
    context.user_data['quiz_theme_key'] = theme_key

    logger.info(
        f"Пользователь {
            user.first_name} ({
            user.id}) выбрал тему {
                theme['name']}")

    await query.message.reply_text("⏳ Генерирую вопрос...")

    # Генерируем вопрос через ChatGPT
    prompt = f"Придумай один интересный вопрос для квиза на тему '{
        theme['name']}'. Вопрос должен быть средней сложности. Напиши только сам вопрос, без ответа."
    question = get_chatgpt_response(prompt)

    # Сохраняем вопрос
    context.user_data['quiz_current_question'] = question

    # Получаем текущий счет
    score = context.user_data.get('quiz_score', 0)
    total = context.user_data.get('quiz_total', 0)

    await query.message.reply_text(
        f"{theme['emoji']} Тема: {theme['name']}\n"
        f"📊 Счет: {score}/{total}\n\n"
        f"❓ Вопрос:\n{question}\n\n"
        f"Напиши свой ответ:"
    )

    return ANSWERING_QUIZ


# 💬 Обработка ответа на вопрос квиза
async def quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверяем ответ пользователя"""
    user = update.effective_user
    user_answer = update.message.text

    question = context.user_data.get('quiz_current_question')
    theme = context.user_data.get('quiz_theme')

    if not question or not theme:
        await update.message.reply_text("Ошибка квиза. Начни заново с /quiz")
        return ConversationHandler.END

    logger.info(
        f"Пользователь {
            user.first_name} ({
            user.id}) ответил: {user_answer}")

    await update.message.reply_text("⏳ Проверяю ответ...")

    # Проверяем ответ через ChatGPT
    check_prompt = f"Вопрос квиза: {question}\nОтвет пользователя: {user_answer}\n\nПроверь, правильный ли ответ. Ответь ТОЛЬКО 'Правильно' или 'Неправильно', а затем кратко объясни почему и дай правильный ответ если нужно."
    result = get_chatgpt_response(check_prompt)

    # Определяем правильность (простая проверка по первому слову)
    is_correct = result.lower().startswith("правильно")

    # Обновляем счет
    total = context.user_data.get('quiz_total', 0) + 1
    score = context.user_data.get('quiz_score', 0)

    if is_correct:
        score += 1
        emoji = "✅"
    else:
        emoji = "❌"

    context.user_data['quiz_score'] = score
    context.user_data['quiz_total'] = total

    # Создаем кнопки
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

    logger.info(
        f"Результат для {
            user.first_name} ({
            user.id}): {
                'Правильно' if is_correct else 'Неправильно'}")

    return ANSWERING_QUIZ


# 🔘 Обработка кнопок квиза
async def quiz_button_handler(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает нажатия на кнопки в квизе"""
    query = update.callback_query
    user = query.from_user
    await query.answer()

    if query.data == "quiz_more":
        # Кнопка "Еще вопрос" - генерируем новый вопрос на ту же тему
        theme = context.user_data.get('quiz_theme')

        if not theme:
            await query.message.reply_text("Ошибка. Начни квиз заново с /quiz")
            return ConversationHandler.END

        logger.info(
            f"Пользователь {
                user.first_name} ({
                user.id}) запросил еще вопрос")

        await query.message.reply_text("⏳ Генерирую новый вопрос...")

        # Генерируем новый вопрос
        prompt = f"Придумай один интересный вопрос для квиза на тему '{
            theme['name']}'. Вопрос должен быть средней сложности. Напиши только сам вопрос, без ответа."
        question = get_chatgpt_response(prompt)

        # Сохраняем вопрос
        context.user_data['quiz_current_question'] = question

        # Получаем текущий счет
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
        # Кнопка "Сменить тему" - показываем выбор тем снова
        logger.info(
            f"Пользователь {
                user.first_name} ({
                user.id}) меняет тему квиза")

        # Создаем кнопки с темами
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
        # Кнопка "Закончить квиз"
        score = context.user_data.get('quiz_score', 0)
        total = context.user_data.get('quiz_total', 0)

        logger.info(
            f"Пользователь {
                user.first_name} ({
                user.id}) завершил квиз. Счет: {score}/{total}")

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

        # Очищаем данные
        context.user_data.clear()

        return ConversationHandler.END


# 🎤 Обработка голосовых сообщений
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает голосовые сообщения"""
    user = update.effective_user
    logger.info(
        f"Пользователь {
            user.first_name} ({
            user.id}) отправил голосовое сообщение")

    await update.message.reply_text("🎤 Обрабатываю голосовое сообщение...")

    try:
        # Получаем файл голосового сообщения
        voice = update.message.voice
        voice_file = await context.bot.get_file(voice.file_id)

        # Создаем папку temp если её нет
        os.makedirs("temp", exist_ok=True)

        # Скачиваем файл
        voice_path = f"temp/voice_{user.id}.ogg"
        await voice_file.download_to_drive(voice_path)

        logger.info(f"Голосовое сообщение сохранено: {voice_path}")

        # Преобразуем голос в текст
        from utils.openai_helper import transcribe_audio
        text = transcribe_audio(voice_path)

        if text.startswith("Ошибка"):
            await update.message.reply_text(f"❌ {text}")
            return

        logger.info(f"Распознанный текст: {text}")
        await update.message.reply_text(f"📝 Ты сказал: {text}\n\n⏳ Генерирую ответ...")

        # Отправляем в ChatGPT
        response = get_chatgpt_response(text)

        # Преобразуем ответ в голос
        from utils.openai_helper import text_to_speech
        audio_path = f"temp/response_{user.id}.mp3"

        if text_to_speech(response, audio_path):
            # Отправляем голосовое сообщение
            with open(audio_path, 'rb') as audio:
                await update.message.reply_voice(
                    voice=audio,
                    caption=f"🤖 {response}"
                )

            logger.info(
                f"Голосовой ответ отправлен пользователю {
                    user.first_name} ({
                    user.id})")

            # Удаляем временные файлы
            os.remove(audio_path)
        else:
            # Если не получилось озвучить, отправляем текстом
            await update.message.reply_text(f"🤖 {response}")

        # Удаляем входящий голосовой файл
        os.remove(voice_path)

    except Exception as e:
        logger.error(f"Ошибка обработки голосового сообщения: {str(e)}")
        await update.message.reply_text(f"❌ Ошибка обработки: {str(e)}")


# 🌍 Команда /translate - начало
async def translate_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало переводчика - выбор языка"""
    user = update.effective_user
    logger.info(
        f"Пользователь {
            user.first_name} ({
            user.id}) вызвал /translate")

    # Создаем кнопки с языками
    keyboard = []
    for key, lang in LANGUAGES.items():
        keyboard.append([InlineKeyboardButton(
            f"{lang['emoji']} {lang['name']}",
            callback_data=f"translate_lang_{key}"
        )])

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Отправляем картинку с выбором языка
    try:
        with open('images/translate.jpg', 'rb') as photo:
            await update.message.reply_photo(
                photo=photo,
                caption="🌍 Переводчик\n\nВыбери язык, на который нужно перевести:",
                reply_markup=reply_markup
            )
    except FileNotFoundError:
        await update.message.reply_text(
            "🌍 Переводчик\n\nВыбери язык, на который нужно перевести:",
            reply_markup=reply_markup
        )

    return CHOOSING_LANGUAGE


# 🌍 Обработка выбора языка
async def translate_choose_language(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE):
    """Пользователь выбрал язык"""
    query = update.callback_query
    user = query.from_user
    await query.answer()

    # Получаем выбранный язык
    lang_key = query.data.replace("translate_lang_", "")
    language = LANGUAGES.get(lang_key)

    if not language:
        await query.message.reply_text("Ошибка выбора языка. Попробуй /translate снова.")
        return ConversationHandler.END

    # Сохраняем выбранный язык
    context.user_data['translate_language'] = language
    context.user_data['translate_lang_key'] = lang_key

    logger.info(
        f"Пользователь {
            user.first_name} ({
            user.id}) выбрал язык {
                language['name']}")

    await query.message.reply_text(
        f"{language['emoji']} Язык перевода: {language['name']}\n\n"
        f"Теперь отправь мне:\n"
        f"• Текстовое сообщение для перевода\n"
        f"• ИЛИ голосовое сообщение 🎤"
    )

    return TRANSLATING


# 💬 Обработка текста для перевода
async def translate_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Переводит текстовое сообщение"""
    user = update.effective_user
    text = update.message.text

    language = context.user_data.get('translate_language')

    if not language:
        await update.message.reply_text("Ошибка: язык не выбран. Начни заново с /translate")
        return ConversationHandler.END

    logger.info(
        f"Пользователь {
            user.first_name} ({
            user.id}) отправил текст для перевода: {text}")

    await update.message.reply_text("⏳ Перевожу...")

    # Переводим через ChatGPT
    prompt = f"Переведи следующий текст на {
        language['name']} язык. Выведи ТОЛЬКО перевод, без комментариев:\n\n{text}"
    translation = get_chatgpt_response(prompt)

    # Создаем кнопки
    keyboard = [
        [InlineKeyboardButton("🔄 Сменить язык", callback_data="translate_change_lang")],
        [InlineKeyboardButton("❌ Закончить", callback_data="translate_end")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"{language['emoji']} Перевод на {language['name']}:\n\n{translation}",
        reply_markup=reply_markup
    )

    logger.info(
        f"Перевод отправлен пользователю {
            user.first_name} ({
            user.id})")

    return TRANSLATING


# 🎤 Обработка голоса для перевода
async def translate_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Переводит голосовое сообщение"""
    user = update.effective_user

    language = context.user_data.get('translate_language')

    if not language:
        await update.message.reply_text("Ошибка: язык не выбран. Начни заново с /translate")
        return ConversationHandler.END

    logger.info(
        f"Пользователь {
            user.first_name} ({
            user.id}) отправил голос для перевода")

    await update.message.reply_text("🎤 Обрабатываю голосовое сообщение...")

    try:
        # Получаем файл голосового сообщения
        voice = update.message.voice
        voice_file = await context.bot.get_file(voice.file_id)

        # Создаем папку temp если её нет
        os.makedirs("temp", exist_ok=True)

        # Скачиваем файл
        voice_path = f"temp/translate_voice_{user.id}.ogg"
        await voice_file.download_to_drive(voice_path)

        # Преобразуем голос в текст
        from utils.openai_helper import transcribe_audio
        text = transcribe_audio(voice_path)

        if text.startswith("Ошибка"):
            await update.message.reply_text(f"❌ {text}")
            os.remove(voice_path)
            return TRANSLATING

        logger.info(f"Распознанный текст: {text}")
        await update.message.reply_text(f"📝 Распознано: {text}\n\n⏳ Перевожу...")

        # Переводим через ChatGPT
        prompt = f"Переведи следующий текст на {
            language['name']} язык. Выведи ТОЛЬКО перевод, без комментариев:\n\n{text}"
        translation = get_chatgpt_response(prompt)

        # Создаем кнопки
        keyboard = [
            [InlineKeyboardButton("🔄 Сменить язык", callback_data="translate_change_lang")],
            [InlineKeyboardButton("❌ Закончить", callback_data="translate_end")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"{language['emoji']} Перевод на {language['name']}:\n\n{translation}",
            reply_markup=reply_markup
        )

        logger.info(
            f"Перевод голоса отправлен пользователю {
                user.first_name} ({
                user.id})")

        # Удаляем временный файл
        os.remove(voice_path)

    except Exception as e:
        logger.error(f"Ошибка обработки голоса для перевода: {str(e)}")
        await update.message.reply_text(f"❌ Ошибка обработки: {str(e)}")

    return TRANSLATING


# 🔘 Обработка кнопок переводчика
async def translate_button_handler(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает нажатия на кнопки в переводчике"""
    query = update.callback_query
    user = query.from_user
    await query.answer()

    if query.data == "translate_change_lang":
        # Кнопка "Сменить язык"
        logger.info(
            f"Пользователь {
                user.first_name} ({
                user.id}) меняет язык перевода")

        # Создаем кнопки с языками
        keyboard = []
        for key, lang in LANGUAGES.items():
            keyboard.append([InlineKeyboardButton(
                f"{lang['emoji']} {lang['name']}",
                callback_data=f"translate_lang_{key}"
            )])

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.reply_text(
            "🌍 Выбери новый язык для перевода:",
            reply_markup=reply_markup
        )

        return CHOOSING_LANGUAGE

    elif query.data == "translate_end":
        # Кнопка "Закончить"
        language = context.user_data.get('translate_language')

        logger.info(
            f"Пользователь {
                user.first_name} ({
                user.id}) завершил переводчик")

        if language:
            await query.message.reply_text(
                "👋 Переводчик завершен!\n\n"
                "Используй /translate чтобы начать снова или /start для главного меню."
            )
        else:
            await query.message.reply_text(
                "Переводчик завершен! Используй /start для главного меню."
            )

        # Очищаем данные
        context.user_data.clear()

        return ConversationHandler.END


# 🚨 Глобальный обработчик ошибок
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает все ошибки в боте"""
    logger.error(f"Произошла ошибка: {context.error}", exc_info=context.error)

    # Если есть update (сообщение от пользователя)
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "😔 Произошла ошибка при обработке запроса.\n"
                "Попробуй снова или используй /start"
            )
        except Exception:
            # Если даже отправить сообщение об ошибке не получилось
            pass


def main():
    """🚀 Запуск бота"""
    logger.info("Запуск бота...")

    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Регистрируем обычные команды
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # ConversationHandler для /gpt
    gpt_handler = ConversationHandler(
        entry_points=[CommandHandler("gpt", gpt_start)],
        states={
            WAITING_GPT_QUESTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, gpt_question),
                CallbackQueryHandler(gpt_button_handler, pattern="^gpt_")
            ]
        },
        fallbacks=[CommandHandler("start", start)]
    )
    application.add_handler(gpt_handler)

    # Обработчик команды /random
    application.add_handler(CommandHandler("random", random_fact))

    # Обработчик нажатий на кнопки /random
    application.add_handler(
        CallbackQueryHandler(
            random_button_handler,
            pattern="^random_"))

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

    # Обработчик голосовых сообщений
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))

    application.add_error_handler(error_handler)
    logger.info("Бот успешно запущен и ожидает команды.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
