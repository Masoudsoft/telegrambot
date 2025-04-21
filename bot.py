from flask import Flask, request
import telebot
import os
import sqlite3

API_TOKEN = '8099196414:AAFUYCNnj9vq-h4MScsLPSuIcHNUzySWmQ0'

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# 📁 اتصال به دیتابیس
conn = sqlite3.connect('messages.db', check_same_thread=False)
cursor = conn.cursor()

# 📌 ایجاد جدول اگر وجود نداشت
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

# ✅ خوش‌آمدگویی
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "👋 سلام! به *دفترچه خاطرات دیجیتال* خوش اومدی!\n\n"
        "📝 می‌تونی خاطره‌هاتو برام بفرستی، متن یا عکس یا هرچی!\n"
        "من برات ذخیره‌شون می‌کنم.\n\n"
        "🔻 دستورات:\n"
        "/start - پیام خوش‌آمد و راهنما\n"
        "/show - نمایش ۵ یادداشت آخر\n"
        "/all - نمایش همه یادداشت‌ها\n"
        "/search [کلمه] - جستجوی پیام\n"
        "/photos - نمایش ۵ عکس آخر\n"
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

# ✅ ذخیره پیام متنی
@bot.message_handler(func=lambda message: True, content_types=['text'])
def save_message(message):
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

# ✅ ذخیره عکس با کپشن
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.from_user.id
    username = message.from_user.username
    photo = message.photo[-1]  # بزرگ‌ترین سایز
    file_id = photo.file_id
    caption = message.caption or ""

    try:
        cursor.execute('''
            INSERT INTO messages (user_id, username, text, photo_file_id)
            VALUES (?, ?, ?, ?)
        ''', (user_id, username, caption, file_id))
        conn.commit()
        bot.reply_to(message, "✅ عکس شما ذخیره شد.")
    except Exception as e:
        print(f"Error saving photo: {e}")
        bot.reply_to(message, "❌ مشکلی در ذخیره عکس پیش آمد.")

# ✅ نمایش ۵ پیام آخر
@bot.message_handler(commands=['show'])
def show_messages(message):
    user_id = message.from_user.id
    cursor.execute('SELECT text, date FROM messages WHERE user_id = ? AND text IS NOT NULL ORDER BY date DESC LIMIT 5', (_
