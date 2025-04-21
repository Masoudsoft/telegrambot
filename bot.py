from flask import Flask, request
import telebot
import os
import sqlite3

API_TOKEN = '8099196414:AAFUYCNnj9vq-h4MScsLPSuIcHNUzySWmQ0'
WEBHOOK_URL = f'https://telegrambot-9hq7.onrender.com/{API_TOKEN}'

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# اتصال به دیتابیس
conn = sqlite3.connect('messages.db', check_same_thread=False)
cursor = conn.cursor()

# ایجاد جدول پیام‌ها
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

# 🟢 پیام خوش‌آمد برای /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    text = (
        "👋 *سلام!*\n"
        "به *دفترچه خاطرات دیجیتال* خوش اومدی!\n\n"
        "📌 اینجا می‌تونی یادداشت‌ها و خاطراتت رو بنویسی و ذخیره کنی.\n"
        "هر موقع دوست داشتی بنویس، من برات نگه‌می‌دارم 😊\n\n"
        "🛠 دستورات من:\n"
        "/start - نمایش خوش‌آمدگویی\n"
        "/show - نمایش ۵ پیام آخر\n"
        "/all - نمایش همه پیام‌ها\n"
        "/search کلمه - جستجو در پیام‌ها\n"
        "/feedback متن - ارسال بازخورد\n"
    )
    bot.reply_to(message, text, parse_mode="Markdown")

# ذخیره پیام
@bot.message_handler(func=lambda message: not message.text.startswith('/'))
def save_note(message):
    try:
        cursor.execute('INSERT INTO messages (user_id, username, text) VALUES (?, ?, ?)', (
            message.from_user.id,
            message.from_user.username,
            message.text
        ))
        conn.commit()
        bot.reply_to(message, "✅ پیام شما ذخیره شد.")
    except Exception as e:
        print(e)
        bot.reply_to(message, "❌ خطا در ذخیره پیام.")

# نمایش ۵ پیام آخر
@bot.message_handler(commands=['show'])
def show_notes(message):
    cursor.execute('SELECT text, date FROM messages WHERE user_id = ? ORDER BY date DESC LIMIT 5', (message.from_user.id,))
    notes = cursor.fetchall()
    if notes:
        response = "\n\n".join([f"📝 {n[0]}\n🕒 {n[1]}" for n in notes])
    else:
        response = "هیچ پیامی ثبت نشده."
    bot.reply_to(message, response)

# نمایش همه پیام‌ها
@bot.message_handler(commands=['all'])
def all_notes(message):
    cursor.execute('SELECT text, date FROM messages WHERE user_id = ? ORDER BY date DESC', (message.from_user.id,))
    notes = cursor.fetchall()
    if notes:
        response = "\n\n".join([f"📝 {n[0]}\n🕒 {n[1]}" for n in notes])
    else:
        response = "هیچ پیامی ثبت نشده."
    bot.reply_to(message, response)

# جستجوی پیام
@bot.message_handler(commands=['search'])
def search_notes(message):
    args = message.text.split(' ', 1)
    if len(args) < 2:
        bot.reply_to(message, "🔎 لطفاً کلمه‌ای برای جستجو وارد کنید.")
        return
    query = args[1]
    cursor.execute('SELECT text, date FROM messages WHERE user_id = ? AND text LIKE ?', (
        message.from_user.id, f'%{query}%'
    ))
    results = cursor.fetchall()
    if results:
        reply = "\n\n".join([f"📝 {r[0]}\n🕒 {r[1]}" for r in results])
    else:
        reply = "هیچ نتیجه‌ای یافت نشد."
    bot.reply_to(message, reply)

# ارسال بازخورد
@bot.message_handler(commands=['feedback'])
def feedback(message):
    args = message.text.split(' ', 1)
    if len(args) < 2:
        bot.reply_to(message, "✏️ لطفاً متن بازخورد خود را وارد کنید.")
        return
    feedback_text = f"بازخورد: {args[1]}"
    cursor.execute('INSERT INTO messages (user_id, username, text) VALUES (?, ?, ?)', (
        message.from_user.id,
        message.from_user.username,
        feedback_text
    ))
    conn.commit()
    bot.reply_to(message, "✅ بازخورد شما ثبت شد. ممنون!")

# وبهوک
@app.route(f'/{API_TOKEN}', methods=['POST'])
def receive_update():
    update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
    bot.process_new_updates([update])
    return '', 200

# تست سلامت سرور
@app.route('/')
def index():
    return '🤖 ربات دفترچه خاطرات فعال است.'

# اجرای برنامه
if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
