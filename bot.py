from flask import Flask, request
import telebot
import os
import sqlite3

API_TOKEN = '8099196414:AAFUYCNnj9vq-h4MScsLPSuIcHNUzySWmQ0'
bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# اتصال به دیتابیس
conn = sqlite3.connect('messages.db', check_same_thread=False)
cursor = conn.cursor()

# ایجاد جدول در صورت نیاز
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

# پیام خوش‌آمدگویی
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "👋 سلام! به *دفترچه خاطرات دیجیتال* خوش اومدی!\n\n"
        "📝 می‌تونی هر چیزی که دوست داری بنویسی، عکس بفرستی و من برات ذخیره می‌کنم.\n\n"
        "دستورات:\n"
        "/start - شروع و توضیحات\n"
        "/show - نمایش ۵ پیام آخر\n"
        "/all - نمایش همه پیام‌ها\n"
        "/search [کلمه] - جستجو در پیام‌ها\n"
        "/feedback [متن] - ارسال بازخورد"
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

# ذخیره پیام متنی
@bot.message_handler(content_types=['text'])
def save_text(message):
    user_id = message.from_user.id
    username = message.from_user.username
    text = message.text

    try:
        cursor.execute(
            'INSERT INTO messages (user_id, username, text) VALUES (?, ?, ?)',
            (user_id, username, text)
        )
        conn.commit()
        bot.reply_to(message, "✅ پیام شما ذخیره شد.")
    except Exception as e:
        print(f"Error saving message: {e}")
        bot.reply_to(message, "❌ مشکلی در ذخیره پیام پیش آمد.")

# ذخیره عکس
@bot.message_handler(content_types=['photo'])
def save_photo(message):
    user_id = message.from_user.id
    username = message.from_user.username
    photo_id = message.photo[-1].file_id

    try:
        cursor.execute(
            'INSERT INTO messages (user_id, username, photo_file_id) VALUES (?, ?, ?)',
            (user_id, username, photo_id)
        )
        conn.commit()
        bot.reply_to(message, "📸 عکس شما ذخیره شد.")
    except Exception as e:
        print(f"Error saving photo: {e}")
        bot.reply_to(message, "❌ مشکلی در ذخیره عکس پیش آمد.")

# نمایش ۵ پیام آخر
@bot.message_handler(commands=['show'])
def show_messages(message):
    user_id = message.from_user.id
    cursor.execute(
        'SELECT text, photo_file_id, date FROM messages WHERE user_id = ? AND (text IS NOT NULL OR photo_file_id IS NOT NULL) ORDER BY date DESC LIMIT 5',
        (user_id,)
    )
    rows = cursor.fetchall()

    if rows:
        for row in rows:
            text, photo_id, date = row
            if photo_id:
                bot.send_photo(message.chat.id, photo_id, caption=f"🕒 {date}")
            if text:
                bot.send_message(message.chat.id, f"📝 {text}\n🕒 {date}")
    else:
        bot.reply_to(message, "هیچ پیامی یافت نشد.")

# نمایش همه پیام‌ها
@bot.message_handler(commands=['all'])
def show_all_messages(message):
    user_id = message.from_user.id
    cursor.execute(
        'SELECT text, photo_file_id, date FROM messages WHERE user_id = ? ORDER BY date DESC',
        (user_id,)
    )
    rows = cursor.fetchall()

    if rows:
        for row in rows:
            text, photo_id, date = row
            if photo_id:
                bot.send_photo(message.chat.id, photo_id, caption=f"🕒 {date}")
            if text:
                bot.send_message(message.chat.id, f"📝 {text}\n🕒 {date}")
    else:
        bot.reply_to(message, "هیچ پیامی یافت نشد.")

# جستجو
@bot.message_handler(commands=['search'])
def search_messages(message):
    user_id = message.from_user.id
    parts = message.text.split(' ', 1)
    if len(parts) < 2:
        bot.reply_to(message, "لطفا کلمه‌ای برای جستجو وارد کنید.")
        return

    search_query = parts[1]
    cursor.execute(
        'SELECT text, date FROM messages WHERE user_id = ? AND text LIKE ? ORDER BY date DESC',
        (user_id, f'%{search_query}%')
    )
    rows = cursor.fetchall()

    if rows:
        reply = "\n\n".join([f"📝 {row[0]}\n🕒 {row[1]}" for row in rows])
    else:
        reply = "هیچ پیامی با این جستجو یافت نشد."

    bot.reply_to(message, reply)

# بازخورد
@bot.message_handler(commands=['feedback'])
def feedback(message):
    user_id = message.from_user.id
    username = message.from_user.username
    parts = message.text.split(' ', 1)
    if len(parts) < 2:
        bot.reply_to(message, "لطفا متن بازخورد را وارد کنید.")
        return

    feedback_text = parts[1]
    cursor.execute(
        'INSERT INTO messages (user_id, username, text) VALUES (?, ?, ?)',
        (user_id, username, f"بازخورد: {feedback_text}")
    )
    conn.commit()
    bot.reply_to(message, "✅ بازخورد شما ذخیره شد.")

# Webhook
@app.route(f'/{API_TOKEN}', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '', 200

# مسیر تستی
@app.route('/')
def index():
    return 'ربات فعال است.'

# اجرای Flask و Webhook
if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url='https://telegrambot-9hq7.onrender.com/' + API_TOKEN)

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
