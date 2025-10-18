import telebot
import json
from telebot import types
from db import init_db, add_request
from config import TOKEN, DEPARTMENT_PROGRAMMERS, DEPARTMENT_SALES

bot = telebot.TeleBot(TOKEN)
init_db()

# Загружаем FAQ из файла
def load_faq():
    with open("faq.json", "r", encoding="utf-8") as f:
        return list(json.load(f).items())  # список (вопрос, ответ)

# --- /start ---
@bot.message_handler(commands=["start", "help"])
def start(message):
    reply_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    reply_kb.add("ℹ️ О боте", "❓ Частые вопросы", "🛠 Техподдержка")
    bot.send_message(message.chat.id, "Добро пожаловать! Выберите действие ниже:", reply_markup=reply_kb)

# --- О боте ---
@bot.message_handler(func=lambda m: m.text == "ℹ️ О боте")
def about(message):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="back"))
    bot.send_message(message.chat.id, "Привет, меня зовут Jarvis — я бот помощник для упрощения жизни пользователей.", reply_markup=kb)

# --- Частые вопросы ---
@bot.message_handler(func=lambda m: m.text == "❓ Частые вопросы")
def faq_menu(message):
    kb = types.InlineKeyboardMarkup(row_width=1)
    faq_list = load_faq()
    for index, (question, _) in enumerate(faq_list):
        kb.add(types.InlineKeyboardButton(question[:60], callback_data=f"faq_{index}"))
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="back"))
    bot.send_message(message.chat.id, "Выберите вопрос:", reply_markup=kb)

# --- Техподдержка ---
@bot.message_handler(func=lambda m: m.text == "🛠 Техподдержка")
def tech_menu(message):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Программисты", callback_data="dept_prog"),
           types.InlineKeyboardButton("Отдел продаж", callback_data="dept_sales"))
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="back"))
    bot.send_message(message.chat.id, "К какому отделу вы бы хотели обратиться?", reply_markup=kb)

# --- Callback для inline-кнопок ---
@bot.callback_query_handler(func=lambda call: True)
def inline_handler(call):
    if call.data == "back":
        reply_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        reply_kb.add("ℹ️ О боте", "❓ Частые вопросы", "🛠 Техподдержка")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "Выберите действие ниже:", reply_markup=reply_kb)
    elif call.data.startswith("faq_"):
        index = int(call.data.split("_")[1])
        faq_list = load_faq()
        if index < len(faq_list):
            question, answer = faq_list[index]
            bot.send_message(call.message.chat.id, f"💬 *{question}*\n\n{answer}", parse_mode="Markdown")
    elif call.data in ["dept_prog", "dept_sales"]:
        bot.answer_callback_query(call.id, "Coming soon")

bot.polling(none_stop=True)