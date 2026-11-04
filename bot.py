import telebot
from telebot import types
import time
import os
from flask import Flask
import threading

# Токен берем из настроек Render
TOKEN = os.environ.get('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TOKEN)

users_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if user_id not in users_data:
        users_data[user_id] = {'balance': 0, 'last_click': 0}
        
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn = types.KeyboardButton('👆 Фармить RBX')
    markup.add(btn)
    
    bot.send_message(message.chat.id, 
                     f"Привет, {message.from_user.first_name}! 👋\n"
                     f"Твой баланс: {users_data[user_id]['balance']} RBX.\n"
                     "Жми на кнопку и фарми робуксы!", 
                     reply_markup=markup)

@bot.message_handler(content_types=['text'])
def handle_text(message):
    # --- ЛОГИРОВАНИЕ СООБЩЕНИЙ ---
    # Это выведет текст в логи Render (в панели управления)
    print(f"[LOG] Пользователь {message.from_user.id} (@{message.from_user.username}) написал: {message.text}")
    
    if message.text == '👆 Фармить RBX':
        user_id = message.from_user.id
        current_time = time.time()
        
        if user_id not in users_data:
            users_data[user_id] = {'balance': 0, 'last_click': 0}

        time_passed = current_time - users_data[user_id]['last_click']
        
        if time_passed < 2:
            bot.send_message(message.chat.id, "⏳ Не так быстро! Подожди пару секунд.")
        else:
            users_data[user_id]['balance'] += 1
            users_data[user_id]['last_click'] = current_time
            bot.send_message(message.chat.id, f"✅ +1 RBX\n💰 Твой баланс: {users_data[user_id]['balance']} RBX")

# --- Код для работы на сервере Render ---
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
