import os
import re
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import telebot
from supabase import create_client, Client

# Фейковый HTTP-сервер для Render (чтобы веб-сервис не засыпал)
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
    server.serve_forever()

threading.Thread(target=run_http_server, daemon=True).start()

# Инициализация
BOT_TOKEN = os.environ.get("BOT_TOKEN")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

bot = telebot.TeleBot(BOT_TOKEN)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, 
        "Привет! Я умный бот KyivLaptop.\n\n"
        "Команды:\n"
        "📋 /laptops — посмотреть список\n"
        "➕ /add [текст] — добавить ноутбук (я сам распаршу цену и характеристики)"
    )

@bot.message_handler(commands=['laptops'])
def list_laptops(message):
    try:
        response = supabase.table('laptops').select('*').execute()
        laptops = response.data
        if not laptops:
            bot.reply_to(message, "В базе пока нет ноутбуков.")
            return
        
        text = "📋 **Каталог ноутбуков:**\n\n"
        for item in laptops:
            text += f"▪️ **{item.get('title', 'Без названия')}**\n"
            text += f"💰 Цена: {item.get('price', 0)} грн\n"
            if item.get('specs'):
                text += f"⚙️ Характеристики: {item.get('specs')}\n"
            text += f"📌 Статус: {item.get('status', 'В наличии')}\n\n"
        bot.reply_to(message, text, parse_mode='Markdown')
    except Exception as e:
        print(f"Ошибка Supabase: {e}")
        bot.reply_to(message, "Ошибка при получении данных из базы.")

@bot.message_handler(commands=['add'])
def add_laptop_smart(message):
    # Убираем саму команду '/add ' из текста
    raw_text = message.text.replace('/add', '', 1).strip()
    
    if not raw_text:
        bot.reply_to(message, 
            "⚠️ Напиши текст после команды.\n"
            "Пример:\n`/add Acer Predator Helios 700 i7-9750h rtx 2080 16gb 512ssd 35000 грн`", 
            parse_mode='Markdown'
        )
        return

    try:
        # 1. Умный поиск цены (ищем числа перед грн, $, eur или просто крупные числа в конце)
        price_match = re.search(r'(\d+[\d\s]*)\s*(грн|грн\.|uah|\$|usd|€)', raw_text, re.IGNORECASE)
        price = "0"
        if price_match:
            price_str = price_match.group(1).replace(" ", "")
            price = price_str
            # Удаляем найденную цену из текста, чтобы она не дублировалась в названии
            raw_text = raw_text.replace(price_match.group(0), "").strip()
        else:
            # Если нет валюты, ищем последнее число в тексте
            numbers = re.findall(r'\b\d{3,6}\b', raw_text)
            if numbers:
                price = numbers[-1]
                raw_text = raw_text.replace(price, "").strip()

        # 2. Очистка и формирование названия и характеристик
        lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
        title = lines[0] if lines else "Ноутбук"
        
        # Если есть несколько строк, всё остальное уходит в характеристики
        specs = " | ".join(lines[1:]) if len(lines) > 1 else raw_text

        # 3. Сохранение в Supabase
        data = {
            "title": title,
            "price": price,
            "specs": specs,
            "status": "В наличии"
        }
        
        response = supabase.table('laptops').insert(data).execute()

        bot.reply_to(message, 
            f"✅ **Ноутбук успешно добавлен!**\n\n"
            f"📌 **Название:** {title}\n"
            f"💰 **Цена:** {price} грн\n"
            f"⚙️ **Характеристики:** {specs}\n"
            f"📊 **Статус:** В наличии", 
            parse_mode='Markdown'
        )
    except Exception as e:
        print(f"Ошибка добавления: {e}")
        bot.reply_to(message, f"❌ Ошибка при добавлении в базу: {e}")

print("Бот запущен и готов к работе...")
bot.infinity_polling(skip_pending=True)
