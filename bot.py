import telebot
from telebot import types
import uuid
import base64
import requests
import io
import os
from dotenv import load_dotenv
import datetime

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
MERCADO_PAGO_TOKEN = os.getenv("ACCESS_TOKEN_MP")
CANAL_USERNAME = "stakealtavip"  # Nome de usuário do canal (sem @)

bot = telebot.TeleBot(TOKEN)

def gerar_link_convite_temporario(chat_id):
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{TOKEN}/createChatInviteLink",
            json={
                "chat_id": f"@{CANAL_USERNAME}",
                "expire_date": int(datetime.datetime.now().timestamp()) + 300,
                "member_limit": 1
            }
        )
        data = response.json()
        if data.get("ok"):
            return data["result"]["invite_link"]
        else:
            print("Erro ao gerar link:", data)
            return None
    except Exception as e:
        print("Exceção ao gerar link:", e)
        return None

def gerar_pix_mp(valor, descricao):
    url = 'https://api.mercadopago.com/v1/payments'
    headers = {
        'Authorization': f'Bearer {MERCADO_PAGO_TOKEN}',
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

@bot.message_handler(commands=["start"])
def start(message):
    texto_boasvindas = (
        "🎯 Membros novos, sejam bem-vindos ao nosso *Grupo de Apostas Profissionais*!\n\n"
        "📊 O que você encontrará aqui:\n"
        "✅ *Sinais diários* com odds reais\n"
        "✅ *Análises* dos slots e jogos ao vivo\n"
        "✅ *Gestão de banca* recomendada\n"
        "✅ *Resultados* transparentes\n"
        "✅ *Suporte* para dúvidas\n\n"
        "🚨 *Aposte com responsabilidade.* Nosso foco é *lucro constante com disciplina.*\n\n"
        "💎✨ *MENSAGEM PARA OS GVIPS* ✨💎\n\n"
        "Senhores, sejam bem-vindos ao *GVIPS*, o grupo onde *o jogo é de alto nível*.\n"
        "📈 Aqui lidamos com estratégia, não com sorte.\n\n"
        "🏆 Vocês fazem parte da elite: investidores e empreendedores que sabem o que querem.\n\n"
        "🔒 Entradas exclusivas\n📊 Análises cirúrgicas\n🛡 Gestão de risco\n🔥 Oportunidades únicas\n\n"
        "Preparem-se para uma nova era de lucros! 💰"
    )

    bot.send_message(message.chat.id, texto_boasvindas, parse_mode="Markdown")

    teclado = types.InlineKeyboardMarkup()
    teclado.add(
        types.InlineKeyboardButton("💸 Mensal - R$50", callback_data="50_Mensal"),
        types.InlineKeyboardButton("💎 Vitalício - R$100", callback_data="100_Vitalicio")
    )
    bot.send_message(message.chat.id, "Escolha um plano para gerar o Pix:", reply_markup=teclado)

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

def enviar_pix(chat_id, valor, descricao):
    qr_base64, copiaecola, ticket_url = gerar_pix_mp(valor, descricao)
    if copiaecola:
        bot.send_message(chat_id, f"🔐 *Pix gerado com sucesso!*\n\n🔢 Código copia e cola:\n`{copiaecola}`", parse_mode='Markdown')
        imagem_bytes = base64.b64decode(qr_base64)
        imagem = io.BytesIO(imagem_bytes)
        imagem.name = "qrcode.png"
        bot.send_photo(chat_id, imagem)

        teclado = types.InlineKeyboardMarkup()
        url_pagamento = ticket_url or f"https://pixbrasil.com.br/pix.html?payload={copiaecola}"
        teclado.add(types.InlineKeyboardButton("✅ Pagar Pix", url=url_pagamento))
        teclado.add(types.InlineKeyboardButton("📤 Já paguei", callback_data=f"conf_{valor}_{descricao}"))
        teclado.add(types.InlineKeyboardButton("🔁 Gerar novo Pix", callback_data=f"novo_{valor}_{descricao}"))

        bot.send_message(chat_id, "⏳ Este código é válido por 5 minutos. Se expirar, clique em *Gerar novo Pix*.", parse_mode='Markdown', reply_markup=teclado)
    else:
        bot.send_message(chat_id, "❌ Erro ao gerar Pix. Tente novamente.")

def solicitar_comprovante(call):
    bot.send_message(call.message.chat.id, "📎 Envie uma foto ou arquivo do comprovante de pagamento:", parse_mode='Markdown')
    bot.register_next_step_handler(call.message, handle_comprovante_pagamento)

@bot.message_handler(content_types=["photo", "document"])
def handle_comprovante_pagamento(message):
    if message.content_type in ["photo", "document"]:
        bot.send_message(message.chat.id, "Comprovante recebido! ✅ Verificando pagamento...")
        liberar_acesso(message.chat.id)
    else:
        bot.send_message(message.chat.id, "❌ Envie o comprovante como imagem ou arquivo.")

def liberar_acesso(chat_id):
    try:
        link = bot.create_chat_invite_link(chat_id=f"@{CANAL_USERNAME}", member_limit=1, expire_date=int(datetime.datetime.now().timestamp()) + 300)
        bot.send_message(chat_id, "🔓 Pagamento confirmado!\nClique abaixo para acessar o canal VIP:", reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🚪 Acessar Canal VIP", url=link.invite_link)))
    except Exception as e:
        bot.send_message(chat_id, f"❌ Erro ao gerar link: {str(e)}")

# Iniciar bot
print("Bot está rodando...")
bot.infinity_polling()
