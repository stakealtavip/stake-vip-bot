import telebot
import requests
import uuid
import json
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ACCESS_TOKEN_MP = os.getenv("ACCESS_TOKEN_MP")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telebot.TeleBot(BOT_TOKEN)

# Função para gerar pagamento no Mercado Pago
def gerar_pagamento(valor):
    url = "https://api.mercadopago.com/v1/payments"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN_MP}",
        "Content-Type": "application/json"
    }
    body = {
        "transaction_amount": float(valor),
        "description": "Acesso VIP Telegram",
        "payment_method_id": "pix",
        "payer": {"email": f"{uuid.uuid4().hex[:8]}@email.com"}
    }

    response = requests.post(url, headers=headers, data=json.dumps(body))
    if response.ok:
        data = response.json()
        return {
            "qr_code": data["point_of_interaction"]["transaction_data"]["qr_code"],
            "qr_code_base64": data["point_of_interaction"]["transaction_data"]["qr_code_base64"],
            "id": data["id"]
        }
    else:
        print("Erro ao gerar Pix:", response.text)
        return None

# Início /start
@bot.message_handler(commands=["start"])
def start(message):
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("📄 Plano Mensal - R$50", callback_data="plano_50"),
        InlineKeyboardButton("💎 Plano Anual - R$300", callback_data="plano_300")
    )
    bot.send_message(
        message.chat.id,
        "✨👑 BEM-VINDO AO STAKE ALTA VIP 👑✨\n\nEscolha seu plano abaixo para gerar o Pix e garantir seu acesso VIP.",
        reply_markup=markup
    )

# Recebe botão
@bot.callback_query_handler(func=lambda call: call.data.startswith("plano_"))
def gerar_pix(call):
    valor = call.data.split("_")[1]
    pagamento = gerar_pagamento(valor)
    if pagamento:
        bot.send_message(call.message.chat.id, f"🔐 Copie o código Pix abaixo e pague via seu app bancário:\n\n`{pagamento['qr_code']}`", parse_mode="Markdown")
        bot.send_photo(call.message.chat.id, f"https://api.qrserver.com/v1/create-qr-code/?data={pagamento['qr_code']}&size=300x300")
        bot.send_message(ADMIN_ID, f"📥 Nova tentativa de pagamento de R${valor}.\nID da transação: {pagamento['id']}")
    else:
        bot.send_message(call.message.chat.id, "❌ Erro ao gerar o Pix. Tente novamente mais tarde.")

# /id para debug
@bot.message_handler(commands=["id"])
def enviar_id(message):
    bot.reply_to(message, f"Este chat ID é: `{message.chat.id}`", parse_mode="Markdown")

print("BOT ONLINE - MODO POLLING ✅")
bot.infinity_polling()
