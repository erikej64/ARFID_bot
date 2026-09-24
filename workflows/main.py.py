import os
import httpx
from fastapi import FastAPI, Request

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

app = FastAPI()

# Состояние пользователя храним в памяти: {chat_id: {"lang": "ru", "state": "main_menu", "answers": {}}}
users = {}

TEXTS = {
    "kz": {
        "choose_language": "Тілді таңдаңыз:",
        "main_menu_title": "🏠 Басты мәзір",
        "btn_test": "📝 Тестен өту",
        "btn_quest": "🌱 Food Quest",
        "btn_info": "📚 ARFID дегеніміз не?",
        "btn_help": "❤️ Көмек керек пе?",
        "coming_soon": "Бұл бөлім жақында қосылады 🙂",
    },
    "ru": {
        "choose_language": "Выберите язык:",
        "main_menu_title": "🏠 Главное меню",
        "btn_test": "📝 Пройти тест",
        "btn_quest": "🌱 Food Quest",
        "btn_info": "📚 Что такое ARFID?",
        "btn_help": "❤️ Нужна помощь?",
        "coming_soon": "Этот раздел скоро появится 🙂",
    },
    "en": {
        "choose_language": "Choose your language:",
        "main_menu_title": "🏠 Main menu",
        "btn_test": "📝 Take the test",
        "btn_quest": "🌱 Food Quest",
        "btn_info": "📚 What is ARFID?",
        "btn_help": "❤️ Need help?",
        "coming_soon": "This section is coming soon 🙂",
    },
}


async def send_message(chat_id: int, text: str, keyboard: list[list[dict]] | None = None):
    payload = {"chat_id": chat_id, "text": text}
    if keyboard:
        payload["reply_markup"] = {"inline_keyboard": keyboard}
    async with httpx.AsyncClient() as client:
        await client.post(f"{API_URL}/sendMessage", json=payload)


async def answer_callback(callback_query_id: str):
    async with httpx.AsyncClient() as client:
        await client.post(f"{API_URL}/answerCallbackQuery", json={"callback_query_id": callback_query_id})


def language_keyboard():
    return [[
        {"text": "🇰🇿 Қазақша", "callback_data": "lang_kz"},
        {"text": "🇷🇺 Русский", "callback_data": "lang_ru"},
        {"text": "🇬🇧 English", "callback_data": "lang_en"},
    ]]


def main_menu_keyboard(lang: str):
    t = TEXTS[lang]
    return [
        [{"text": t["btn_test"], "callback_data": "menu_test"}],
        [{"text": t["btn_quest"], "callback_data": "menu_quest"}],
        [{"text": t["btn_info"], "callback_data": "menu_info"}],
        [{"text": t["btn_help"], "callback_data": "menu_help"}],
    ]


async def show_main_menu(chat_id: int, lang: str):
    t = TEXTS[lang]
    users[chat_id]["state"] = "main_menu"
    await send_message(chat_id, t["main_menu_title"], main_menu_keyboard(lang))


@app.post("/webhook")
async def webhook(request: Request):
    update = await request.json()

    # Обычное сообщение (например, /start)
    if "message" in update:
        chat_id = update["message"]["chat"]["id"]
        text = update["message"].get("text", "")

        if chat_id not in users:
            users[chat_id] = {"lang": None, "state": "choose_language", "answers": {}}

        if text == "/start" or users[chat_id]["state"] == "choose_language":
            users[chat_id]["state"] = "choose_language"
            await send_message(chat_id, "🇰🇿 / 🇷🇺 / 🇬🇧\n" + TEXTS["ru"]["choose_language"], language_keyboard())

    # Нажатие на inline-кнопку
    elif "callback_query" in update:
        cq = update["callback_query"]
        chat_id = cq["message"]["chat"]["id"]
        data = cq["data"]
        await answer_callback(cq["id"])

        if chat_id not in users:
            users[chat_id] = {"lang": None, "state": "choose_language", "answers": {}}

        if data.startswith("lang_"):
            lang = data.split("_")[1]  # kz / ru / en
            users[chat_id]["lang"] = lang
            await show_main_menu(chat_id, lang)

        elif data.startswith("menu_"):
            lang = users[chat_id]["lang"] or "ru"
            t = TEXTS[lang]
            if data == "menu_test":
                # TODO: следующий этап — запуск теста Q1-Q18
                await send_message(chat_id, t["coming_soon"])
            elif data == "menu_quest":
                await send_message(chat_id, t["coming_soon"])
            elif data == "menu_info":
                await send_message(chat_id, t["coming_soon"])
            elif data == "menu_help":
                await send_message(chat_id, t["coming_soon"])

    return {"ok": True}


@app.get("/")
async def health():
    return {"status": "ARFID bot is running"}
