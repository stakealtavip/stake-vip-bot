
import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
import datetime

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
CANAL_VIP_ID = int(os.getenv("CANAL_VIP_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def boas_vindas(message):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("✅ Já paguei", callback_data="paguei"),
        InlineKeyboardButton("📲 Gerar outro Pix", callback_data="gerar_pix")
    )
    bot.send_message(message.chat.id, "👋 Seja bem-vindo!

Envie a foto ou PDF do comprovante de pagamento:", reply_markup=markup)

@bot.message_handler(commands=['id'])
def pegar_id(message):
    bot.send_message(message.chat.id, f"🆔 ID deste chat: `{message.chat.id}`", parse_mode="Markdown")

@bot.message_handler(content_types=['document', 'photo'])
def receber_comprovante(message):
    bot.send_message(message.chat.id, "🔍 Verificando comprovante...")
    # Aqui entraria a verificação automática via API de pagamentos

    bot.send_message(message.chat.id, "✅ Pagamento confirmado! Em breve você será adicionado.")
    bot.send_message(ADMIN_ID, f"📩 Novo pagamento detectado!
Usuário: @{message.from_user.username}
ID: `{message.chat.id}`", parse_mode="Markdown")

print("🤖 Bot rodando...")
bot.infinity_polling()
    