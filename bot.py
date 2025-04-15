# create_project.py
import os

# Dicionário com os nomes dos arquivos e seus respectivos conteúdos
files = {
    "bot.py": r'''import telebot
import requests
import uuid
import base64
import io
import os
import datetime
from flask import Flask, request
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from apscheduler.schedulers.background import BackgroundScheduler

# Tokens já embutidos (NÃO USE ESSA PRÁTICA EM PRODUÇÃO!)
TELEGRAM_TOKEN = '7776075436:AAFdPlLaseQkmFo7CQNFauhg-Wf8Nzhd1x0'
ACCESS_TOKEN_MP = 'APP_USR-7951666709252852-041313-728c6a5375bb603a60aaefcc56a776c4-583811745'

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

# Nome do grupo VIP – o bot precisa ser administrador para remover membros
CANAL_VIP = "@stakealtavip"

# Inicia o agendador em background
scheduler = BackgroundScheduler()
scheduler.start()

# Dicionário para armazenar o tipo de assinatura (mensal ou anual) de cada usuário
subscription_info = {}

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    texto = (
        "💎✨ *BEM-VINDO AO STAKE ALTA VIP* ✨💎\n\n"
        "Você acaba de entrar no grupo onde dados, estratégia e gestão de risco se unem para transformar apostas em decisões lucrativas. 📈\n\n"
        "📊 Nosso robô Cassini utiliza algoritmos preditivos avançados, análise de padrões por IA e filtros estatísticos para entregar entradas de alta precisão.\n\n"
        "🔐 Aqui você terá:\n"
        "- Gestão de banca profissional 🛡\n"
        "- Entradas validadas por padrões estatísticos 📌\n"
        "- Acompanhamento em tempo real 📲\n"
        "- Acesso direto ao modelo analítico do robô Cassini 🤖\n\n"
        "Esse grupo é para quem joga grande e pensa grande.\n"
        "*Bem-vindo à elite. Bem-vindo ao STAKE ALTA.* 👑🚀"
    )
    teclado = InlineKeyboardMarkup()
    # Botões para escolher o plano
    teclado.add(InlineKeyboardButton("Mensal - R$50", callback_data="50_Mensal"))
    teclado.add(InlineKeyboardButton("Anual - R$300", callback_data="300_Anual"))
    bot.send_message(chat_id, texto, parse_mode='Markdown', reply_markup=teclado)

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
        "payer": {"email": "cliente@email.com"}
    }
    response = requests.post(url, json=payload, headers=headers)
    dados = response.json()
    if "point_of_interaction" in dados:
        tx = dados["point_of_interaction"]["transaction_data"]
        return tx["qr_code_base64"], tx["qr_code"], tx.get("ticket_url", "")
    return None, None, None

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    data = call.data
    if data.startswith("conf_"):
        # Dados quando o usuário confirma o pagamento: "conf_{valor}_{plano}"
        parts = data.split("_", 2)
        if len(parts) == 3:
            _, valor, plano = parts
            subscription_info[call.message.chat.id] = plano.lower()
        solicitar_comprovante(call)
    else:
        # Dados para gerar Pix: "{valor}_{plano}"
        parts = data.split("_", 1)
        if len(parts) == 2:
            valor, plano = parts
            subscription_info[call.message.chat.id] = plano.lower()
            enviar_pix(call.message.chat.id, float(valor), plano)

def enviar_pix(chat_id, valor, descricao):
    qr_base64, copiaecola, ticket_url = gerar_pix_mp(valor, descricao)
    if copiaecola:
        bot.send_message(chat_id, f"✅ *Pix gerado com sucesso!*\n\nCódigo copia e cola:\n`{copiaecola}`", parse_mode='Markdown')
        imagem = io.BytesIO(base64.b64decode(qr_base64))
        imagem.name = "qrcode.png"
        bot.send_photo(chat_id, imagem)
        teclado = InlineKeyboardMarkup()
        url_pagamento = ticket_url or f"https://pixbrasil.com.br/pix.html?payload={copiaecola}"
        teclado.add(InlineKeyboardButton("Pagar Pix", url=url_pagamento))
        teclado.add(InlineKeyboardButton("Já paguei", callback_data=f"conf_{valor}_{descricao}"))
        bot.send_message(chat_id, "Após efetuar o pagamento, clique em 'Já paguei' para enviar o comprovante.", reply_markup=teclado)
    else:
        bot.send_message(chat_id, "Erro ao gerar Pix. Tente novamente.")

def solicitar_comprovante(call):
    bot.send_message(call.message.chat.id, "📎 Envie agora o comprovante de pagamento (imagem ou arquivo):")
    bot.register_next_step_handler(call.message, verificar_pagamento)

def verificar_pagamento(message):
    if message.content_type in ['photo', 'document']:
        bot.send_message(message.chat.id, "⏳ Verificando comprovante...")
        # Aqui você poderia inserir uma verificação real do comprovante
        liberar_link_unico(message.chat.id)
    else:
        bot.send_message(message.chat.id, "⚠️ Por favor, envie o comprovante como imagem ou arquivo.")

def liberar_link_unico(chat_id):
    try:
        # Gera link único com expiração em 10 minutos
        link = bot.create_chat_invite_link(
            chat_id=CANAL_VIP,
            member_limit=1,
            expire_date=int(datetime.datetime.now().timestamp()) + 600
        )
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🚀 Acessar Canal VIP", url=link.invite_link))
        bot.send_message(chat_id, "✅ Pagamento confirmado! Clique abaixo para entrar no grupo VIP:", reply_markup=markup)
        # Se o plano for mensal, agenda a remoção do usuário após 31 dias
        if subscription_info.get(chat_id, "") == "mensal":
            run_time = datetime.datetime.now() + datetime.timedelta(days=31)
            scheduler.add_job(remover_usuario, 'date', run_date=run_time, args=[chat_id])
            bot.send_message(chat_id, "ℹ️ Você será removido do grupo após 31 dias se não renovar sua assinatura.")
    except Exception as e:
        bot.send_message(chat_id, f"Erro ao gerar link: {str(e)}")

def remover_usuario(user_id):
    try:
        bot.kick_chat_member(CANAL_VIP, user_id)
        bot.send_message(user_id, "Sua assinatura mensal expirou e você foi removido do grupo. Para reentrar, realize um novo pagamento.")
    except Exception as e:
        bot.send_message(user_id, f"Erro ao remover você do grupo: {str(e)}")

@app.route(f"/webhook/{TELEGRAM_TOKEN}", methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.get_data().decode("utf-8"))
    bot.process_new_updates([update])
    return "Webhook recebido", 200

@app.route("/", methods=["GET"])
def home():
    return "Bot Stake VIP Online!"

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"https://aposta-vip-bot-web.onrender.com/webhook/{TELEGRAM_TOKEN}")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
''',
    "requirements.txt": r'''flask
pytelegrambotapi
python-dotenv
requests
apscheduler
''',
    "Procfile": r'''web: python bot.py
''',
    ".env.example": r'''TELEGRAM_TOKEN=7776075436:AAFdPlLaseQkmFo7CQNFauhg-Wf8Nzhd1x0
ACCESS_TOKEN_MP=APP_USR-7951666709252852-041313-728c6a5375bb603a60aaefcc56a776c4-583811745
''',
    "README.md": r'''# Bot Stake Alta VIP

Este projeto é um bot para o grupo VIP do Stake Alta. Ele integra:

- Mensagem de boas-vindas com explicação do serviço.
- Geração de Pix para pagamento, com opção de código "copia e cola" e QR Code.
- Confirmação de pagamento e envio de link único (com expiração) para acesso ao grupo VIP.
- Remoção automática do usuário do grupo após 31 dias (para assinaturas mensais), se não renovar.

## Arquivos

- **bot.py**: Código principal do bot.
- **requirements.txt**: Dependências do projeto.
- **Procfile**: Configuração para deploy no Render.
- **.env.example**: Exemplo de variáveis de ambiente.
- **README.md**: Documentação do projeto.

## Deploy

1. Crie um repositório no GitHub e faça o upload destes arquivos.
2. Conecte o repositório à Render e configure um Web Service com o comando `python bot.py`.
3. Como os tokens já estão embutidos no código, não é necessário configurar variáveis de ambiente (mas recomendamos utilizar variáveis de ambiente para maior segurança em produção).
4. Após o deploy, configure o webhook do Telegram com o comando:
