import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, ConversationHandler
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Состояния разговора
QUESTION = 0

# Вопросы теста
QUESTIONS = [
    {
        "text": "Когда ты смотришь на себя в зеркало, чаще всего ты думаешь:",
        "options": [
            ("Надо улучшить вот это и вот это", "D"),
            ("Надо сфоткаться, выбрав позу, где я буду себе нравиться", "I"),
            ("Нормально, пойдёт, я себя принимаю", "S"),
            ("Хочу понять, как подчеркнуть свою уникальность", "C")
        ]
    },
    {
        "text": "Как ты ведёшь себя, если тебе не нравится, как ты выглядишь?",
        "options": [
            ("Начинаю действовать — спорт, уход, цели", "D"),
            ("Всячески пытаюсь избежать этого неприятного чувства, отвлекаю себя или перенастраиваю", "I"),
            ("Принимаю это как часть себя — у всех бывают такие дни", "S"),
            ("Анализирую, почему мне это важно, и что я могу изменить", "C")
        ]
    },
    {
        "text": "Когда ты оказываешься в новой компании девушек, ты…",
        "options": [
            ("Держишь себя уверенно, сразу оцениваешь, кто есть кто", "D"),
            ("Стараешься расположить к себе, шутить, быть яркой", "I"),
            ("Наблюдаешь, привыкаешь к атмосфере, включаешься постепенно", "S"),
            ("Анализируешь поведение других, подмечаешь детали общения", "C")
        ]
    },
    {
        "text": "Когда тебе делают комплимент, ты…",
        "options": [
            ("Вежливо благодаришь, но внутри думаешь: «Я могу быть лучше»", "D"),
            ("Радостно принимаешь и сияешь", "I"),
            ("Улыбаешься, немного стесняешься, но приятно", "S"),
            ("Сначала сомневаешься, потом анализируешь — правда ли это", "C")
        ]
    },
    {
        "text": "Что для тебя любовь к себе?",
        "options": [
            ("Уважать себя и ставить цели", "D"),
            ("Радоваться жизни и быть собой", "I"),
            ("Заботиться о себе и отдыхать", "S"),
            ("Знать себя глубоко и понимать, что тебе нужно", "C")
        ]
    },
    {
        "text": "Когда ты сравниваешь себя с другими девушками, ты…",
        "options": [
            ("Думаешь: «Я могу быть круче, и я добьюсь»", "D"),
            ("Вдохновляешься, мечтаешь, хочешь дружить", "I"),
            ("Чувствуешь лёгкую зависть, но не соревнуешься", "S"),
            ("Сравниваешь детали: внешность, стиль, поведение", "C")
        ]
    },
    {
        "text": "Что ты делаешь, когда у тебя плохое настроение и упала самооценка?",
        "options": [
            ("Собираюсь, ставлю цель, иду к результату", "D"),
            ("Включаю музыку, общаюсь, отвлекаюсь", "I"),
            ("Лежу в кровати, даю себе время", "S"),
            ("Пишу дневник или размышляю, почему это произошло", "C")
        ]
    }
]

# Группы для перенаправления
GROUPS = {
    "D": "https://t.me/+5Q642xVao1c5ZTMy",
    "I": "https://t.me/+-6PJFdEuSEQzNWVi",
    "S": "https://t.me/+vHIY2ssuQY01Yzli",
    "C": "https://t.me/+JYD3UK1fBiM4NGZi"
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начало теста"""
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
        results = {'D': 0, 'I': 0, 'S': 0, 'C': 0}
        for answer in context.user_data['answers']:
            results[answer] += 1
        
        # Определение доминирующего типа
        dominant_type = max(results.items(), key=lambda x: x[1])[0]
        
        # Отправка результата и ссылки на группу
        await query.edit_message_text(
            text=f"Тест завершен!\n\nВаш результат: {dominant_type}\n\n"
                 f"Присоединяйтесь к вашей группе: {GROUPS[dominant_type]}"
        )
        return ConversationHandler.END

def main():
    """Запуск бота"""
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