import telebot
import requests
import os
from flask import Flask, request

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ACCESS_TOKEN_MP = os.environ.get("ACCESS_TOKEN_MP")
ADMIN_ID = os.environ.get("ADMIN_ID")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/", methods=["GET"])
def index():
    return "Bot está rodando com webhook!", 200

@bot.message_handler(commands=["start"])
def start(message):
    markup = telebot.types.InlineKeyboardMarkup()
    btn1 = telebot.types.InlineKeyboardButton("📄 Plano Mensal - R$50", callback_data="plano_50")
    btn2 = telebot.types.InlineKeyboardButton("💎 Plano Anual - R$300", callback_data="plano_300")
    markup.add(btn1, btn2)

    bot.send_message(message.chat.id, "✨ BEM-VINDO AO STAKE ALTA VIP 💰✨\n\nEscolha seu plano abaixo para gerar o Pix e garantir seu acesso VIP.", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "plano_50":
        valor = 50
    elif call.data == "plano_300":
        valor = 300
    else:
        return

    payload = {
        "transaction_amount": float(valor),
        "description": f"Plano VIP R${valor}",
        "payment_method_id": "pix",
        "payer": {"email": "comprador@email.com"},
    }

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN_MP}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post("https://api.mercadopago.com/v1/payments", json=payload, headers=headers)
        data = response.json()

        if response.status_code == 201:
            qr_code = data["point_of_interaction"]["transaction_data"]["qr_code"]
            qr_img = data["point_of_interaction"]["transaction_data"]["qr_code_base64"]
            bot.send_message(call.message.chat.id, f"📲 Escaneie o QR Code ou copie o código abaixo para pagar R${valor}:\n\n`{qr_code}`", parse_mode="Markdown")
            bot.send_photo(call.message.chat.id, photo=f"data:image/png;base64,{qr_img}")
            bot.send_message(ADMIN_ID, f"🟢 Novo pedido de pagamento gerado!\nUsuário: @{call.from_user.username or 'sem_username'}\nPlano: R${valor}")
        else:
            bot.send_message(call.message.chat.id, "❌ Erro ao gerar o Pix. Tente novamente mais tarde.")
            bot.send_message(ADMIN_ID, f"❌ Erro ao gerar Pix: {data}")
    except Exception as e:
        bot.send_message(call.message.chat.id, "❌ Erro ao processar seu pedido.")
        bot.send_message(ADMIN_ID, f"❌ Exceção: {str(e)}")

# Inicia o webhook apenas se rodando no Render
if __name__ == "__main__":
    import logging
    import sys
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)

    # Defina o domínio do seu serviço Render aqui:
    DOMAIN = "https://estaca-vip-bot.onrender.com"  # altere para o nome do seu serviço
    bot.remove_webhook()
    bot.set_webhook(url=f"{DOMAIN}/{BOT_TOKEN}")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
