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

# ایجاد جدول در صورت نبود
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

# دستور /start - خوش‌آمدگویی
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "👋 سلام! به *دفترچه خاطرات دیجیتال* خوش اومدی!\n\n"
        "📝 می‌تونی هر چیزی که دوست داری برام بنویسی؛ من برات ذخیره‌ش می‌کنم.\n"
        "بعداً هم می‌تونی همه‌ی نوشته‌هاتو ببینی، جستجو کنی یا ویرایششون کنی.\n\n"
        "📚 لیست دستوراتی که می‌تونی استفاده کنی:\n\n"
        "/start - خوش‌آمدگویی و معرفی\n"
        "/show - نمایش ۵ پیام آخر\n"
        "/all - نمایش همه پیام‌ها\n"
        "/search [کلمه] - جستجو در پیام‌ها\n"
        "/save - ذخیره پیام (به‌زودی)\n"
        "/edit - ویرایش پیام (به‌زودی)\n"
        "/delete - حذف پیام (به‌زودی)\n"
        "/remind - یادآوری پیام‌ها (در دست ساخت)\n"
        "/stats - نمایش آمار نوشته‌ها\n"
        "/feedback [متن] - ارسال بازخورد\n"
        "/feedback_view - مشاهده بازخوردها"
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

# دستور /show - نمایش ۵ پیام آخر
@bot.message_handler(commands=['show'])
def show_messages(message):
    user_id = message.from_user.id
    cursor.execute('SELECT text, date FROM messages WHERE user_id = ? ORDER BY date DESC LIMIT 5', (user_id,))
    rows = cursor.fetchall()

    if rows:
        reply = "\n\n".join([f"📝 {row[0]}\n🕒 {row[1]}" for row in rows])
    else:
        reply = "📭 هنوز پیامی ذخیره نکردی."

    bot.reply_to(message, reply)

# دستور /all - نمایش همه پیام‌ها
@bot.message_handler(commands=['all'])
def show_all_messages(message):
    user_id = message.from_user.id
    cursor.execute('SELECT text, date FROM messages WHERE user_id = ? ORDER BY date DESC', (user_id,))
    rows = cursor.fetchall()

    if rows:
        reply = "\n\n".join([f"📝 {row[0]}\n🕒 {row[1]}" for row in rows])
    else:
        reply = "📭 هنوز پیامی ذخیره نکردی."

    bot.reply_to(message, reply)

# دستور /search - جستجوی پیام‌ها
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
            reply = "🔍 هیچ چیزی با این عبارت پیدا نشد."
    else:
        reply = "لطفاً عبارتی برای جستجو وارد کن."

    bot.reply_to(message, reply)

# دستور /feedback - ارسال بازخورد
@bot.message_handler(commands=['feedback'])
def feedback(message):
    user_id = message.from_user.id
    feedback_text = message.text.split(' ', 1)[1] if len(message.text.split(' ', 1)) > 1 else ""

    if feedback_text:
        cursor.execute('INSERT INTO messages (user_id, username, text) VALUES (?, ?, ?)',
                       (user_id, message.from_user.username, f"بازخورد: {feedback_text}"))
        conn.commit()
        bot.reply_to(message, "✅ بازخوردت ثبت شد.")
    else:
        bot.reply_to(message, "لطفاً متن بازخوردت رو بنویس.")

# ذخیره پیام‌های معمولی (غیردستوری)
@bot.message_handler(func=lambda message: not message.text.startswith('/'))
def save_message(message):
    user_id = message.from_user.id
    username = message.from_user.username
    text = message.text

    try:
        cursor.execute('INSERT INTO messages (user_id, username, text) VALUES (?, ?, ?)', (user_id, username, text))
        conn.commit()
        bot.reply_to(message, "✅ پیام شما ذخیره شد.")
    except Exception as e:
        print(f"Error saving message: {e}")
        bot.reply_to(message, "❌ مشکلی در ذخیره پیام پیش اومد.")

# Webhook route
@app.route(f'/{API_TOKEN}', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '', 200

# Index route
@app.route('/')
def index():
    return '🤖 ربات دفترچه خاطرات فعال است.'

# اجرای اپلیکیشن
if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url='https://telegrambot-9hq7.onrender.com/' + API_TOKEN)

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
