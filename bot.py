import os
import sqlite3
from flask import Flask, request
import telebot
from telebot import types

API_TOKEN = "8099196414:AAFUYCNnj9vq-h4MScsLPSuIcHNUzySWmQ0"

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# 📦 اتصال به دیتابیس
conn = sqlite3.connect('messages.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        text TEXT,
        photo_file_id TEXT,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()

# 🎉 پیام خوش‌آمدگویی با دکمه‌ها
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('📝 ارسال متن', '🖼️ ارسال عکس')
    markup.row('📖 مشاهده خاطرات', '🔍 جستجو')
    bot.send_message(message.chat.id, "سلام! 👋\nبه ربات دفترچه یادداشت و خاطره خوش اومدی!\n\nمی‌تونی متن‌ و عکس‌هات رو ذخیره کنی و بعداً ببینی یا جستجو کنی.", reply_markup=markup)

# 📝 ذخیره متن
@bot.message_handler(func=lambda message: message.text == "📝 ارسال متن")
def ask_for_text(message):
    bot.send_message(message.chat.id, "متنت رو بفرست:")

@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text in ["📝 ارسال متن", "🖼️ ارسال عکس", "📖 مشاهده خاطرات", "🔍 جستجو", "/start"]:
        return  # جلوگیری از ذخیره دکمه‌ها یا دستورات
    cursor.execute('INSERT INTO messages (user_id, username, text) VALUES (?, ?, ?)',
                   (message.from_user.id, message.from_user.username, message.text))
    conn.commit()
    bot.send_message(message.chat.id, "یادداشتت ذخیره شد 📝")

# 🖼️ ذخیره عکس
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    photo_id = message.photo[-1].file_id
    cursor.execute('INSERT INTO messages (user_id, username, photo_file_id) VALUES (?, ?, ?)',
                   (message.from_user.id, message.from_user.username, photo_id))
    conn.commit()
    bot.send_message(message.chat.id, "عکست ذخیره شد 🖼️")

# 📖 مشاهده خاطرات
@bot.message_handler(func=lambda message: message.text == "📖 مشاهده خاطرات")
def show_memories(message):
    cursor.execute('SELECT text, date FROM messages WHERE user_id = ? AND text IS NOT NULL ORDER BY date DESC LIMIT 5', (message.from_user.id,))
    rows = cursor.fetchall()
    if rows:
        response = "📝 آخرین خاطراتت:\n\n"
        for row in rows:
            response += f"📅 {row[1]}\n{row[0]}\n\n"
    else:
        response = "خاطره‌ای پیدا نشد."
    bot.send_message(message.chat.id, response)

# 🔍 جستجو
@bot.message_handler(func=lambda message: message.text == "🔍 جستجو")
def ask_for_keyword(message):
    bot.send_message(message.chat.id, "کلمه‌ای که می‌خوای جستجو کنی رو بنویس:")

@bot.message_handler(func=lambda message: True)
def search_notes(message):
    keyword = message.text.strip()
    if not keyword or keyword in ["📝 ارسال متن", "🖼️ ارسال عکس", "📖 مشاهده خاطرات", "🔍 جستجو", "/start"]:
        return
    cursor.execute('SELECT text, date FROM messages WHERE user_id = ? AND text LIKE ?', (message.from_user.id, f"%{keyword}%"))
    rows = cursor.fetchall()
    if rows:
        response = "🔎 نتایج جستجو:\n\n"
        for row in rows:
            response += f"📅 {row[1]}\n{row[0]}\n\n"
    else:
        response = "موردی پیدا نشد."
    bot.send_message(message.chat.id, response)

# 🌐 Webhook برای Render
@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    return '', 403

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
