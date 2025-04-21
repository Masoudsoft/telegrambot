import os
import sqlite3
from flask import Flask, request
import telebot
from telebot import types

TOKEN = "YOUR_BOT_TOKEN"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# اتصال به دیتابیس
conn = sqlite3.connect("messages.db", check_same_thread=False)
cursor = conn.cursor()

# ایجاد جدول در صورت نبودش
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

# منوی اصلی
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📝 ارسال متن", "📷 ارسال عکس")
    markup.row("📖 مشاهده خاطرات", "🔍 جستجو")
    return markup

# استارت و نمایش منو
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(
        message.chat.id,
        "👋 خوش اومدی به دفترچه خاطرات دیجیتال!\n\n"
        "از منوی زیر استفاده کن یا متنی بفرست تا ذخیره بشه 😊",
        reply_markup=main_menu()
    )

# دریافت متن کاربر
@bot.message_handler(func=lambda m: m.text == "📝 ارسال متن")
def ask_for_note(message):
    bot.send_message(message.chat.id, "✍️ لطفاً متنت رو بفرست.")

@bot.message_handler(func=lambda m: m.text == "📖 مشاهده خاطرات")
def show_notes(message):
    cursor.execute('''
        SELECT text, date FROM messages
        WHERE user_id = ? AND text IS NOT NULL
        ORDER BY date DESC LIMIT 5
    ''', (message.from_user.id,))
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            bot.send_message(message.chat.id, f"📝 {row[0]}\n📅 {row[1]}")
    else:
        bot.send_message(message.chat.id, "هنوز خاطره‌ای ثبت نکردی.")

@bot.message_handler(func=lambda m: m.text == "🔍 جستجو")
def ask_search_query(message):
    bot.send_message(message.chat.id, "🔍 لطفاً واژه‌ای برای جستجو بفرست.")

# ذخیره متن اگر دستور خاص نبود
@bot.message_handler(func=lambda message: message.text not in [
    "📝 ارسال متن", "📖 مشاهده خاطرات", "📷 ارسال عکس", "🔍 جستجو"
])
def save_text(message):
    if message.reply_to_message and "🔍 لطفاً واژه‌ای برای جستجو" in message.reply_to_message.text:
        query = message.text
        cursor.execute('''
            SELECT text, date FROM messages
            WHERE user_id = ? AND text LIKE ?
            ORDER BY date DESC
        ''', (message.from_user.id, f"%{query}%"))
        results = cursor.fetchall()
        if results:
            for row in results:
                bot.send_message(message.chat.id, f"📝 {row[0]}\n📅 {row[1]}")
        else:
            bot.send_message(message.chat.id, "چیزی پیدا نشد.")
    else:
        cursor.execute('''
            INSERT INTO messages (user_id, username, text)
            VALUES (?, ?, ?)
        ''', (message.from_user.id, message.from_user.username, message.text))
        conn.commit()
        bot.send_message(message.chat.id, "✅ متن ذخیره شد.")

# دریافت عکس
@bot.message_handler(content_types=['photo'])
def save_photo(message):
    photo_id = message.photo[-1].file_id
    cursor.execute('''
        INSERT INTO messages (user_id, username, photo_file_id)
        VALUES (?, ?, ?)
    ''', (message.from_user.id, message.from_user.username, photo_id))
    conn.commit()
    bot.send_message(message.chat.id, "✅ عکس ذخیره شد.")

# Flask Webhook
@app.route(f"/{TOKEN}", methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

@app.route('/')
def index():
    return "ربات در حال اجراست 🚀"

# راه‌اندازی Webhook
import requests
WEBHOOK_URL = "https://telegrambot-9hq7.onrender.com/" + TOKEN
requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={WEBHOOK_URL}")

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
