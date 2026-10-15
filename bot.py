import os
import telebot
from supabase import create_client

BOT_TOKEN = os.getenv('BOT_TOKEN')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

bot = telebot.TeleBot(BOT_TOKEN)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

user_data = {}

@bot.message_handler(commands=['start'])
def send_welcome(bot_message):
    bot.send_message(
        bot_message.chat.id, 
        "Привет! Я админ-бот твоего сайта по ноутбукам.\n"
        "Напиши /add, чтобы добавить новый ноутбук в каталог."
    )

@bot.message_handler(commands=['add'])
def add_laptop(message):
    msg = bot.send_message(message.chat.id, "Введи название и модель ноутбука (например: *Asus ROG Strix*):", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_title)

def process_title(message):
    user_data[message.chat.id] = {'title': message.text}
    msg = bot.send_message(message.chat.id, "Введи цену (например: *25000 грн*):", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_price)

def process_price(message):
    user_data[message.chat.id]['price'] = message.text
    msg = bot.send_message(message.chat.id, "Введи характеристики (процессор, видеокарта, ОЗУ):")
    bot.register_next_step_handler(msg, process_specs)

def process_specs(message):
    user_data[message.chat.id]['specs'] = message.text
    msg = bot.send_message(message.chat.id, "Отправь фото ноутбука:")
    bot.register_next_step_handler(msg, process_photo)

def process_photo(message):
    if not message.photo:
        msg = bot.send_message(message.chat.id, "Пожалуйста, отправь именно фото! Попробуй еще раз:")
        bot.register_next_step_handler(msg, process_photo)
        return

    file_id = message.photo[-1].file_id
    file_info = bot.get_file(file_id)
    photo_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
    
    user_data[message.chat.id]['photo_url'] = photo_url
    user_data[message.chat.id]['status'] = 'В наличии'

    data = user_data[message.chat.id]
    try:
        supabase.table('laptops').insert(data).execute()
        bot.send_message(message.chat.id, "✅ Ноутбук успешно добавлен и уже появился на сайте!")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка при сохранении в базу: {e}")

bot.infinity_polling()