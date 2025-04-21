import telebot
from flask import Flask, request
import sqlite3
import os

API_TOKEN = '8099196414:AAFUYCNnj9vq-h4MScsLPSuIcHNUzySWmQ0'
bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# دکمه‌ها
from telebot import types
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📝 ارسال متن", "🖼️ ارسال عکس")
    markup.row("📖 مشاهده خاطرات", "🔍 جستجو")
    return markup

# اتصال به دیتابیس
def init_db():
    conn = sqlite3.connect("messages.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  username TEXT,
                  text TEXT,
                  photo_file_id TEXT,
                  date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

# پاسخ به /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(
        message.chat.id,
        "سلام! 👋\nمن ربات دفترچه یادداشت و خاطرات تو هستم.\n\n📌 با این دکمه‌ها می‌تونی کار کنی:\n\n"
        "📝 ارسال متن - برای نوشتن خاطره یا یادداشت\n"
        "🖼️ ارسال عکس - برای ذخیره تصویر خاطرات\n"
        "📖 مشاهده خاطرات - دیدن ۵ مورد آخر\n"
        "🔍 جستجو - جستجو در خاطرات با کلمه کلیدی",
        reply_markup=main_menu()
    )

# ذخیره متن
@bot.message_handler(func=lambda m: m.text == "📝 ارسال متن")
def ask_for_text(message):
    bot.send_message(message.chat.id, "متنت رو بنویس تا ذخیره کنم:")

@bot.message_handler(func=lambda message: True, content_types=['text'])
def save_text(message):
    if message.text in ["📝 ارسال متن", "🖼️ ارسال عکس", "📖 مشاهده خاطرات", "🔍 جستجو"]:
        return  # برای جلوگیری از ذخیره خود دکمه‌ها
    conn = sqlite3.connect("messages.db")
    c = conn.cursor()
    c.execute("INSERT INTO messages (user_id, username, text) VALUES (?, ?, ?)",
              (message.from_user.id, message.from_user.username, message.text))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ متنت ذخیره شد.")

# ذخیره عکس
@bot.message_handler(func=lambda m: m.text == "🖼️ ارسال عکس")
def ask_for_photo(message):
    bot.send_message(message.chat.id, "عکست رو بفرست:")

@bot.message_handler(content_types=['photo'])
def save_photo(message):
    photo_id = message.photo[-1].file_id
    conn = sqlite3.connect("messages.db")
    c = conn.cursor()
    c.execute("INSERT INTO messages (user_id, username, photo_file_id) VALUES (?, ?, ?)",
              (message.from_user.id, message.from_user.username, photo_id))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ عکست ذخیره شد.")

# مشاهده خاطرات
@bot.message_handler(func=lambda m: m.text == "📖 مشاهده خاطرات")
def show_memories(message):
    conn = sqlite3.connect("messages.db")
    c = conn.cursor()
    c.execute('''SELECT text, date FROM messages
                 WHERE user_id = ? AND text IS NOT NULL
                 ORDER BY date DESC LIMIT 5''', (message.from_user.id,))
    results = c.fetchall()
    conn.close()
    if not results:
        bot.send_message(message.chat.id, "📭 هنوز متنی ذخیره نکردی.")
    else:
        response = "\n\n".join([f"🕒 {row[1]}\n📝 {row[0]}" for row in results])
        bot.send_message(message.chat.id, "📖 آخرین یادداشت‌ها:\n\n" + response)

# جستجو
@bot.message_handler(func=lambda m: m.text == "🔍 جستجو")
def ask_for_keyword(message):
    bot.send_message(message.chat.id, "🔎 کلمه‌ای که می‌خوای جستجو کنی رو بفرست:")

@bot.message_handler(func=lambda m: m.text and not m.text.startswith("/"))
def handle_search(message):
    keyword = message.text
    conn = sqlite3.connect("messages.db")
    c = conn.cursor()
    c.execute("SELECT text, date FROM messages WHERE user_id = ? AND text LIKE ?",
              (message.from_user.id, f"%{keyword}%"))
    results = c.fetchall()
    conn.close()
    if not results:
        bot.send_message(message.chat.id, "چیزی پیدا نشد.")
    else:
        response = "\n\n".join([f"🕒 {row[1]}\n📝 {row[0]}" for row in results])
        bot.send_message(message.chat.id, "نتایج جستجو:\n\n" + response)

# Flask
@app.route(f"/{API_TOKEN}", methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/", methods=['GET'])
def index():
    return "ربات فعال است."

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=port)
