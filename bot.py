from flask import Flask, request
import telebot
import os
import sqlite3

API_TOKEN = '8099196414:AAFUYCNnj9vq-h4MScsLPSuIcHNUzySWmQ0'  

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# 📁 اتصال به دیتابیس SQLite
conn = sqlite3.connect('messages.db', check_same_thread=False)
cursor = conn.cursor()

# 📌 ایجاد جدول اگر وجود نداشت
cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        text TEXT,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()

# ✅ ذخیره پیام‌ها
@bot.message_handler(func=lambda message: True)
def save_message(message):
    user_id = message.from_user.id
    username = message.from_user.username
    text = message.text

    cursor.execute('INSERT INTO messages (user_id, username, text) VALUES (?, ?, ?)',
                   (user_id, username, text))
    conn.commit()

    bot.reply_to(message, "✅ پیام شما ذخیره شد.")

# 📤 دستور برای دیدن ۵ پیام آخر
@bot.message_handler(commands=['show'])
def show_messages(message):
    user_id = message.from_user.id
    cursor.execute('SELECT text, date FROM messages WHERE user_id = ? ORDER BY date DESC LIMIT 5', (user_id,))
    rows = cursor.fetchall()

    if rows:
        reply = "\n\n".join([f"📝 {row[0]}\n🕒 {row[1]}" for row in rows])
    else:
        reply = "هیچ پیامی یافت نشد."

    bot.reply_to(message, reply)

# 🔗 Webhook route
@app.route(f'/{API_TOKEN}', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '', 200

# 🌐 روت تست ساده
@app.route('/')
def index():
    return 'ربات فعال است.'

# 🚀 اجرای Flask
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
