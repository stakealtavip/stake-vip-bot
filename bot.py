import telebot
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def boas_vindas(message):
    markup = InlineKeyboardMarkup()
    botao1 = InlineKeyboardButton("✅ Já paguei", callback_data="paguei")
    botao2 = InlineKeyboardButton("📲 Gerar outro Pix", callback_data="gerar_pix")
    markup.add(botao1, botao2)
    bot.send_message(message.chat.id, "👋 Seja bem-vindo!

Escolha uma opção abaixo:", reply_markup=markup)

@bot.message_handler(commands=['id'])
def pegar_id(message):
    bot.send_message(message.chat.id, f"🆔 ID deste grupo: `{message.chat.id}`", parse_mode="Markdown")

@bot.message_handler(content_types=['document', 'photo'])
def verificar_comprovante(message):
    bot.reply_to(message, "⏳ Verificando comprovante...")
    try:
        chat_id = message.chat.id
        bot.send_message(chat_id, "✅ Pagamento confirmado!
Em breve você será adicionado ao grupo VIP.")
        bot.send_message(ADMIN_ID, f"📥 Novo pagamento recebido de @{message.from_user.username or message.from_user.first_name}.
Verifique o comprovante.")
    except Exception as e:
        bot.send_message(chat_id, f"❌ Erro ao processar comprovante: {e}")

if __name__ == "__main__":
    print("🤖 Bot rodando... Aguardando comandos.")
    bot.infinity_polling()
