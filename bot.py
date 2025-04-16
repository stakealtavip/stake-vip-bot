import telebot
import requests
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ACCESS_TOKEN_MP = os.getenv("ACCESS_TOKEN_MP")
ADMIN_ID = os.getenv("ADMIN_ID")

bot = telebot.TeleBot(BOT_TOKEN)

# Função para gerar QR Code do Pix
def gerar_pix(valor, descricao):
    url = "https://api.mercadopago.com/v1/payments"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN_MP}",
        "Content-Type": "application/json"
    }
    payload = {
        "transaction_amount": float(valor),
        "description": descricao,
        "payment_method_id": "pix",
        "payer": {
            "email": "comprador@gmail.com",
            "first_name": "Comprador",
            "last_name": "Bot"
        }
    }

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 201:
        data = response.json()
        return {
            "copiaecola": data["point_of_interaction"]["transaction_data"]["qr_code"],
            "qr_code_base64": data["point_of_interaction"]["transaction_data"]["qr_code_base64"],
            "payment_id": data["id"]
        }
    else:
        print("Erro ao gerar Pix:", response.text)
        return None

# Mensagem de boas-vindas com botões de plano
@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.InlineKeyboardMarkup()
    mensal_btn = telebot.types.InlineKeyboardButton("💳 Plano Mensal - R$50", callback_data="plano_mensal")
    anual_btn = telebot.types.InlineKeyboardButton("💎 Plano Anual - R$300", callback_data="plano_anual")
    markup.add(mensal_btn, anual_btn)

    texto = (
        "✨👑 BEM-VINDO AO STAKE ALTA VIP 👑✨\n\n"
        "Escolha seu plano abaixo para gerar o Pix e garantir seu acesso VIP."
    )
    bot.send_message(message.chat.id, texto, reply_markup=markup)

# Geração do Pix ao clicar nos botões
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "plano_mensal":
        plano = "Plano Mensal"
        valor = 50
    elif call.data == "plano_anual":
        plano = "Plano Anual"
        valor = 300
    else:
        return

    bot.answer_callback_query(call.id, "Gerando seu Pix...")
    pagamento = gerar_pix(valor, plano)

    if pagamento:
        mensagem = (
            f"📲 Escaneie o QR Code abaixo ou copie e cole para pagar via Pix:\n\n"
            f"`{pagamento['copiaecola']}`\n\n"
            f"Estamos monitorando seu pagamento. O código expira em 5 minutos."
        )
        bot.send_photo(
            call.message.chat.id,
            photo=f"data:image/png;base64,{pagamento['qr_code_base64']}",
            caption=mensagem,
            parse_mode="Markdown"
        )
    else:
        bot.send_message(call.message.chat.id, "❌ Erro ao gerar o Pix. Tente novamente mais tarde.")

# Comando /id para pegar ID do grupo ou usuário
@bot.message_handler(commands=['id'])
def pegar_id(message):
    bot.reply_to(message, f"Este chat ID é: `{message.chat.id}`", parse_mode="Markdown")

# Inicializar o bot
if __name__ == '__main__':
    print("Bot rodando...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
