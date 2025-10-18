import telebot
import json
from telebot import types
import sqlite3
from config import TOKEN, DEPARTMENT_PROGRAMMERS, DEPARTMENT_SALES, ADMIN_IDS

bot = telebot.TeleBot(TOKEN)

# --- Работа с базой support.db ---
DB_NAME = 'support.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS support_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            message TEXT,
            department TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def add_request(user_id, username, message, department):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO support_requests (user_id, username, message, department)
        VALUES (?, ?, ?, ?)
    """, (user_id, username, message, department))
    conn.commit()
    conn.close()

init_db()

# --- Хранилище ID сообщений бота ---
chat_messages = {}
user_pending_requests = {}  # хранит, если пользователь вводит запрос

def add_bot_message(chat_id, message_id):
    if chat_id not in chat_messages:
        chat_messages[chat_id] = []
    chat_messages[chat_id].append(message_id)

# --- Загружаем FAQ ---
def load_faq():
    with open("faq.json", "r", encoding="utf-8") as f:
        return list(json.load(f).items())

# --- /start ---
@bot.message_handler(commands=["start", "help"])
def start(message):
    reply_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    reply_kb.add("ℹ️ О боте", "❓ Частые вопросы", "🛠 Техподдержка")
    if message.from_user.id in ADMIN_IDS:
        reply_kb.add("⚙️ Админ")
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

# --- Админская кнопка ---
@bot.message_handler(func=lambda m: m.text == "⚙️ Админ")
def admin_button(message):
    if message.from_user.id in ADMIN_IDS:
        # TODO: сюда впиши сообщение для админа
        bot.send_message(message.chat.id, "Здесь ваше сообщение для админа")

# --- Обработка inline-кнопок ---
@bot.callback_query_handler(func=lambda call: True)
def inline_handler(call):
    if call.data == "back":
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
        chat_messages[call.message.chat.id] = []
        user_pending_requests.pop(call.from_user.id, None)
        reply_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        reply_kb.add("ℹ️ О боте", "❓ Частые вопросы", "🛠 Техподдержка")
        if call.from_user.id in ADMIN_IDS:
            reply_kb.add("⚙️ Админ")
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
        department = "programmers" if call.data == "dept_prog" else "sales"
        msg = bot.send_message(call.message.chat.id, "📝 Впешите ваш запрос:")
        add_bot_message(call.message.chat.id, msg.message_id)
        user_pending_requests[call.from_user.id] = department

# --- Получение текста запроса ---
@bot.message_handler(func=lambda m: m.from_user.id in user_pending_requests)
def handle_user_request(message):
    department = user_pending_requests.pop(message.from_user.id)
    add_request(
        user_id=message.from_user.id,
        username=message.from_user.username or "",
        message=message.text,
        department=department
    )
    bot.send_message(message.chat.id, f"✅ Ваш запрос отправлен на обработку в отдел {department}")

bot.polling(none_stop=True)
