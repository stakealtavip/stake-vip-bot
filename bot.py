import telebot
from telebot import types
from datetime import datetime, timedelta

# === CONFIGURAÇÕES ===
TOKEN = 'SEU_TOKEN_DO_BOT_AQUI'
CANAL_VIP = 'https://t.me/+2wtgut5HQ6czNzEx'  # link do canal VIP
CANAL_VIP_ID = '@seu_canal_vip'  # ou use ID numérico com -100...

bot = telebot.TeleBot(TOKEN)

# === COMANDO /START ===
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📩 Enviar Comprovante")
    bot.send_message(message.chat.id, """
💎✨ MENSAGEM PARA OS GVIPS ✨💎

Senhores,

Sejam muito bem-vindos ao GVIPS, o grupo onde o jogo é de alto nível e os resultados falam mais alto que promessas. Aqui não lidamos com sorte — lidamos com estratégia, informação privilegiada e decisões inteligentes. 🧠📈

Preparem-se para uma nova era de lucros.
O jogo mudou, e vocês estão no comando. 🎯👑
""", reply_markup=markup)

# === VERIFICAR COMPROVANTE (foto ou documento) ===
@bot.message_handler(content_types=['photo', 'document'])
def verificar_comprovante(message):
    try:
        bot.send_message(message.chat.id, "✅ Comprovante recebido! Gerando acesso...")
        liberar_acesso(message.chat.id)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Erro ao processar o comprovante: {e}")

# === LIBERAR ACESSO COM LINK TEMPORÁRIO ===
def liberar_acesso(chat_id):
    try:
        tempo_expiracao = datetime.now() + timedelta(minutes=5)
        link = bot.create_chat_invite_link(chat_id=CANAL_VIP_ID, expire_date=int(tempo_expiracao.timestamp()), member_limit=1)

        teclado = types.InlineKeyboardMarkup()
        botao = types.InlineKeyboardButton("🎟️ Entrar no Grupo VIP", url=link.invite_link)
        teclado.add(botao)

        bot.send_message(chat_id, "✅ Pagamento confirmado! Clique abaixo para acessar o canal VIP:", reply_markup=teclado)

    except Exception as e:
        bot.send_message(chat_id, f"❌ Erro ao gerar link de acesso: {e}")

# === INICIAR BOT ===
if __name__ == "__main__":
    print("🤖 Bot está rodando... Aguarde comandos.")
    bot.infinity_polling()
