import sqlite3
from telegram.ext import Updater, CommandHandler
from datetime import datetime, time
import time as tm
from config import TOKEN, GROUP_CHAT_ID

CONGRATULATION_TIME = time(00, 15)

def create_table():
    conn = sqlite3.connect('bd.bd')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS birthdays (
            id INTEGER PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            date TEXT,
            username TEXT
        )
    ''')
    conn.commit()
    conn.close()

def load_birthday_list():
    conn = sqlite3.connect('bd.bd')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM birthdays')
    rows = cursor.fetchall()
    birthday_list = {}
    for row in rows:
        full_name = f"{row[1]} {row[2]}"
        birthday_list[full_name] = (row[3], row[4])
    conn.close()
    return birthday_list

def save_birthday_list(birthday_list):
    conn = sqlite3.connect('bd.bd')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM birthdays')
    
    for full_name, (date, username) in birthday_list.items():
        name_parts = full_name.split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""
        cursor.execute('INSERT INTO birthdays (first_name, last_name, date, username) VALUES (?, ?, ?, ?)', 
                       (first_name, last_name, date, username))
    
    conn.commit()
    conn.close()

def sort_birthday_list(birthday_list):
    sorted_list = sorted(birthday_list.items(), key=lambda x: datetime.strptime(x[1][0], '%d.%m'))
    return dict(sorted_list)

def start(update, context):
    context.bot.send_message(chat_id=update.message.chat_id, text='--')

def birthday_list_command(update, context):
    if str(update.message.chat_id) == GROUP_CHAT_ID:
        birthday_list = load_birthday_list()
        if not birthday_list:
            bd_message = "Список дней рождения пуст."
        else:
            bd_message = "Список дней рождения:\n"
            for name, (date, username) in birthday_list.items():
                bd_message += f"{name}: {date} (@{username})\n"
        context.bot.send_message(chat_id=update.message.chat_id, text=bd_message)
    else:
        pass

def add_birthday(update, context):
    if str(update.message.chat_id) == GROUP_CHAT_ID:
        args = context.args
        if len(args) >= 3:
            first_name = args[0]
            last_name = args[1] if len(args) == 4 else ""
            date = args[2] if len(args) == 4 else args[1]
            username = args[3] if len(args) == 4 else args[2]
            
            birthday_list = load_birthday_list()
            full_name = f"{first_name} {last_name}".strip()
            
            if full_name in birthday_list:
                update.message.reply_text(f"Пользователь {full_name} уже есть в списке с датой {birthday_list[full_name][0]} (@{birthday_list[full_name][1]}).")
            else:
                birthday_list[full_name] = (date, username)
                
                birthday_list = sort_birthday_list(birthday_list)
                
                save_birthday_list(birthday_list)
                update.message.reply_text(f"Добавлен день рождения: {full_name} - {date} (@{username})")
        else:
            update.message.reply_text("Неверный формат команды. Используйте: /addbd Имя [Фамилия] ДД.ММ username")
    else:
        pass

def delete_birthday(update, context):
    if str(update.message.chat_id) == GROUP_CHAT_ID:
        if len(context.args) != 1:
            update.message.reply_text('Пожалуйста, укажите username пользователя для удаления его дня рождения.')
            return

        username = context.args[0]
        
        birthday_list = load_birthday_list()
        full_name_to_delete = None
        for full_name, (date, user) in birthday_list.items():
            if user == username:
                full_name_to_delete = full_name
                break
        
        if full_name_to_delete:
            del birthday_list[full_name_to_delete]
            save_birthday_list(birthday_list)
            update.message.reply_text(f'День рождения для @{username} ({full_name_to_delete}) успешно удален из списка.')
        else:
            update.message.reply_text(f'Пользователь @{username} не найден в списке дней рождения.')
    else:
        pass

def check_birthday(update, context):
    if str(update.message.chat_id) == GROUP_CHAT_ID:
        birthday_list = load_birthday_list()
        today = datetime.now().strftime('%d.%m')
        birthday_count = 0

        for full_name, (date, username) in birthday_list.items():
            if date == today:
                update.message.reply_text(f"С днем рождения, {full_name} (@{username})!")
                birthday_count += 1

        if birthday_count == 0:
            update.message.reply_text('Сегодня нет дней рождений.')
    else:
        pass

def congratulate_birthdays(bot):
    while True:
        now = datetime.now().time()
        if now.hour == CONGRATULATION_TIME.hour and now.minute == CONGRATULATION_TIME.minute:
            birthday_list = load_birthday_list()
            today = datetime.now().strftime('%d.%m')
            for full_name, (date, username) in birthday_list.items():
                if date == today:
                    bot.send_message(chat_id=GROUP_CHAT_ID, text=f"С днем рождения, {full_name} (@{username})!")
            tm.sleep(60 * 60)
        else:
            tm.sleep(60)

def ping_list_command(update, context):
    if str(update.message.chat_id) == GROUP_CHAT_ID:
        update.message.reply_text('Подключение стабильно.')
    else:
        pass

def help_list_command(update, context):
    help = """Актуальный список команд:
    
    /addbd Имя [Фамилия] ДД.ММ username
    - для добавления пользователя в список (фамилия опциональна)
    
    /delbd username
    - для удаления пользователя из списка по username
    
    /checkbd
    - для проверки на наличие дня рождения сегодня
    
    /sync
    - для искуственной сортировки таблицы

    /ping
    - для проверки подключения бота"""

    if str(update.message.chat_id) == GROUP_CHAT_ID:
        update.message.reply_text(help)
    else:
        pass

def sync_birthday_list_command(update, context):
    if str(update.message.chat_id) == GROUP_CHAT_ID:
        birthday_list = load_birthday_list()
        
        if birthday_list:
            birthday_list = sort_birthday_list(birthday_list)
            save_birthday_list(birthday_list)
            update.message.reply_text("Список дней рождений успешно отсортирован.")
        else:
            update.message.reply_text("Список дней рождений пуст.")
    else:
        pass

def main():
    create_table()
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("bd", birthday_list_command))
    dp.add_handler(CommandHandler("addbd", add_birthday, pass_args=True))
    dp.add_handler(CommandHandler("delbd", delete_birthday, pass_args=True))
    dp.add_handler(CommandHandler("checkbd", check_birthday))
    dp.add_handler(CommandHandler("ping", ping_list_command))
    dp.add_handler(CommandHandler("help", help_list_command))
    dp.add_handler(CommandHandler("sync", sync_birthday_list_command))

    updater.start_polling()
    congratulate_birthdays(updater.bot)
    updater.idle()

if __name__ == '__main__':
    main()
