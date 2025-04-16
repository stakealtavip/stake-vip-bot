
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ACCESS_TOKEN_MP = os.getenv("ACCESS_TOKEN_MP")
ADMIN_ID = os.getenv("ADMIN_ID")

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("💳 Plano Mensal - R$50", callback_data="plano_50_Mensal"),
        InlineKeyboardButton("💎 Plano Anual - R$300", callback_data="plano_300_Anual")
    )
    texto = (
        "✨💰 BEM-VINDO AO STAKE ALTA VIP 💰✨\n\n"
        "Escolha seu plano abaixo para gerar o Pix e garantir seu acesso VIP."
    )
    bot.send_message(message.chat.id, texto, reply_markup=markup)

@bot.message_handler(commands=['id'])
def pegar_id(message):
    bot.send_message(message.chat.id, f"`ID deste chat: `{message.chat.id}`", parse_mode="Markdown")

bot.infinity_polling()
