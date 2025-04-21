import os
import sqlite3
import telebot
from flask import Flask, request

API_TOKEN = '8099196414:AAFUYCNnj9vq-h4MScsLPSuIcHNUzySWmQ0'
bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# اتصال به دیتابیس
conn = sqlite3.connect('messages.db', check_same_thread=False)
cursor = conn.cursor()

# ساخت جدول اگر وجود نداشته باشد
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

# ارسال منوی اصلی
def send_main_menu(chat_id):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📝 ارسال متن", "📷 ارسال عکس")
    markup.row("📚 مشاهده خاطرات", "🔍 جستجو")
    bot.send_message(chat_id, "یکی از گزینه‌ها رو انتخاب کن:", reply_markup=markup)

# پیام خوش‌آمدگویی
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(
        message.chat.id,
        "سلام! 👋\nبه ربات دفترچه خاطرات خوش اومدی.\n\n"
        "با این ربات می‌تونی یادداشت‌هات و خاطراتت رو ذخیره کنی و بعداً مرورشون کنی.\n\n"
        "دستورها:\n"
        "📝 ارسال متن\n📷 ارسال عکس\n📚 مشاهده خاطرات\n🔍 جستجو",
    )
    send_main_menu(message.chat.id)

# دکمه‌ها
@bot.message_handler(func=lambda message: message.text == "📝 ارسال متن")
def ask_for_text(message):
    bot.send_message(message.chat.id, "متنت رو برام بفرست:")

@bot.message_handler(func=lambda message: message.text == "📷 ارسال عکس")
def ask_for_photo(message):
    bot.send_message(message.chat.id, "عکست رو بفرست:")

@bot.message_handler(func=lambda message: message.text == "📚 مشاهده خاطرات")
def show_memories(message):
    cursor.execute('SELECT text, date FROM messages WHERE user_id = ? AND text IS NOT NULL ORDER BY date DESC LIMIT 5', (message.from_user.id,))
    rows = cursor.fetchall()
    if not rows:
        bot.send_message(message.chat.id, "خاطره‌ای پیدا نشد.")
    else:
        for text, date in rows:
            bot.send_message(message.chat.id, f"{date}:\n{text}")

@bot.message_handler(func=lambda message: message.text == "🔍 جستجو")
def ask_for_search(message):
    bot.send_message(message.chat.id, "عبارتی که می‌خوای جستجو کنی رو بفرست:")

# ذخیره متن
@bot.message_handler(content_types=['text'])
def save_text(message):
    if message.text in ["📝 ارسال متن", "📷 ارسال عکس", "📚 مشاهده خاطرات", "🔍 جستجو"]:
        return  # برای اینکه متن دکمه‌ها ذخیره نشه
    cursor.execute('INSERT INTO messages (user_id, username, text) VALUES (?, ?, ?)', (
        message.from_user.id,
        message.from_user.username,
        message.text
    ))
    conn.commit()
    bot.send_message(message.chat.id, "متنت ذخیره شد ✅")

# ذخیره عکس
@bot.message_handler(content_types=['photo'])
def save_photo(message):
    file_id = message.photo[-1].file_id
    cursor.execute('INSERT INTO messages (user_id, username, photo_file_id) VALUES (?, ?, ?)', (
        message.from_user.id,
        message.from_user.username,
        file_id
    ))
    conn.commit()
    bot.send_message(message.chat.id, "عکست ذخیره شد ✅")

# وبهوک
@app.route(f"/{API_TOKEN}", methods=['POST'])
def webhook():
    json_str = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '', 200

# تست محلی
@app.route('/', methods=['GET'])
def index():
    return "Bot is running."

# اجرای برنامه
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
