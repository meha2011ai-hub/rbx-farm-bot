import telebot
from telebot import types
import time
import os
import sqlite3
from flask import Flask
import threading

TOKEN = os.environ.get('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TOKEN)

# --- НАСТРОЙКА БАЗЫ ДАННЫХ (SQLite) ---
DB_FILE = 'bot_database.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance REAL DEFAULT 0,
            last_click REAL DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_user_data(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT balance, last_click FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    if row is None:
        cursor.execute('INSERT INTO users (user_id, balance, last_click) VALUES (?, 0, 0)', (user_id,))
        conn.commit()
        conn.close()
        return 0.0, 0.0
    conn.close()
    return row[0], row[1]

def update_balance(user_id, new_balance, new_last_click):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET balance = ?, last_click = ? WHERE user_id = ?', (new_balance, new_last_click, user_id))
    conn.commit()
    conn.close()

# --- ОБРАБОТЧИКИ БОТА ---

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    balance, _ = get_user_data(user_id)
    
    # Добавляем две кнопки
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('👆 Фармить RBX')
    btn2 = types.KeyboardButton('💸 Вывод')
    markup.add(btn1, btn2)
    
    bot.send_message(message.chat.id, 
                     f"Привет, {message.from_user.first_name}! 👋\n"
                     f"Твой баланс: {round(balance, 1)} RBX.\n"
                     "Жми на кнопку и фарми робуксы! (За клик дают 0.2 RBX)", 
                     reply_markup=markup)

@bot.message_handler(content_types=['text'])
def handle_text(message):
    print(f"[LOG] Пользователь {message.from_user.id} (@{message.from_user.username}) написал: {message.text}")
    
    user_id = message.from_user.id
    current_time = time.time()
    balance, last_click = get_user_data(user_id)

    # ЛОГИКА КЛИКА
    if message.text == '👆 Фармить RBX':
        time_passed = current_time - last_click
        
        if time_passed < 2:
            bot.send_message(message.chat.id, "⏳ Не так быстро! Подожди пару секунд.")
        else:
            new_balance = balance + 0.2
            update_balance(user_id, new_balance, current_time)
            bot.send_message(message.chat.id, f"✅ +0.2 RBX\n💰 Твой баланс: {round(new_balance, 1)} RBX")

    # ЛОГИКА ВЫВОДА
    elif message.text == '💸 Вывод':
        if balance >= 30:
            bot.send_message(message.chat.id, 
                             f"🎉 Поздравляю! У тебя {round(balance, 1)} RBX.\n\n"
                             f"Для получения робуксов свяжись с модератором: **@meha2011**\n"
                             f"Ссылка на профиль: https://t.me/Meha2011\n\n"
                             f"*Напиши ему, что ты из бота RBX Farm, и укажи свой ID: {user_id}*",
                             parse_mode='Markdown')
        else:
            needed = 30 - balance
            bot.send_message(message.chat.id, 
                             f"❌ У тебя пока только {round(balance, 1)} RBX.\n"
                             f"Для вывода нужно минимум 30 RBX. Тебе осталось нафармить: **{round(needed, 1)}** RBX.",
                             parse_mode='Markdown')


# --- КОД ДЛЯ RENDER ---
app = Flask(__name__)

@app.route('/')
def health():
    return "Bot is running", 200

def run_bot():
    print("Бот запущен...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
