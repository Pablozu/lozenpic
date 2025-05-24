import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, ConversationHandler
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Состояния разговора
QUESTION = 0

# Список модераторов
MODERATORS = ['pavzu']

# Функция проверки на модератора
def is_moderator(username: str) -> bool:
    return username in MODERATORS

# Вопросы теста
QUESTIONS = [
    {
        "text": "В торговом центре ты…",
        "options": [
            ("Покупаю нужное и ухожу", "A"),
            ("Смотрю всё и кайфую", "B"),
            ("Хожу спокойно, с чаем", "C"),
            ("Сравниваю цены и бренды", "D")
        ]
    },
    {
        "text": "В аэропорту ты…",
        "options": [
            ("Контроль и маршрут — моё всё", "A"),
            ("Кофе, музыка и сторис", "B"),
            ("Просто жду, не спеша", "C"),
            ("Читаю, наблюдаю людей", "D")
        ]
    },
    {
        "text": "Голод застал внезапно.",
        "options": [
            ("Быстро ем что-то полезное", "A"),
            ("Беру вкусное по настроению", "B"),
            ("Готовлю то, что планировала", "C"),
            ("Читаю отзывы о доставке", "D")
        ]
    },
    {
        "text": "Если трата неожиданная…",
        "options": [
            ("Злюсь и считаю бюджет", "A"),
            ("Отмахиваюсь — бывает", "B"),
            ("Немного тревожно, но ладно", "C"),
            ("Ищу ошибку и выводы", "D")
        ]
    },
    {
        "text": "Как проявляешь симпатию?",
        "options": [
            ("Беру и инициирую контакт", "A"),
            ("Флиртую, шучу, играю", "B"),
            ("Забочусь, делаю тепло", "C"),
            ("Сначала переписываюсь", "D")
        ]
    },
    {
        "text": "Твой стиль покупок —",
        "options": [
            ("Нужно — беру и ухожу", "A"),
            ("Нравится — сразу хочу", "B"),
            ("Главное — мягко и удобно", "C"),
            ("Сравниваю и читаю всё", "D")
        ]
    },
    {
        "text": "Что важно в отношениях?",
        "options": [
            ("Рост, цель, движение", "A"),
            ("Лёгкость, страсть, игра", "B"),
            ("Тепло, стабильность, забота", "C"),
            ("Честность, глубина, смысл", "D")
        ]
    },
    {
        "text": "Ты на свидании. Что главное?",
        "options": [
            ("Понимание целей", "A"),
            ("Атмосфера и эмоции", "B"),
            ("Чувство уюта и такта", "C"),
            ("Интеллект и глубина", "D")
        ]
    },
    {
        "text": "Когда ты злишься…",
        "options": [
            ("Кричу и решаю проблему", "A"),
            ("Переключаюсь на хорошее", "B"),
            ("Ухожу в себя, замираю", "C"),
            ("Пишу и анализирую", "D")
        ]
    },
    {
        "text": "На вечеринке ты…",
        "options": [
            ("Веду, рулю, управляю", "A"),
            ("Душа, танцы, контакт", "B"),
            ("Спокойно, ближе к одному", "C"),
            ("В стороне, наблюдаю", "D")
        ]
    },
    {
        "text": "День свободен. Что делаешь?",
        "options": [
            ("Список задач — и в бой", "A"),
            ("Вдохновляюсь, кайфую", "B"),
            ("Диван, книга, плед", "C"),
            ("Планирую, читаю, думаю", "D")
        ]
    },
    {
        "text": "Что ты заказываешь в ресторане?",
        "options": [
            ("То, что даст энергию", "A"),
            ("Самое вкусное и яркое", "B"),
            ("Тёплое и привычное", "C"),
            ("Состав, калории, анализ", "D")
        ]
    },
    {
        "text": "Кто ты в команде?",
        "options": [
            ("Лидер и мотиватор", "A"),
            ("Вдохновляю и заряжаю", "B"),
            ("Слушаю, поддерживаю", "C"),
            ("Анализирую и улучшаю", "D")
        ]
    },
    {
        "text": "Как реагируешь на критику?",
        "options": [
            ("Отвечаю, отстаиваю", "A"),
            ("Обидно, но улыбаюсь", "B"),
            ("Молчу, переживаю", "C"),
            ("Анализирую слова", "D")
        ]
    },
    {
        "text": "В поездке ты…",
        "options": [
            ("Планирую экскурсии", "A"),
            ("Хочу фанов и контента", "B"),
            ("Просто отдыхаю", "C"),
            ("Исследую, читаю о месте", "D")
        ]
    },
    {
        "text": "Что мотивирует тебя больше?",
        "options": [
            ("Результат и признание", "A"),
            ("Восторг и вдохновение", "B"),
            ("Уют и гармония", "C"),
            ("Знание и понимание", "D")
        ]
    },
    {
        "text": "Что тебя раздражает?",
        "options": [
            ("Слабость и хаос", "A"),
            ("Скука и рутина", "B"),
            ("Давление и спешка", "C"),
            ("Бессмыслица и ошибки", "D")
        ]
    },
    {
        "text": "Когда что-то не получается…",
        "options": [
            ("Пробую снова, другой путь", "A"),
            ("Отдыхаю и вдохновляюсь", "B"),
            ("Жду — может, само пройдёт", "C"),
            ("Разбираю, что пошло не так", "D")
        ]
    },
    {
        "text": "Как ты себя хвалишь?",
        "options": [
            ("За результат и действия", "A"),
            ("За энергию и кайф", "B"),
            ("За терпение и тепло", "C"),
            ("За точность и логику", "D")
        ]
    },
    {
        "text": "Где тебе комфортно?",
        "options": [
            ("В активной среде", "A"),
            ("Там, где весело и люди", "B"),
            ("Дома, наедине с собой", "C"),
            ("Там, где можно подумать", "D")
        ]
    },
    {
        "text": "Что тебе важно в себе?",
        "options": [
            ("Сила и целеустремлённость", "A"),
            ("Лёгкость и харизма", "B"),
            ("Добро и забота", "C"),
            ("Глубина и ум", "D")
        ]
    }
]

