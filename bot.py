from flask import Flask, request
import telebot
import os
import sqlite3

API_TOKEN = '8099196414:AAFUYCNnj9vq-h4MScsLPSuIcHNUzySWmQ0'

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# اتصال به دیتابیس SQLite
conn = sqlite3.connect('messages.db', check_same_thread=False)
cursor = conn.cursor()

# ساخت جدول اگر وجود نداشت
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

# 🎉 خوش‌آمدگویی
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "👋 سلام! به *دفترچه خاطرات دیجیتال* خوش اومدی!\n\n"
        "📝 می‌تونی متن یا عکس ارسال کنی، من برات ذخیره می‌کنم.\n\n"
        "*دستورات ربات:*\n"
        "/start - شروع و خوش‌آمدگویی\n"
        "/show - نمایش ۵ پیام آخر\n"
        "/all - نمایش همه پیام‌ها\n"
        "/search کلمه - جستجو در پیام‌ها\n"
        "/feedback پیام - ارسال بازخورد\n"
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

# 📤 نمایش ۵ پیام آخر
@bot.message_handler(commands=['show'])
def show_messages(message):
    user_id = message.from_user.id
    cursor.execute('SELECT text, date FROM messages WHERE user_id = ? AND text IS NOT NULL ORDER BY date DESC LIMIT 5', (user_id,))
    rows = cursor.fetchall()

    if rows:
        reply = "\n\n".join([f"📝 {row[0]}\n🕒 {row[1]}" for row in rows])
    else:
        reply = "هیچ پیامی یافت نشد."
    bot.reply_to(message, reply)

# 📤 نمایش همه پیام‌ها
@bot.message_handler(commands=['all'])
def show_all_messages(message):
    user_id = message.from_user.id
    cursor.execute('SELECT text, date FROM messages WHERE user_id = ? AND text IS NOT NULL ORDER BY date DESC', (user_id,))
    rows = cursor.fetchall()

    if rows:
        reply = "\n\n".join([f"📝 {row[0]}\n🕒 {row[1]}" for row in rows])
    else:
        reply = "هیچ پیامی یافت نشد."
    bot.reply_to(message, reply)

# 🔍 جستجو
@bot.message_handler(commands=['search'])
def search_messages(message):
    user_id = message.from_user.id
    search_query = message.text.split(' ', 1)[1] if len(message.text.split(' ', 1)) > 1 else ""

    if search_query:
        cursor.execute('SELECT text, date FROM messages WHERE user_id = ? AND text LIKE ? ORDER BY date DESC',
                       (user_id, f'%{search_query}%'))
        rows = cursor.fetchall()

        if rows:
            reply = "\n\n".join([f"📝 {row[0]}\n🕒 {row[1]}" for row in rows])
        else:
            reply = "هیچ پیامی با این جستجو یافت نشد."
    else:
        reply = "لطفا کلمه‌ای برای جستجو وارد کنید."

    bot.reply_to(message, reply)

# 📬 بازخورد
@bot.message_handler(commands=['feedback'])
def feedback(message):
    user_id = message.from_user.id
    feedback_text = message.text.split(' ', 1)[1] if len(message.text.split(' ', 1)) > 1 else ""

    if feedback_text:
        cursor.execute('INSERT INTO messages (user_id, username, text) VALUES (?, ?, ?)',
                       (user_id, message.from_user.username, f"بازخورد: {feedback_text}"))
        conn.commit()
        bot.reply_to(message, "✅ بازخورد شما ذخیره شد.")
    else:
        bot.reply_to(message, "لطفا متن بازخورد خود را وارد کنید.")

# 📸 ذخیره عکس‌ها
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.from_user.id
    username = message.from_user.username
    photo_file_id = message.photo[-1].file_id  # بزرگ‌ترین سایز

    try:
        cursor.execute('INSERT INTO messages (user_id, username, photo_file_id) VALUES (?, ?, ?)',
                       (user_id, username, photo_file_id))
        conn.commit()
        bot.reply_to(message, "📸 عکس شما ذخیره شد.")
    except Exception as e:
        print(f"Error saving photo: {e}")
        bot.reply_to(message, "❌ مشکلی در ذخیره عکس به وجود آمده.")

# ✅ ذخیره پیام‌های متنی عادی (در انتهای فایل قرار داده شده!)
@bot.message_handler(func=lambda message: True, content_types=['text'])
def save_message(message):
    if message.text.startswith("/"):  # جلوگیری از ذخیره دستورات
        return

    user_id = message.from_user.id
    username = message.from_user.username
    text = message.text

    try:
        cursor.execute('INSERT INTO messages (user_id, username, text) VALUES (?, ?, ?)',
                       (user_id, username, text))
        conn.commit()
        bot.reply_to(message, "✅ پیام شما ذخیره شد.")
    except Exception as e:
        print(f"Error saving message: {e}")
        bot.reply_to(message, "❌ مشکلی در ذخیره پیام به وجود آمده.")

# 🔗 Webhook برای دریافت پیام‌ها از تلگرام
@app.route(f'/{API_TOKEN}', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '', 200

# 🌐 صفحه اصلی تست
@app.route('/')
def index():
    return 'ربات فعال است.'

# 🚀 اجرای برنامه
if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url='https://telegrambot-9hq7.onrender.com/' + API_TOKEN)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
