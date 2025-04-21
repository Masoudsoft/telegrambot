import telebot
from telebot import types
from flask import Flask, request
import sqlite3
import os

API_TOKEN = '8099196414:AAFUYCNnj9vq-h4MScsLPSuIcHNUzySWmQ0'
bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# اتصال به دیتابیس
conn = sqlite3.connect('messages.db', check_same_thread=False)
cursor = conn.cursor()

# ساخت جدول اگر وجود نداشته باشد
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

# کیبورد اصلی
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📝 ارسال متن", "📷 ارسال عکس")
    markup.add("📚 مشاهده خاطرات", "🔍 جستجو در خاطرات")
    return markup

# خوش‌آمدگویی
@bot.message_handler(commands=['start'])
def start(message):
    text = (
        "سلام 👋\n"
        "به ربات دفترچه خاطرات خوش اومدی!\n\n"
        "با این ربات می‌تونی متن‌ها و عکس‌های روزانه‌تو ذخیره کنی.\n"
        "از منوی زیر یکی از گزینه‌ها رو انتخاب کن.👇"
    )
    bot.send_message(message.chat.id, text, reply_markup=main_menu())

# ارسال متن
@bot.message_handler(func=lambda msg: msg.text == "📝 ارسال متن")
def ask_text(message):
    bot.send_message(message.chat.id, "متنت رو بفرست:")

# ذخیره متن
@bot.message_handler(content_types=['text'])
def save_text(message):
    if message.text in ["📝 ارسال متن", "📷 ارسال عکس", "📚 مشاهده خاطرات", "🔍 جستجو در خاطرات"]:
        return  # جلو ذخیره شدن دکمه‌ها گرفته بشه

    cursor.execute('INSERT INTO messages (user_id, username, text) VALUES (?, ?, ?)',
                   (message.from_user.id, message.from_user.username, message.text))
    conn.commit()
    bot.send_message(message.chat.id, "✅ متنت ذخیره شد.", reply_markup=main_menu())

# ارسال عکس
@bot.message_handler(func=lambda msg: msg.text == "📷 ارسال عکس")
def ask_photo(message):
    bot.send_message(message.chat.id, "عکست رو بفرست:")

# ذخیره عکس
@bot.message_handler(content_types=['photo'])
def save_photo(message):
    photo = message.photo[-1].file_id
    cursor.execute('INSERT INTO messages (user_id, username, photo_file_id) VALUES (?, ?, ?)',
                   (message.from_user.id, message.from_user.username, photo))
    conn.commit()
    bot.send_message(message.chat.id, "✅ عکس ذخیره شد.", reply_markup=main_menu())

# مشاهده آخرین خاطرات
@bot.message_handler(func=lambda msg: msg.text == "📚 مشاهده خاطرات")
def show_memories(message):
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
        bot.send_message(message.chat.id, "هیچ خاطره‌ای نداری هنوز 😔")

# جستجو در خاطرات
@bot.message_handler(func=lambda msg: msg.text == "🔍 جستجو در خاطرات")
def ask_query(message):
    bot.send_message(message.chat.id, "عبارتی که می‌خوای_
