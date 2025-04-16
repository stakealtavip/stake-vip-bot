import telebot
import os
from flask import Flask, request

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)
APP_URL = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/{BOT_TOKEN}"

# Flask
app = Flask(__name__)

# Rota para receber atualizações do Telegram
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

# Comando /start
@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(message, "👋 Bem-vindo ao bot!")

# Ativar webhook ao iniciar
@app.route("/", methods=["GET"])
def index():
    bot.remove_webhook()
    bot.set_webhook(url=APP_URL)
    return "Webhook configurado com sucesso!", 200
