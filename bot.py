import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import telebot
from supabase import create_client, Client

# 1. Запуск фейкового HTTP-сервера для Render (чтобы проходила проверка порта)
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
    server.serve_forever()

# Запускаем HTTP-сервер в отдельном потоке
threading.Thread(target=run_http_server, daemon=True).start()

# 2. Инициализация бота и Supabase
BOT_TOKEN = os.environ.get("BOT_TOKEN")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

bot = telebot.TeleBot(BOT_TOKEN)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Я бот для управления каталогом KyivLaptop. Используй /laptops для просмотра списка.")

@bot.message_handler(commands=['laptops'])
def list_laptops(message):
    try:
        response = supabase.table('laptops').select('*').execute()
        laptops = response.data
        if not laptops:
            bot.reply_to(message, "В базе пока нет ноутбуков.")
            return
        
        text = "📋 **Список ноутбуков:**\n\n"
        for item in laptops:
            text += f"▪️ **{item.get('title', 'Без названия')}** — {item.get('price', 0)} грн\nСтатус: {item.get('status', 'N/A')}\n\n"
        bot.reply_to(message, text, parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"Ошибка при получении данных: {e}")

print("Бот запущен...")
bot.infinity_polling()
