import telebot
import requests
import uuid
import base64
import io
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
import datetime

# Carrega variáveis do .env
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ACCESS_TOKEN_MP = os.getenv("ACCESS_TOKEN_MP")

if not TELEGRAM_TOKEN or not ACCESS_TOKEN_MP:
    raise Exception("Erro: TELEGRAM_TOKEN ou ACCESS_TOKEN_MP não encontrados no .env.")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

CANAL_VIP = "@stakealtavip"  # Canal VIP que receberá os usuários

# Boas-vindas automáticas para novos membros no grupo
@bot.message_handler(content_types=['new_chat_members'])
def boas_vindas_grupo(message):
    texto_boas_vindas = (
        "Membros novos, sejam bem-vindos ao nosso Grupo de Apostas Profissionais! 🎯\n\n"
        "Aqui você terá acesso a entradas selecionadas com base em análise técnica, gestão de banca responsável e suporte diário. Nosso foco é lucro constante a longo prazo, com disciplina e estratégia.\n\n"
        "📊 O que você encontrará aqui:\n\n"
        "✅ Sinais diários com odds reais e verificadas\n"
        "✅ Análises dos slots e jogos ao vivos que estão pagando\n"
        "✅ Gestão de banca recomendada\n"
        "✅ Resultados transparentes\n"
        "✅ Suporte para dúvidas e orientações\n\n"
        "🚨 Importante: Aposte com responsabilidade. Nosso grupo é voltado para pessoas que entendem que apostas esportivas exigem paciência, controle emocional e visão de longo prazo. Não prometemos ganhos fáceis — entregamos estratégia e consistência."
    )
    bot.send_message(message.chat.id, texto_boas_vindas)

# Geração de pagamento Pix via Mercado Pago
def gerar_pix_mp(valor, descricao):
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
        "payer": {"email": "comprador@email.com"}
    }

    response = requests.post(url, json=payload, headers=headers)
    dados = response.json()

    if "point_of_interaction" in dados:
        transacao = dados["point_of_interaction"]["transaction_data"]
        return transacao["qr_code_base64"], transacao["qr_code"], transacao.get("ticket_url", "")
    return None, None, None

# Comando /start
@bot.message_handler(commands=['start'])
def start(message):
    texto = (
        "Stake Alta VIP\n\n"
        "O canal com as melhores entradas de apostas esportivas e slots.\n\n"
        "Escolha um plano para obter acesso ao grupo VIP."
    )

    teclado = InlineKeyboardMarkup()
    planos = [
        ("Mensal - R$50", "50_Mensal"),
        ("Vitalício - R$100", "100_Vitalicio")
    ]

    for texto_botao, callback_data in planos:
        teclado.add(InlineKeyboardButton(text=texto_botao, callback_data=callback_data))

    bot.send_message(message.chat.id, texto, parse_mode='Markdown', reply_markup=teclado)

# Lida com os botões de plano
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    data = call.data
    try:
        if data.startswith("conf_"):
            solicitar_comprovante(call)
        elif data.startswith("novo_"):
            partes = data[5:].split("_", 1)
            enviar_pix(call.message.chat.id, float(partes[0]), partes[1])
        else:
            partes = data.split("_", 1)
            enviar_pix(call.message.chat.id, float(partes[0]), partes[1])
    except Exception as e:
        bot.send_message(call.message.chat.id, f"Ocorreu um erro: {str(e)}")

# Envia o QR code e Pix copia e cola
def enviar_pix(chat_id, valor, descricao):
    qr_base64, copiaecola, ticket_url = gerar_pix_mp(valor, descricao)

    if copiaecola:
        bot.send_message(chat_id, f"Pix gerado com sucesso!\n\nCódigo copia e cola:\n`{copiaecola}`", parse_mode='Markdown')

        imagem_bytes = base64.b64decode(qr_base64)
        imagem = io.BytesIO(imagem_bytes)
        imagem.name = "qrcode.png"
        bot.send_photo(chat_id, imagem)

        teclado = InlineKeyboardMarkup()
        url_pagamento = ticket_url or f"https://pixbrasil.com.br/pix.html?payload={copiaecola}"
        teclado.add(InlineKeyboardButton("Pagar Pix", url=url_pagamento))
        teclado.add(InlineKeyboardButton("Já paguei", callback_data=f"conf_{valor}_{descricao}"))
        teclado.add(InlineKeyboardButton("Gerar novo Pix", callback_data=f"novo_{valor}_{descricao}"))

        bot.send_message(chat_id, "Este código é válido por 5 minutos.\nSe expirar, clique em Gerar novo Pix.", parse_mode='Markdown', reply_markup=teclado)
    else:
        bot.send_message(chat_id, "Erro ao gerar Pix. Tente novamente.")

# Solicita envio de comprovante
def solicitar_comprovante(call):
    bot.send_message(call.message.chat.id, "Envie uma foto ou arquivo do comprovante de pagamento:", parse_mode='Markdown')
    bot.register_next_step_handler(call.message, handle_comprovante_pagamento)

# Trata o comprovante enviado
def handle_comprovante_pagamento(message):
    if message.content_type in ['photo', 'document']:
        bot.send_message(message.chat.id, "Comprovante recebido! Verificando pagamento...")
        liberar_acesso(message.chat.id)
    else:
        bot.send_message(message.chat.id, "Por favor, envie o comprovante como imagem ou arquivo.", parse_mode='Markdown')

# Libera acesso ao canal VIP com link único
def liberar_acesso(chat_id):
    try:
        link = bot.create_chat_invite_link(
            chat_id=CANAL_VIP,
            member_limit=1,
            expire_date=int(datetime.datetime.now().timestamp()) + 600
        )
        markup = InlineKeyboardMarkup().add(
            InlineKeyboardButton("Acessar Canal VIP", url=link.invite_link)
        )

        bot.send_message(chat_id, "Pagamento confirmado! Clique abaixo para entrar no canal VIP:", reply_markup=markup)

    except Exception as e:
        bot.send_message(chat_id, f"Erro ao gerar link: {str(e)}")

# Inicia o bot
print("Bot está rodando...")
bot.infinity_polling()
