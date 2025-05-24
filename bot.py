import os
import json
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Константы
# !!! Вставьте сюда ID вашей группы. Его можно получить, добавив бота в группу и воспользовавшись, например, @getidsbot
GROUP_CHAT_ID = -1002777227564 # Замените на реальный ID вашей группы
LINK_EXPIRY_MINUTES = 10
MEMBERSHIP_EXPIRY_DAYS = 30 # Новый срок для автоматического удаления из группы

USER_LINKS_FILE = 'user_links.json'
user_link_data = {}

def load_user_links():
    global user_link_data
    try:
        with open(USER_LINKS_FILE, 'r') as f:
            data = json.load(f)
            # Преобразуем строки даты обратно в объекты datetime
            for user_id, link_info in data.items():
                link_info['expiry_date'] = datetime.fromisoformat(link_info['expiry_date'])
                # Добавляем membership_expiry_date, если его нет (для старых записей)
                if 'membership_expiry_date' in link_info:
                    link_info['membership_expiry_date'] = datetime.fromisoformat(link_info['membership_expiry_date'])
                user_link_data[int(user_id)] = link_info
    except FileNotFoundError:
        pass
    except json.JSONDecodeError:
        print("Ошибка чтения JSON-файла. Создаю пустой словарь.")
        user_link_data = {}

def save_user_links():
    with open(USER_LINKS_FILE, 'w') as f:
        # Преобразуем объекты datetime в строки для сохранения в JSON
        serializable_data = {}
        for uid, data in user_link_data.items():
            serializable_item = {}
            for k, v in data.items():
                if isinstance(v, datetime):
                    serializable_item[k] = v.isoformat()
                else:
                    serializable_item[k] = v
            serializable_data[str(uid)] = serializable_item
        json.dump(serializable_data, f, indent=4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name

    # Проверяем, получал ли пользователь уже ссылку
    if user_id in user_link_data and user_link_data[user_id].get('link_issued'):
        await update.message.reply_text(
            f"Извините, {username}, вы уже получали ссылку на группу. Ссылку можно получить только один раз."
        )
        return

    try:
        link_expiry_date = datetime.now() + timedelta(minutes=LINK_EXPIRY_MINUTES)
        membership_expiry_date = datetime.now() + timedelta(days=MEMBERSHIP_EXPIRY_DAYS)
        
        # Создаем уникальную одноразовую пригласительную ссылку
        invite_link_object = await context.bot.create_chat_invite_link(
            chat_id=GROUP_CHAT_ID,
            member_limit=1,  # Только один пользователь может использовать эту ссылку
            expire_date=link_expiry_date # Ссылка действует ограниченное время
        )
        
        invite_link = invite_link_object.invite_link
        
        user_link_data[user_id] = {
            'invite_link': invite_link,
            'link_expiry_date': link_expiry_date,
            'membership_expiry_date': membership_expiry_date, # Дата, когда пользователь будет удален из группы
            'link_issued': True,
            'used': False, # Будет отмечено как True после использования, если есть такая возможность отслеживать
            'removed_from_group': False # Флаг, чтобы не пытаться удалить повторно
        }
        save_user_links()

        await update.message.reply_text(
            f"Привет, {username}! Вот ваша уникальная ссылка на группу: {invite_link}\n"
            f"Она действительна в течение {LINK_EXPIRY_MINUTES} минут и может быть использована только один раз.\n"
            f"Через {MEMBERSHIP_EXPIRY_DAYS} дней после получения этой ссылки вы будете автоматически удалены из группы."
        )

    except Exception as e:
        await update.message.reply_text(
            f"Произошла ошибка при создании ссылки. Пожалуйста, попробуйте позже. Ошибка: {e}"
        )
        print(f"Ошибка при создании ссылки для {username} ({user_id}): {e}")

async def cleanup_expired_links(context: ContextTypes.DEFAULT_TYPE):
    """Задача для очистки (аннулирования) просроченных ссылок и удаления пользователей из группы"""
    current_time = datetime.now()
    links_to_revoke = []
    users_to_remove = []

    for user_id, link_info in list(user_link_data.items()): # Создаем копию для итерации
        # Проверка на аннулирование просроченных ссылок
        if not link_info.get('used', False) and current_time >= link_info['link_expiry_date']:
            links_to_revoke.append(link_info['invite_link'])
            # Не удаляем запись полностью, так как она еще нужна для membership_expiry_date
            # Можно пометить link_issued как False, если нужно
            link_info['link_issued'] = False # Ссылка больше неактивна
            print(f"Ссылка для пользователя {user_id} просрочена.")
        
        # Проверка на удаление пользователя из группы
        if not link_info.get('removed_from_group', False) and current_time >= link_info['membership_expiry_date']:
            users_to_remove.append(user_id)
            link_info['removed_from_group'] = True # Помечаем, что пытались удалить
            print(f"Пользователь {user_id} достиг срока автоматического удаления.")

    save_user_links() # Сохраняем все изменения в файл

    for link in links_to_revoke:
        try:
            await context.bot.revoke_chat_invite_link(chat_id=GROUP_CHAT_ID, invite_link=link)
            print(f"Ссылка {link} успешно аннулирована.")
        except Exception as e:
            print(f"Не удалось аннулировать ссылку {link}: {e}")

    for user_id_to_remove in users_to_remove:
        try:
            # Удаление пользователя из группы (ban_chat_member - это фактическое удаление)
            # Временный бан - это самый простой способ удалить пользователя.
            # Затем можно сразу разбанить, если нужно, чтобы он мог снова вступить.
            await context.bot.ban_chat_member(chat_id=GROUP_CHAT_ID, user_id=user_id_to_remove, until_date=datetime.now() + timedelta(seconds=30)) # Бан на 30 секунд
            await context.bot.unban_chat_member(chat_id=GROUP_CHAT_ID, user_id=user_id_to_remove)
            print(f"Пользователь {user_id_to_remove} успешно удален из группы.")
        except Exception as e:
            print(f"Не удалось удалить пользователя {user_id_to_remove} из группы: {e}")

def main():
    """Запуск бота"""
    load_user_links()
    # Создаем приложение
    application = Application.builder().token(os.getenv("TELEGRAM_TOKEN")).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    
    # Добавляем задачу очистки просроченных ссылок и удаления пользователей (например, каждые 10 минут)
    job_queue = application.job_queue
    job_queue.run_repeating(cleanup_expired_links, interval=600) # 600 секунд = 10 минут
    
    # Запускаем бота
    print("Бот запущен! Ожидание команд...")
    application.run_polling()

if __name__ == "__main__":
    main() 