import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
import os

# Tokens de acesso
TOKEN = os.getenv("TELEGRAM_TOKEN")
CANAL_VIP = os.getenv("CANAL_VIP_ID")

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def boas_vindas(message):
    texto = """💎✨ MENSAGEM PARA OS GVIPS ✨💎

Senhores,

Sejam muito bem-vindos ao GVIPS, o grupo onde o jogo é de alto nível e os resultados falam mais alto que promessas. Aqui não lidamos com sorte — lidamos com estratégia, informação privilegiada e decisões inteligentes. 🧠📈

Vocês fazem parte de uma elite: investidores, empreendedores, milionários que sabem onde estão pisando. 🏆💼
E por isso, o tratamento aqui é diferente:
🔒 Entradas exclusivas
📊 Análises cirúrgicas
🛡 Gestão de risco profissional
🔥 Oportunidades únicas

Preparem-se para uma nova era de lucros.
O jogo mudou, e vocês estão no comando. 🎯👑
"""
    bot.send_message(message.chat.id, texto)

@bot.message_handler(content_types=['photo', 'document'])
def verificar_comprovante(message):
    if message.caption and "pix" in message.caption.lower():
        liberar_acesso(message.chat.id)
    else:
        bot.send_message(message.chat.id, "⚠️ Envie o comprovante como foto ou documento, com legenda 'pix', por favor.")

def liberar_acesso(chat_id):
    try:
        tempo = 60 * 5  # 5 minutos de validade
        link = bot.create_chat_invite_link(chat_id=CANAL_VIP, expire_date=int(datetime.now().timestamp()) + tempo, member_limit=1)
        
        teclado = InlineKeyboardMarkup()
        teclado.add(InlineKeyboardButton("🎯 Entrar no Grupo VIP", url=link.invite_link))
        
        bot.send_message(chat_id, "✅ Pagamento confirmado! Clique abaixo para acessar o canal VIP:", reply_markup=teclado)
    except Exception as e:
        bot.send_message(chat_id, f"❌ Erro ao gerar link de acesso: {e}")

if __name__ == "__main__":
    print("🤖 Bot está rodando... Aguardando comandos.")
    bot.infinity_polling()
