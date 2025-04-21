from flask import Flask, request
import telebot
import os
import sqlite3

API_TOKEN = '8099196414:AAFUYCNnj9vq-h4MScsLPSuIcHNUzySWmQ0'

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# ✅ پیام خوش‌آمد هنگام start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(
        message,
        "👋 سلام! به *دفترچه خاطرات دیجیتال* خوش اومدی!\n\n"
        "📝 می‌تونی هر چیزی که دوست داری بنویسی و من برات ذخیره‌ش می‌کنم.\n\n"
        "برای دیدن تمام یادداشت‌هات، دستور /all رو بفرست.",
        parse_mode='Markdown'
    )

# ✅ دستور /all برای نمایش همه پیام‌های کاربر
@bot.message_handler(commands=['all'])
def show_all_messages(message):
    user_id = message.from_user.id
    cursor.execute('SELECT text, date FROM messages WHERE user_id = ? ORDER BY date DESC', (user_id,))
    rows = cursor.fetchall()

    if rows:
        reply = "\n\n".join([f"📝 {row[0]}\n🕒 {row[1]}" for row in rows])
    else:
        reply = "📭 هنوز هیچ یادداشتی ثبت نکردی."

    bot.reply_to(message, reply)

# 📁 اتصال به دیتابیس SQLite
conn = sqlite3.connect('messages.db', check_same_thread=False)
cursor = conn.cursor()

# 📌 ساخت جدول در صورت نبود
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

# ✅ ذخیره پیام‌ها (فقط پیام‌های متنی معمولی، نه دستورها)
@bot.message_handler(func=lambda message: message.text and not message.text.startswith('/'))
def save_message(message):
    user_id = message.from_user.id
    username = message.from_user.username
    text = message.text

    cursor.execute('INSERT INTO messages (user_id, username, text) VALUES (?, ?, ?)',
                   (user_id, username, text))
    conn.commit()

    bot.reply_to(message, "✅ پیام شما ذخیره شد.")

# 🔗 Webhook endpoint برای دریافت پیام از تلگرام
@app.route(f'/{API_TOKEN}', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '', 200

# 🌐 آدرس اصلی برای تست
@app.route('/')
def index():
    return 'ربات فعال است.'

# 🚀 اجرای برنامه Flask
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
