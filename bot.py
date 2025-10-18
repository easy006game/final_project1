import telebot
import json
from telebot import types
from db import init_db, add_request
from config import TOKEN, DEPARTMENT_PROGRAMMERS, DEPARTMENT_SALES

bot = telebot.TeleBot(TOKEN)
init_db()

# Хранилище ID сообщений бота в чате
chat_messages = {}

def add_bot_message(chat_id, message_id):
    if chat_id not in chat_messages:
        chat_messages[chat_id] = []
    chat_messages[chat_id].append(message_id)

# Загружаем FAQ из файла
def load_faq():
    with open("faq.json", "r", encoding="utf-8") as f:
        return list(json.load(f).items())  # список (вопрос, ответ)

# --- /start ---
@bot.message_handler(commands=["start", "help"])
def start(message):
    reply_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    reply_kb.add("ℹ️ О боте", "❓ Частые вопросы", "🛠 Техподдержка")
    msg = bot.send_message(message.chat.id, "Добро пожаловать! Выберите действие ниже:", reply_markup=reply_kb)
    add_bot_message(message.chat.id, msg.message_id)

# --- О боте ---
@bot.message_handler(func=lambda m: m.text == "ℹ️ О боте")
def about(message):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="back"))
    msg = bot.send_message(message.chat.id, "Привет, меня зовут Jarvis — я бот помощник для упрощения жизни пользователей.", reply_markup=kb)
    add_bot_message(message.chat.id, msg.message_id)

# --- Частые вопросы ---
@bot.message_handler(func=lambda m: m.text == "❓ Частые вопросы")
def faq_menu(message):
    kb = types.InlineKeyboardMarkup(row_width=1)
    faq_list = load_faq()
    for index, (question, _) in enumerate(faq_list):
        kb.add(types.InlineKeyboardButton(question[:60], callback_data=f"faq_{index}"))
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="back"))
    msg = bot.send_message(message.chat.id, "Выберите вопрос:", reply_markup=kb)
    add_bot_message(message.chat.id, msg.message_id)

# --- Техподдержка ---
@bot.message_handler(func=lambda m: m.text == "🛠 Техподдержка")
def tech_menu(message):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Программисты", callback_data="dept_prog"),
           types.InlineKeyboardButton("Отдел продаж", callback_data="dept_sales"))
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="back"))
    msg = bot.send_message(message.chat.id, "К какому отделу вы бы хотели обратиться?", reply_markup=kb)
    add_bot_message(message.chat.id, msg.message_id)

# --- Callback для inline-кнопок ---
@bot.callback_query_handler(func=lambda call: True)
def inline_handler(call):
    if call.data == "back":
        # Удаляем все сообщения бота и пользователя кроме /start
        try:
            history = bot.get_chat(call.message.chat.id).get_history(limit=100)
        except:
            history = []
        for msg in history:
            try:
                if msg.text and msg.text.strip() == "/start":
                    continue
                bot.delete_message(call.message.chat.id, msg.message_id)
            except:
                pass

        # Очищаем внутренние ID сообщений
        chat_messages[call.message.chat.id] = []

        # Отправляем стартовое меню
        reply_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        reply_kb.add("ℹ️ О боте", "❓ Частые вопросы", "🛠 Техподдержка")
        msg = bot.send_message(call.message.chat.id, "Выберите действие ниже:", reply_markup=reply_kb)
        add_bot_message(call.message.chat.id, msg.message_id)

    elif call.data.startswith("faq_"):
        index = int(call.data.split("_")[1])
        faq_list = load_faq()
        if index < len(faq_list):
            question, answer = faq_list[index]
            msg = bot.send_message(call.message.chat.id, f"💬 *{question}*\n\n{answer}", parse_mode="Markdown")
            add_bot_message(call.message.chat.id, msg.message_id)

    elif call.data in ["dept_prog", "dept_sales"]:
        msg = bot.send_message(call.message.chat.id, "Coming soon")
        add_bot_message(call.message.chat.id, msg.message_id)

bot.polling(none_stop=True)