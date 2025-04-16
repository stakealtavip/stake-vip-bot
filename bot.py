import telebot
import requests
import os
from flask import Flask, request

# Variáveis de ambiente
BOT_TOKEN = os.getenv("BOT_TOKEN")
ACCESS_TOKEN_MP = os.getenv("ACCESS_TOKEN_MP")
ADMIN_ID = os.getenv("ADMIN_ID")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Função para gerar o Pix
def gerar_pix(valor):
    url = "https://api.mercadopago.com/v1/payments"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN_MP}",
        "Content-Type": "application/json"
    }
    payload = {
        "transaction_amount": float(valor),
        "description": f"Plano R${valor}",
        "payment_method_id": "pix",
        "payer": {
            "email": "pagador@email.com",
            "first_name": "Cliente",
            "last_name": "Bot"
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 201:
        dados = response.json()
        qr_code = dados['point_of_interaction']['transaction_data']['qr_code']
        return qr_code
    else:
        return None

# Comando /start
@bot.message_handler(commands=["start"])
def start(message):
    texto = (
        "✨ 👑 BEM-VINDO AO STAKE ALTA VIP 👑 ✨\n\n"
        "Escolha seu plano abaixo para gerar o Pix e garantir seu acesso VIP."
    )
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("📄 Plano Mensal - R$50", callback_data="plano_50"),
        telebot.types.InlineKeyboardButton("💎 Plano Anual - R$300", callback_data="plano_300")
    )
    bot.send_message(message.chat.id, texto, reply_markup=markup)

# Botão pressionado
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "plano_50":
        valor = 50
    elif call.data == "plano_300":
        valor = 300
    else:
        bot.answer_callback_query(call.id, "Plano inválido.")
        return

    qr = gerar_pix(valor)
    if qr:
        bot.send_message(call.message.chat.id, f"✅ Pix gerado para R${valor}:\n\n🔢 Copie e cole o código abaixo:\n\n`{qr}`", parse_mode="Markdown")
    else:
        bot.send_message(call.message.chat.id, "❌ Erro ao gerar o Pix. Tente novamente mais tarde.")

# Webhook principal
@app.route("/", methods=["POST"])
def receive_update():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "ok", 200

# Endpoint para testar se está ativo
@app.route("/", methods=["GET"])
def index():
    return "Bot está rodando!", 200

# Inicia localmente (opcional, para testes locais)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
