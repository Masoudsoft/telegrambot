from flask import Flask, request
import telebot
import os
import sqlite3
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

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

# 🌐 Webhook route
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

# ✅ ارسال خوشامدگویی به کاربر
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 سلام! به *دفترچه خاطرات دیجیتال* خوش اومدی!\n\n📝 می‌تونی هر چیزی که دوست داری بنویسی و من برات ذخیره‌ش می‌کنم.\n\nبرای دیدن خاطراتت، دستور `/all` رو بفرست.\nبرای نمایش ۵ پیام آخر، از دستور `/show` استفاده کن.")

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

# 📤 دستور برای دیدن تمام پیام‌ها
@bot.message_handler(commands=['all'])
def show_all_messages(message):
    user_id = message.from_user.id
    cursor.execute('SELECT text, date FROM messages WHERE user_id = ? ORDER BY date DESC', (user_id,))
    rows = cursor.fetchall()

    if rows:
        reply = "\n\n".join([f"📝 {row[0]}\n🕒 {row[1]}" for row in rows])
    else:
        reply = "هیچ پیامی یافت نشد."

    bot.reply_to(message, reply)

# 📤 دستور برای حذف آخرین پیام
@bot.message_handler(commands=['delete'])
def delete_message(message):
    user_id = message.from_user.id
    cursor.execute('DELETE FROM messages WHERE user_id = ? ORDER BY date DESC LIMIT 1', (user_id,))
    conn.commit()
    bot.reply_to(message, "✅ آخرین پیام شما حذف شد.")

# 📤 دستور برای حذف تمام پیام‌ها
@bot.message_handler(commands=['clear'])
def clear_messages(message):
    user_id = message.from_user.id
    cursor.execute('DELETE FROM messages WHERE user_id = ?', (user_id,))
    conn.commit()
    bot.reply_to(message, "✅ تمام پیام‌های شما پاک شد.")

# 📤 دستور برای نمایش تعداد پیام‌ها
@bot.message_handler(commands=['count'])
def count_messages(message):
    user_id = message.from_user.id
    cursor.execute('SELECT COUNT(*) FROM messages WHERE user_id = ?', (user_id,))
    count = cursor.fetchone()[0]
    bot.reply_to(message, f"شما {count} پیام ذخیره کرده‌اید.")

# 📤 دستور برای نمایش پیام تصادفی
@bot.message_handler(commands=['random'])
def random_message(message):
    user_id = message.from_user.id
    cursor.execute('SELECT text, date FROM messages WHERE user_id = ? ORDER BY RANDOM() LIMIT 1', (user_id,))
    row = cursor.fetchone()
    if row:
        bot.reply_to(message, f"📝 پیام تصادفی شما:\n\n{row[0]}\n🕒 {row[1]}")
    else:
        bot.reply_to(message, "هیچ پیام ذخیره‌شده‌ای پیدا نشد.")

# 📤 دستور برای جستجو در پیام‌ها
@bot.message_handler(commands=['search'])
def search_message(message):
    msg = bot.reply_to(message, "لطفاً کلمه‌ای برای جستجو وارد کن:")
    bot.register_next_step_handler(msg, process_search)

def process_search(message):
    search_term = message.text
    user_id = message.from_user.id
    cursor.execute('SELECT text, date FROM messages WHERE user_id = ? AND text LIKE ? ORDER BY date DESC', (user_id, f'%{search_term}%'))
    rows = cursor.fetchall()
    if rows:
        reply = "\n\n".join([f"📝 {row[0]}\n🕒 {row[1]}" for row in rows])
    else:
        reply = "هیچ پیامی یافت نشد."
    bot.reply_to(message, reply)

# 📤 دستور برای تنظیم یادآوری
scheduler = BackgroundScheduler()

@bot.message_handler(commands=['reminder'])
def set_reminder(message):
    msg = bot.reply_to(message, "لطفاً متن یادآوری و زمان رو وارد کن. (مثلاً: 'یادآوری: 2025-04-22 12:00')")
    bot.register_next_step_handler(msg, process_reminder)

def process_reminder(message):
    reminder_info = message.text.split(":")
    reminder_text = reminder_info[0].strip()
    reminder_time = datetime.strptime(reminder_info[1].strip(), '%Y-%m-%d %H:%M')
    scheduler.add_job(reminder, 'date', run_date=reminder_time, args=[message, reminder_text])
    bot.reply_to(message, f"✅ یادآوری برای پیام '{reminder_text}' در {reminder_time} تنظیم شد.")

def reminder(message, reminder_text):
    bot.send_message(message.chat.id, f"⏰ یادآوری: {reminder_text}")

# 📤 دستور برای آمار استفاده
@bot.message_handler(commands=['stats'])
def show_stats(message):
    cursor.execute('SELECT COUNT(*) FROM messages')
    total_messages = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(DISTINCT user_id) FROM messages')
    unique_users = cursor.fetchone()[0]
    bot.reply_to(message, f"📊 آمار ربات:\n\n- تعداد کل پیام‌ها: {total_messages}\n- تعداد کاربران منحصر به فرد: {unique_users}")

# 📤 دستور برای راهنمایی
@bot.message_handler(commands=['help'])
def help(message):
    help_text = """
    سلام! به ربات دفترچه خاطرات خوش آمدید. شما می‌توانید از دستورات زیر استفاده کنید:

    - /start: شروع مکالمه با ربات
    - /show: نمایش ۵ پیام آخر
    - /all: نمایش تمام پیام‌ها
    - /delete: حذف آخرین پیام
    - /clear: حذف تمام پیام‌ها
    - /count: تعداد پیام‌های ذخیره‌شده
    - /random: دریافت یک پیام تصادفی
    - /search: جستجوی پیام‌ها
    - /reminder: تنظیم یادآوری
    - /stats: مشاهده آمار
    """
    bot.reply_to(message, help_text)

# 🚀 اجرای Flask
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
