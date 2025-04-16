import os
import telebot
import requests
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ACCESS_TOKEN_MP = os.getenv("ACCESS_TOKEN_MP")
ADMIN_ID = os.getenv("ADMIN_ID")

bot = telebot.TeleBot(BOT_TOKEN)

# Comando /start
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

# Comando /id
@bot.message_handler(commands=['id'])
def pegar_id(message):
    bot.send_message(message.chat.id, f"`ID deste chat: `{message.chat.id}", parse_mode="Markdown")

# Função para gerar QR Code e código copia e cola
def gerar_pix_qr(valor, descricao):
    url = "https://api.mercadopago.com/v1/payments"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN_MP}",
        "Content-Type": "application/json"
    }
    body = {
        "transaction_amount": float(valor),
        "description": descricao,
        "payment_method_id": "pix",
        "payer": {
            "email": "pagador@email.com",
            "first_name": "Cliente",
            "last_name": "StakeVIP"
        }
    }

    response = requests.post(url, headers=headers, json=body)
    if response.status_code == 201:
        data = response.json()
        qr_code = data["point_of_interaction"]["transaction_data"]["qr_code"]
        qr_base64 = data["point_of_interaction"]["transaction_data"]["qr_code_base64"]
        return qr_code, qr_base64
    else:
        return None, None

# Callback dos botões de plano
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "plano_50_Mensal":
        valor = 50
        descricao = "Plano Mensal"
    elif call.data == "plano_300_Anual":
        valor = 300
        descricao = "Plano Anual"
    else:
        return

    codigo, qr = gerar_pix_qr(valor, descricao)

    if codigo and qr:
        bot.send_photo(
            call.message.chat.id,
            photo=f"https://api.qrserver.com/v1/create-qr-code/?data={codigo}&size=300x300"
        )
        bot.send_message(
            call.message.chat.id,
            f"📲 Escaneie ou copie:\n`{codigo}`\n\nEstamos monitorando seu pagamento. O código expira em 5 minutos.",
            parse_mode="Markdown"
        )
    else:
        bot.send_message(call.message.chat.id, "❌ Erro ao gerar o Pix. Tente novamente mais tarde.")

bot.infinity_polling()
