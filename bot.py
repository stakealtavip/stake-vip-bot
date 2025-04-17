import telebot
import requests
import uuid
import base64
import io
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
ACCESS_TOKEN_MP = os.getenv("ACCESS_TOKEN_MP")
CANAL_VIP = "@stakealtavip"  # Nome de usuário do canal (ou use ID)

bot = telebot.TeleBot(TOKEN)

# 📌 Função para gerar pagamento Pix via Mercado Pago
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
        "payer": {"email": "cliente@exemplo.com"}
    }
    response = requests.post(url, json=payload, headers=headers)
    dados = response.json()
    if "point_of_interaction" in dados:
        transacao = dados["point_of_interaction"]["transaction_data"]
        return transacao["qr_code_base64"], transacao["qr_code"], transacao.get("ticket_url", "")
    return None, None, None

# 🔥 Mensagem inicial + planos
@bot.message_handler(commands=['start'])
def boas_vindas(message):
    texto = (
        "👋 *Membros novos, sejam bem-vindos ao nosso Grupo de Apostas Profissionais!*\n\n"
        "📈 Aqui você terá acesso a entradas *selecionadas com base em análise técnica*, "
        "gestão de banca responsável e suporte diário.\n\n"
        "💡 Nosso foco é *lucro constante a longo prazo*, com disciplina e estratégia.\n\n"
        "📊 O que você encontrará aqui:\n"
        "✅ Sinais diários com odds reais e verificadas\n"
        "✅ Análises dos slots e jogos ao vivo que estão pagando\n"
        "✅ Gestão de banca recomendada\n"
        "✅ Resultados transparentes\n"
        "✅ Suporte para dúvidas e orientações\n\n"
        "🚨 *Aposte com responsabilidade!*"
    )

    texto_gvips = (
        "\n\n💎✨ *MENSAGEM PARA OS GVIPS* ✨💎\n\n"
        "Senhores, sejam bem-vindos ao GVIPS — onde o jogo é de alto nível e os resultados "
        "falam mais alto que promessas.\n\n"
        "🎯 Vocês fazem parte de uma elite:\n"
        "🔒 Entradas exclusivas\n"
        "📊 Análises cirúrgicas\n"
        "🛡 Gestão de risco profissional\n"
        "🔥 Oportunidades únicas\n\n"
        "👑 *CLUUBE DA STAKE ALTA GVIPS* — Aqui, lucro é estilo de vida.\n"
    )

    teclado = InlineKeyboardMarkup()
    teclado.add(InlineKeyboardButton("📆 Plano Mensal - R$50", callback_data="50_Mensal"))
    teclado.add(InlineKeyboardButton("♾️ Vitalício - R$100", callback_data="100_Vitalicio"))

    bot.send_message(message.chat.id, texto, parse_mode='Markdown')
    bot.send_message(message.chat.id, texto_gvips, parse_mode='Markdown')
    bot.send_message(message.chat.id, "👇 *Escolha seu plano e gere seu Pix automático:*", parse_mode='Markdown', reply_markup=teclado)

# 🔁 Resposta aos botões
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    data = call.data
    if data.startswith("conf_"):
        solicitar_comprovante(call)
    elif data.startswith("novo_"):
        partes = data[5:].split("_", 1)
        enviar_pix(call.message.chat.id, float(partes[0]), partes[1])
    else:
        partes = data.split("_", 1)
        enviar_pix(call.message.chat.id, float(partes[0]), partes[1])

# 💰 Geração de QR + botão Pix
def enviar_pix(chat_id, valor, descricao):
    qr_base64, copiaecola, ticket_url = gerar_pix_mp(valor, descricao)
    if copiaecola:
        bot.send_message(chat_id, f"✅ *Pix gerado com sucesso!*\n\n💸 *Copia e cola:*\n`{copiaecola}`", parse_mode='Markdown')
        imagem_bytes = base64.b64decode(qr_base64)
        imagem = io.BytesIO(imagem_bytes)
        imagem.name = "qrcode.png"
        bot.send_photo(chat_id, imagem)

        teclado = InlineKeyboardMarkup()
        url_pagamento = ticket_url or f"https://pixbrasil.com.br/pix.html?payload={copiaecola}"
        teclado.add(InlineKeyboardButton("💳 Pagar Pix", url=url_pagamento))
        teclado.add(InlineKeyboardButton("✅ Já paguei", callback_data=f"conf_{valor}_{descricao}"))
        teclado.add(InlineKeyboardButton("🔁 Gerar novo Pix", callback_data=f"novo_{valor}_{descricao}"))

        bot.send_message(chat_id, "⏱ Este Pix expira em 5 minutos. Clique abaixo se precisar gerar novamente:", reply_markup=teclado)
    else:
        bot.send_message(chat_id, "❌ Erro ao gerar Pix. Tente novamente.")

# 📷 Receber comprovante
def solicitar_comprovante(call):
    bot.send_message(call.message.chat.id, "📤 Envie a foto do seu comprovante para liberar o acesso:")
    bot.register_next_step_handler(call.message, handle_comprovante_pagamento)

# 🔐 Verificação do comprovante (simulação) + gerar link
def handle_comprovante_pagamento(message):
    if message.content_type in ['photo', 'document']:
        bot.send_message(message.chat.id, "✅ Comprovante recebido! Verificando pagamento...")
        liberar_acesso(message.chat.id)
    else:
        bot.send_message(message.chat.id, "⚠️ Envie o comprovante como imagem ou arquivo.")

# 🎟 Link único de acesso
def liberar_acesso(chat_id):
    try:
        link = bot.create_chat_invite_link(chat_id=CANAL_VIP, member_limit=1)
        bot.send_message(
            chat_id,
            "🎉 Pagamento confirmado! Acesse agora o canal VIP:",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🚪 Entrar no VIP", url=link.invite_link)
            )
        )
    except Exception as e:
        bot.send_message(chat_id, f"❌ Erro ao gerar link: {str(e)}")

# ▶️ Iniciar bot
print("Bot está rodando...")
bot.infinity_polling()
