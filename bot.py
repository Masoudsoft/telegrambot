from flask import Flask, request
import telebot
import os
import sqlite3

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

# 📤 خوش‌آمدگویی و دستورات
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "👋 سلام! به *دفترچه خاطرات دیجیتال* خوش اومدی!\n\n"
        "📝 می‌تونی هر چیزی که دوست داری بنویسی و من برات ذخیره‌ش می‌کنم.\n\n"
        "در اینجا لیست دستورات من هست:\n\n"
        "/start - خوش‌آمدگویی و توضیحات\n"
        "/show - نمایش ۵ پیام آخر\n"
        "/all - نمایش همه پیام‌ها\n"
        "/help - برای کمک و توضیحات بیشتر\n"
        "/save - ذخیره کردن پیام\n"
        "/edit - ویرایش پیام\n"
        "/delete - حذف پیام\n"
        "/search - جستجوی پیام\n"
        "/remind - یادآوری پیام‌ها\n"
        "/stats - نمایش آمار پیام‌ها\n"
        "/feedback - ارسال بازخورد\n"
        "/feedback_view - مشاهده بازخوردها"
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

# ✅ ذخیره پیام‌ها
@bot.message_handler(func=lambda message: True)
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
        bot.reply_to(message, "❌ مشکلی در ذخیره پیام به وجود آمده.")

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

# 📤 دستور برای دیدن همه پیام‌ها
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

# 📤 دستور برای جستجوی پیام‌ها
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
            reply = "هیچ پیامی با این جستجو یافت نشد."
    else:
        reply = "لطفا کلمه‌ای برای جستجو وارد کنید."

    bot.reply_to(message, reply)

# 📤 دستور برای ارسال بازخورد
@bot.message_handler(commands=['feedback'])
def feedback(message):
    user_id = message.from_user.id
    feedback_text = message.text.split(' ', 1)[1] if len(message.text.split(' ', 1)) > 1 else ""
    
    if feedback_text:
        cursor.execute('INSERT INTO messages (user_id, username, text) VALUES (?, ?, ?)', 
                       (user_id, message.from_user.username, f"بازخورد: {feedback_text}"))
        conn.commit()
        bot.reply_to(message, "✅ بازخورد شما ذخیره شد.")
    else:
        bot.reply_to(message, "لطفا متن بازخورد خود را وارد کنید.")

# 🔗 Webhook route
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

# 🚀 اجرای Flask
if __name__ == '__main__':
    # این خط رو برای تست Polling اضافه کنین، اگر Webhook کار نکرد
    # bot.polling(none_stop=True)

    # تنظیم Webhook در صورت استفاده از آن
    bot.remove_webhook()
    bot.set_webhook(url='https://your-app-url.com/' + API_TOKEN)  # URL خودتون رو جایگزین کنین

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