# Группы для перенаправления
GROUPS = {
    "A": "https://t.me/+5Q642xVao1c5ZTMy",
    "B": "https://t.me/+-6PJFdEuSEQzNWVi",
    "C": "https://t.me/+vHIY2ssuQY01Yzli",
    "D": "https://t.me/+JYD3UK1fBiM4NGZi"
}

PASSED_USERS_FILE = 'passed_users.txt'
PASSED_USERS = set()

def load_passed_users():
    try:
        with open(PASSED_USERS_FILE, 'r') as f:
            for line in f:
                PASSED_USERS.add(int(line.strip()))
    except FileNotFoundError:
        pass

def save_passed_user(user_id):
    with open(PASSED_USERS_FILE, 'a') as f:
        f.write(f"{user_id}\n")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начало теста"""
    user_id = update.effective_user.id
    # Проверка на модератора
    if update.effective_user.username and is_moderator(update.effective_user.username):
        await update.message.reply_text("Добро пожаловать, модератор!")
    # Проверка, проходил ли пользователь тест
    if user_id in PASSED_USERS:
        await update.message.reply_text("Вы уже прошли тест")
        return ConversationHandler.END
    context.user_data['answers'] = []
    context.user_data['current_question'] = 0
    await ask_question(update, context)
    return QUESTION

async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Задать вопрос пользователю"""
    current_question = context.user_data['current_question']
    question = QUESTIONS[current_question]
    
    keyboard = []
    for text, value in question['options']:
        keyboard.append([InlineKeyboardButton(text, callback_data=value)])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=f"Вопрос {current_question + 1} из {len(QUESTIONS)}:\n\n{question['text']}",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            text=f"Вопрос {current_question + 1} из {len(QUESTIONS)}:\n\n{question['text']}",
            reply_markup=reply_markup
        )

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка ответа пользователя"""
    query = update.callback_query
    await query.answer()
    
    answer = query.data
    context.user_data['answers'].append(answer)
    context.user_data['current_question'] += 1
    
    if context.user_data['current_question'] < len(QUESTIONS):
        await ask_question(update, context)
        return QUESTION
    else:
        # Подсчет результатов
        results = {'A': 0, 'B': 0, 'C': 0, 'D': 0}
        for answer in context.user_data['answers']:
            results[answer] += 1
        
        # Определение доминирующего типа
        dominant_type = max(results.items(), key=lambda x: x[1])[0]
        
        # Отправка результата и ссылки на группу
        await query.edit_message_text(
            text=f"Тест завершен!\n\nВаш результат: {dominant_type}\n\n"
                 f"Присоединяйтесь к вашей группе: {GROUPS[dominant_type]}"
        )
        PASSED_USERS.add(update.effective_user.id)
        save_passed_user(update.effective_user.id)
        return ConversationHandler.END

def main():
    """Запуск бота"""
    # Загрузка прошедших пользователей
    load_passed_users()
    # Создаем приложение
    application = Application.builder().token(os.getenv('TELEGRAM_TOKEN')).build()
    
    # Создаем обработчик разговора
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            QUESTION: [CallbackQueryHandler(handle_answer)]
        },
        fallbacks=[],
        per_chat=True,
        per_message=False
    )
    
    # Добавляем обработчик
    application.add_handler(conv_handler)
    
    # Запускаем бота
    print("Бот запущен! Ищите его в Telegram по имени, которое вы указали при создании.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main() 