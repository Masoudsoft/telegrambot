from flask import Flask, request
import telebot
import os

API_TOKEN = '8099196414:AAFUYCNnj9vq-h4MScsLPSuIcHNUzySWmQ0' 

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

@app.route(f'/{API_TOKEN}', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '', 200

@app.route('/')
def index():
    return 'ربات فعال است.'
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, "پیامت دریافت شد 😊")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, "✅ پیام شما دریافت شد: " + message.text)
