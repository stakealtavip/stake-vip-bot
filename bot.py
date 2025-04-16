import telebot
import requests
import os
import uuid

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

# AQUI estamos usando o token diretamente no código para teste
ACCESS_TOKEN_MP = "APP_USR-7951666709252852-041313-728c6a5375bb603a60aaefcc56a776c4-503811745"

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("📄 Plano Mensal - R$50", callback_data='plano_50'),
        telebot.types.InlineKeyboardButton("💎 Plano Anual - R$300", callback_data='plano_300')
    )
    texto = (
        "✨👑 BEM-VINDO AO STAKE ALTA VIP 👑✨\n\n"
        "Escolha seu plano abaixo para gerar o Pix e garantir seu acesso VIP."
    )
    bot.send_message(message.chat.id, texto, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == 'plano_50':
        valor = 5000
        desc = "Plano Mensal"
    elif call.data == 'plano_300':
        valor = 30000
        desc = "Plano Anual"
    else:
        return

    bot.send_message(call.message.chat.id, "⏳ Gerando código Pix...")

    try:
        url = "https://api.mercadopago.com/v1/payments"
        headers = {
            "Authorization": f"Bearer {ACCESS_TOKEN_MP}",
            "Content-Type": "application/json"
        }
        payload = {
            "transaction_amount": valor / 100,
            "description": desc,
            "payment_method_id": "pix",
            "payer": {
                "email": f"{call.from_user.id}@teste.com"
            }
        }

        response = requests.post(url, json=payload, headers=headers)
        data = response.json()

        if "point_of_interaction" in data:
            qr_code = data["point_of_interaction"]["transaction_data"]["qr_code"]
            qr_img = data["point_of_interaction"]["transaction_data"]["qr_code_base64"]

            bot.send_message(call.message.chat.id, f"📄 Escaneie ou copie:\n`{qr_code}`", parse_mode="Markdown")
            bot.send_message(call.message.chat.id, "⏱ Estamos monitorando seu pagamento. O código expira em 5 minutos.")
        else:
            bot.send_message(call.message.chat.id, "❌ Erro ao gerar o Pix. Tente novamente mais tarde.")

    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Erro ao gerar o Pix: {str(e)}")

if __name__ == '__main__':
    bot.polling(none_stop=True)
