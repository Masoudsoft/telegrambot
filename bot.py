import telebot
from telebot import types
from flask import Flask, request
import sqlite3
import os

API_TOKEN = os.environ.get("BOT_TOKEN") or "توکن رباتت رو اینجا بذار"
bot = telebot.TeleBot(API_TOKEN)

app = Flask(__name__)

# 📌 ساخت دیتابیس اگر وجود نداشت
def init_db():
    conn = sqlite3.connect('messages.db')
    c = conn.cursor()
    c.execute('''
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
    conn.close()

init_db()

# 📌 منوی دکمه‌ها
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("📝 ارسال متن"), types.KeyboardButton("📷 ارسال عکس"))
    markup.row(types.KeyboardButton("📖 مشاهده خاطرات"), types.KeyboardButton("🔍 جستجو"))
    return markup

# 🚀 استارت ربات
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(
        message.chat.id,
        "👋 خوش اومدی به دفترچه خاطرات دیجیتال!\n\n"
        "با استفاده از منوی زیر می‌تونی متن یا عکس ذخیره کنی، خاطراتتو ببینی یا جستجو کنی:",
        reply_markup=main_menu()
    )

# 📝 دریافت متن
@bot.message_handler(func=lambda message: message.text == "📝 ارسال متن")
def ask_for_text(message):
    bot.send_message(message.chat.id, "لطفاً متنت رو بفرست تا ذخیره بشه.")

@bot.message_handler(func=lambda message: message.text and message.text not in [
    "📝 ارسال متن", "📷 ارسال عکس", "📖 مشاهده خاطرات", "🔍 جستجو"
])
def save_text(message):
    conn = sqlite3.connect('messages.db')
    c = conn.cursor()
    c.execute("INSERT INTO messages (user_id, username, text) VALUES (?, ?, ?)", (
        message.from_user.id,
        message.from_user.username,
        message.text
    ))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ متن ذخیره شد!")

# 📷 دریافت عکس
@bot.message_handler(func=lambda message: message.text == "📷 ارسال عکس")
def ask_for_photo(message):
    bot.send_message(message.chat.id, "لطفاً عکست رو بفرست تا ذخیره بشه.")

@bot.message_handler(content_types=['photo'])
def save_photo(message):
    photo_id = message.photo[-1].file_id
    conn = sqlite3.connect('messages.db')
    c = conn.cursor()
    c.execute("INSERT INTO messages (user_id, username, photo_file_id) VALUES (?, ?, ?)", (
        message.from_user.id,
        message.from_user.username,
        photo_id
    ))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ عکس ذخیره شد!")

# 📖 مشاهده خاطرات
@bot.message_handler(func=lambda message: message.text == "📖 مشاهده خاطرات")
def show_memories(message):
    conn = sqlite3.connect('messages.db')
    c = conn.cursor()
    c.execute('SELECT text, photo_file_id, date FROM messages WHERE user_id = ? ORDER BY date DESC LIMIT 5', (
        message.from_user.id,))
    rows = c.fetchall()
    conn.close()

    if not rows:
        bot.send_message(message.chat.id, "خاطره‌ای پیدا نشد 😔")
        return

    for row in rows:
        text, photo_file_id, date = row
        if photo_file_id:
            bot.send_photo(message.chat.id, photo_file_id, caption=f"🕓 {date}")
        elif text:
            bot.send_message(message.chat.id, f"{text}\n🕓 {date}")

# 🔍 جستجو
@bot.message_handler(func=lambda message: message.text == "🔍 جستجو")
def ask_for_keyword(message):
    bot.send_message(message.chat.id, "🔎 لطفاً کلمه‌ای برای جستجو بفرست.")

@bot.message_handler(func=lambda message: message.reply_to_message and "🔎 لطفاً کلمه‌ای برای جستجو" in message.reply_to_message.text)
def search_notes(message):
    keyword = message.text
    conn = sqlite3.connect('messages.db')
    c = conn.cursor()
    c.execute("SELECT text, date FROM messages WHERE user_id = ? AND text LIKE ?", (
        message.from_user.id,
        f'%{keyword}%'
    ))
    results = c.fetchall()
    conn.close()

    if results:
        for text, date in results:
            bot.send_message(message.chat.id, f"{text}\n🕓 {date}")
    else:
        bot.send_message(message.chat.id, "❌ چیزی پیدا نشد.")

# 🌐 Webhook برای Render
@app.route('/', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return 'ok', 200

# 🔧 تنظیم Webhook (فقط برای بار اول اجراش کن)
@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    webhook_url = 'https://telegrambot-9hq7.onrender.com'
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)
    return "Webhook set!"

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
