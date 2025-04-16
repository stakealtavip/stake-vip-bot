import telebot
import requests
import uuid
import base64
import io
import threading
import time
from datetime import datetime, timedelta
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# === CONFIG ===
TOKEN = '7776075436:AAFdPlLaseQkmFo7CQNFauhg-Wf8Nzhd1x0'
ACCESS_TOKEN_MP = 'APP_USR-7951666709252852-041313-728c6a5375bb603a60aaefcc56a776c4-583811745'
ADMIN_ID = 842820136  # Seu ID para notificações
TEMPO_EXPIRACAO_PIX = 5 * 60  # 5 minutos
INTERVALO_VERIFICACAO = 20  # Segundos

bot = telebot.TeleBot(TOKEN)
pagamentos_pendentes = {}  # {payment_id: {'chat_id': int, 'username': str, 'plano': str}}

# === COMANDO /start ===
@bot.message_handler(commands=['start'])
def start(message):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("💳 Plano Mensal - R$50", callback_data="plano_50_Mensal"),
        InlineKeyboardButton("💎 Plano Anual - R$300", callback_data="plano_300_Anual")
    )
    texto = (
        "💎✨ BEM-VINDO AO STAKE ALTA VIP ✨💎\n\n"
        "Escolha seu plano abaixo para gerar o Pix e garantir seu acesso VIP."
    )
    bot.send_message(message.chat.id, texto, reply_markup=markup)

# === GERAR PIX ===
def gerar_pix(valor, descricao):
    url = 'https://api.mercadopago.com/v1/payments'
    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN_MP}',
        'Content-Type': 'application/json',
        'X-Idempotency-Key': str(uuid.uuid4())
    }
    payload = {
        "transaction_amount": float(valor),
        "description": descricao,
        "payment_method_id": "pix",
        "payer": {"email": f"cliente_{uuid.uuid4().hex[:8]}@email.com"}
    }
    r = requests.post(url, headers=headers, json=payload)
    data = r.json()
    if "point_of_interaction" in data:
        qr_code = data["point_of_interaction"]["transaction_data"]["qr_code"]
        qr_img = data["point_of_interaction"]["transaction_data"]["qr_code_base64"]
        payment_id = data["id"]
        return payment_id, qr_code, qr_img
    return None, None, None

# === VERIFICAR STATUS DO PAGAMENTO ===
def verificar_status(payment_id):
    url = f"https://api.mercadopago.com/v1/payments/{payment_id}"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN_MP}"}
    r = requests.get(url, headers=headers)
    data = r.json()
    return data.get("status")

# === VERIFICAÇÃO AUTOMÁTICA EM BACKGROUND ===
def monitorar_pagamentos():
    while True:
        time.sleep(INTERVALO_VERIFICACAO)
        for payment_id in list(pagamentos_pendentes.keys()):
            status = verificar_status(payment_id)
            if status == 'approved':
                info = pagamentos_pendentes.pop(payment_id)
                bot.send_message(info['chat_id'], "✅ Pagamento aprovado! Aguarde ser adicionado ao grupo VIP.")
                aviso = f"🔔 Novo pagamento confirmado:\nUsuário: @{info['username']}\nPlano: {info['plano']}"
                bot.send_message(ADMIN_ID, aviso)

threading.Thread(target=monitorar_pagamentos, daemon=True).start()

# === CALLBACK DOS BOTÕES ===
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.data.startswith("plano_"):
        _, valor, plano = call.data.split("_")
        valor = float(valor)
        descricao = f"{plano} - R${valor}"
        payment_id, codigo, qr_img = gerar_pix(valor, descricao)

        if payment_id:
            pagamentos_pendentes[payment_id] = {
                'chat_id': call.message.chat.id,
                'username': call.from_user.username or 'sem_username',
                'plano': plano
            }
            img = io.BytesIO(base64.b64decode(qr_img))
            img.name = "pix.png"
            bot.send_photo(call.message.chat.id, img, caption=f"📸 Escaneie ou copie:\n`{codigo}`", parse_mode="Markdown")
            bot.send_message(call.message.chat.id, "⏳ Estamos monitorando seu pagamento. O código expira em 5 minutos.")
        else:
            bot.send_message(call.message.chat.id, "❌ Erro ao gerar Pix. Tente novamente.")

# === COMANDO /id (opcional) ===
@bot.message_handler(commands=['id'])
def pegar_id(message):
    bot.send_message(message.chat.id, f"🆔 ID deste chat: `{message.chat.id}`", parse_mode="Markdown")

# === INICIAR O BOT ===
print("🤖 Bot rodando...")
bot.infinity_polling()
