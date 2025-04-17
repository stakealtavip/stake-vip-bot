import telebot
from telebot import types
import uuid
import requests
import os
from dotenv import load_dotenv
import time

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
MERCADO_PAGO_TOKEN = os.getenv("ACCESS_TOKEN_MP")
ADMIN_ID = os.getenv("ADMIN_ID")  # ID do admin para receber notificações

bot = telebot.TeleBot(TOKEN)

def gerar_pix_mp(valor, descricao):
    url = "https://api.mercadopago.com/v1/payments"
    headers = {
        "Authorization": f"Bearer {MERCADO_PAGO_TOKEN}",
        "Content-Type": "application/json",
        "X-Idempotency-Key": str(uuid.uuid4())
    }
    payload = {
        "transaction_amount": float(valor),
        "description": descricao,
        "payment_method_id": "pix",
        "payer": {
            "email": f"{uuid.uuid4().hex[:6]}@email.com"
        }
    }
    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    if "point_of_interaction" in data:
        transacao = data["point_of_interaction"]["transaction_data"]
        return data["id"], transacao["qr_code"], transacao["qr_code_base64"]
    else:
        return None, None, None

def verificar_pagamento(payment_id):
    url = f"https://api.mercadopago.com/v1/payments/{payment_id}"
    headers = {"Authorization": f"Bearer {MERCADO_PAGO_TOKEN}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        status = response.json().get("status")
        return status == "approved"
    return False

@bot.message_handler(commands=["start"])
def boas_vindas(message):
    texto = (
        "👋 *Bem-vindo(a) ao Clube da Stake Alta!* \n\n"
        "💎✨ MENSAGEM PARA OS GVIPS ✨💎\n\n"
        "Sejam muito bem-vindos ao GVIPS, o grupo onde o jogo é de alto nível e os resultados falam mais alto que promessas.\n\n"
        "Aqui você encontra:\n"
        "🔒 Entradas exclusivas\n📊 Análises cirúrgicas\n🛡 Gestão de risco\n🔥 Oportunidades únicas\n\n"
        "🚨 *Escolha um plano abaixo para começar:*"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Mensal - R$50", callback_data="plano_50_Mensal"),
        types.InlineKeyboardButton("Vitalício - R$100", callback_data="plano_100_Vitalício")
    )
    bot.send_message(message.chat.id, texto, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def processar_plano(call):
    try:
        dados = call.data.split("_")
        valor = float(dados[1])
        descricao = dados[2]

        payment_id, copiaecola, qr_base64 = gerar_pix_mp(valor, descricao)
        if payment_id:
            imagem_bytes = requests.get(f"https://api.qrserver.com/v1/create-qr-code/?data={copiaecola}").content
            bot.send_photo(call.message.chat.id, imagem_bytes, caption=f"📌 *Plano:* {descricao}\n💰 *Valor:* R${valor}\n\n✅ Pague o Pix usando o QR Code ou copie o código abaixo:", parse_mode="Markdown")
            bot.send_message(call.message.chat.id, f"🔁 Código copia e cola:\n`{copiaecola}`", parse_mode="Markdown")

            bot.send_message(call.message.chat.id, "⏳ Verificando pagamento automaticamente... aguarde.")

            for i in range(10):  # Tenta por 2 minutos
                if verificar_pagamento(payment_id):
                    nome = call.from_user.first_name
                    bot.send_message(call.message.chat.id, "✅ Pagamento aprovado! Você receberá o acesso VIP em instantes.")
                    bot.send_message(ADMIN_ID, f"📢 {nome} realizou o pagamento!\nPlano escolhido: *{descricao}* ✅", parse_mode="Markdown")
                    return
                time.sleep(12)

            bot.send_message(call.message.chat.id, "⏱ Ainda não identificamos o pagamento. Caso já tenha pago, aguarde ou entre em contato com o suporte.")
        else:
            bot.send_message(call.message.chat.id, "❌ Erro ao gerar Pix.")
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Ocorreu um erro: {str(e)}")

print("Bot rodando...")
bot.infinity_polling()
