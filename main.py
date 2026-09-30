import os
import httpx
from fastapi import FastAPI, Request

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

app = FastAPI()

# Состояние пользователя в памяти:
# {chat_id: {"lang": "ru", "state": "main_menu", "answers": {}}}
users = {}

TEXTS = {
    "kz": {
        "choose_language": "Тілді таңдаңыз:",
        "main_menu_title": "🏠 Басты мәзір",
        "btn_test": "📝 Тестен өту",
        "btn_quest": "🌱 Food Quest",
        "btn_info": "📚 ARFID дегеніміз не?",
        "btn_help": "❤️ Көмек керек пе?",
        "btn_back": "🏠 Басты мәзірге",
        "coming_soon": "Бұл бөлім жақында қосылады 🙂",
        "test_intro": "Тест 18 сұрақтан тұрады. Әр сұраққа қаншалықты жиі сай келетінін таңда.",
        "question_prefix": "Сұрақ",
        "result_title": "📊 Нәтиже",
        "result_score": "Жалпы балл",
        "attention_title": "Назар аударатын жайттар",
        "attention_intro": "Сен келесі сұрақтарға «жиі» немесе «дерлік әрдайым» деп жауап бердің:",
        "no_attention": "Ерекше алаңдаушылық тудыратын жауап жоқ.",
        "disclaimer": "⚠️ Бұл тест диагноз қоймайды. Бұл — өзіңді жақсырақ түсінуге көмектесетін скрининг.",
        "specialists_title": "Кімге баруға болады:",
        "specialists": ["психиатр", "клиникалық психолог", "психотерапевт", "тамақтану бұзылыстары бойынша маман"],
    },
    "ru": {
        "choose_language": "Выберите язык:",
        "main_menu_title": "🏠 Главное меню",
        "btn_test": "📝 Пройти тест",
        "btn_quest": "🌱 Food Quest",
        "btn_info": "📚 Что такое ARFID?",
        "btn_help": "❤️ Нужна помощь?",
        "btn_back": "🏠 В главное меню",
        "coming_soon": "Этот раздел скоро появится 🙂",
        "test_intro": "Тест состоит из 18 вопросов. Для каждого выбери, насколько часто это про тебя.",
        "question_prefix": "Вопрос",
        "result_title": "📊 Результат",
        "result_score": "Общий балл",
        "attention_title": "На что стоит обратить внимание",
        "attention_intro": "Ты ответил(а) «часто» или «почти всегда» на следующие вопросы:",
        "no_attention": "Нет ответов, которые вызывают особое беспокойство.",
        "disclaimer": "⚠️ Этот тест не ставит диагноз. Это скрининг, который помогает лучше понять себя.",
        "specialists_title": "К кому можно обратиться:",
        "specialists": ["психиатр", "клинический психолог", "психотерапевт", "специалист по расстройствам пищевого поведения"],
    },
    "en": {
        "choose_language": "Choose your language:",
        "main_menu_title": "🏠 Main menu",
        "btn_test": "📝 Take the test",
        "btn_quest": "🌱 Food Quest",
        "btn_info": "📚 What is ARFID?",
        "btn_help": "❤️ Need help?",
        "btn_back": "🏠 Main menu",
        "coming_soon": "This section is coming soon 🙂",
        "test_intro": "The test has 18 questions. For each one, choose how often it applies to you.",
        "question_prefix": "Question",
        "result_title": "📊 Result",
        "result_score": "Total score",
        "attention_title": "What's worth paying attention to",
        "attention_intro": "You answered \"often\" or \"almost always\" to these questions:",
        "no_attention": "No answers stand out as a particular concern.",
        "disclaimer": "⚠️ This test does not give a diagnosis. It's a screening to help you understand yourself better.",
        "specialists_title": "Who you could talk to:",
        "specialists": ["a psychiatrist", "a clinical psychologist", "a psychotherapist", "an eating disorder specialist"],
    },
}

SCALE = {
    "kz": ["Ешқашан", "Сирек", "Кейде", "Жиі", "Дерлік әрдайым"],
    "ru": ["Никогда", "Редко", "Иногда", "Часто", "Почти всегда"],
    "en": ["Never", "Rarely", "Sometimes", "Often", "Almost always"],
}

# 18 вопросов, сгруппированные по 4 блокам (как в исходном ТЗ)
QUESTIONS = [
    {"id": 1, "ru": "У меня очень ограниченный список «безопасных» продуктов.",
     "kz": "Менің «қауіпсіз» тағамдарымның тізімі өте шектеулі.",
     "en": "I have a very limited list of \"safe\" foods."},
    {"id": 2, "ru": "Я избегаю многих продуктов из-за текстуры, запаха или вкуса.",
     "kz": "Мен көптеген тағамдардан құрылымына, иісіне немесе дәміне байланысты бас тартамын.",
     "en": "I avoid many foods because of their texture, smell, or taste."},
    {"id": 3, "ru": "Мне трудно пробовать новую еду.",
     "kz": "Маған жаңа тағамды тәттеп көру қиын.",
     "en": "It's hard for me to try new foods."},
    {"id": 4, "ru": "Я могу отказаться от еды, даже если голоден(на).",
     "kz": "Мен ашыққан кезде де тамақтан бас тарта аламын.",
     "en": "I can refuse to eat even when I'm hungry."},
    {"id": 5, "ru": "Некоторые продукты вызывают у меня сильное отвращение.",
     "kz": "Кейбір тағамдар маған қатты жиіркеніш тудырады.",
     "en": "Some foods cause me strong disgust."},
    {"id": 6, "ru": "Я боюсь подавиться во время еды.",
     "kz": "Мен тамақтанып жатқанда буынып қалудан қорқамын.",
     "en": "I'm afraid of choking while eating."},
    {"id": 7, "ru": "Я переживаю, что после еды мне станет плохо.",
     "kz": "Мен тамақтан кейін жаман сезінуден қорқамын.",
     "en": "I worry that I'll feel sick after eating."},
    {"id": 8, "ru": "Еда вызывает у меня тревогу или стресс.",
     "kz": "Тамақ маған мазасыздық немесе стресс тудырады.",
     "en": "Food causes me anxiety or stress."},
    {"id": 9, "ru": "Я избегаю определенных продуктов после неприятного опыта.",
     "kz": "Мен жағымсыз тәжірибеден кейін белгілі бір тағамдардан бас тартамын.",
     "en": "I avoid certain foods after a bad experience with them."},
    {"id": 10, "ru": "Мне сложно есть в присутствии других людей.",
     "kz": "Маған басқа адамдардың алдында тамақтану қиын.",
     "en": "It's hard for me to eat in front of other people."},
    {"id": 11, "ru": "Я часто пропускаю приемы пищи.",
     "kz": "Мен жиі тамақтануды өткізіп аламын.",
     "en": "I often skip meals."},
    {"id": 12, "ru": "Мне трудно получать достаточное количество калорий.",
     "kz": "Маған жеткілікті калория алу қиын.",
     "en": "It's hard for me to get enough calories."},
    {"id": 13, "ru": "У меня были проблемы с весом из-за ограниченного питания.",
     "kz": "Шектеулі тамақтануға байланысты салмағыммен мәселелерім болды.",
     "en": "I've had weight problems because of restricted eating."},
    {"id": 14, "ru": "Врачи или близкие беспокоились о моем питании.",
     "kz": "Дәрігерлер немесе жақындарым тамақтануым туралы алаңдаған.",
     "en": "Doctors or people close to me have worried about my eating."},
    {"id": 15, "ru": "Я принимаю витамины или добавки, чтобы компенсировать рацион.",
     "kz": "Мен рационымды толықтыру үшін дәрумендер немесе қоспалар қабылдаймын.",
     "en": "I take vitamins or supplements to make up for my diet."},
    {"id": 16, "ru": "Я ограничиваю еду НЕ ради похудения.",
     "kz": "Мен тамақты арықтау үшін ШЕКТЕМЕЙМІН.",
     "en": "I restrict food NOT in order to lose weight."},
    {"id": 17, "ru": "Меня мало волнует набор веса по сравнению с самой едой.",
     "kz": "Салмақ қосу мені тамақтың өзімен салыстырғанда аз алаңдатады.",
     "en": "Gaining weight worries me much less than the food itself."},
    {"id": 18, "ru": "Основная причина ограничения пищи — дискомфорт или страх, а не фигура.",
     "kz": "Тамақты шектеудің басты себебі — фигура емес, ыңғайсыздық немесе қорқыныш.",
     "en": "The main reason I restrict food is discomfort or fear, not body shape."},
]


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


def question_keyboard(lang: str, qnum: int):
    labels = SCALE[lang]
    return [[{"text": labels[v], "callback_data": f"ans_{qnum}_{v}"}] for v in range(5)]


async def show_main_menu(chat_id: int, lang: str):
    t = TEXTS[lang]
    users[chat_id]["state"] = "main_menu"
    await send_message(chat_id, t["main_menu_title"], main_menu_keyboard(lang))


async def send_question(chat_id: int, lang: str, qnum: int):
    t = TEXTS[lang]
    users[chat_id]["state"] = f"test_q{qnum}"
    q = QUESTIONS[qnum - 1]
    text = f"{t['question_prefix']} {qnum}/18\n\n{q[lang]}"
    await send_message(chat_id, text, question_keyboard(lang, qnum))


async def start_test(chat_id: int, lang: str):
    t = TEXTS[lang]
    users[chat_id]["answers"] = {}
    await send_message(chat_id, t["test_intro"])
    await send_question(chat_id, lang, 1)


def compute_flags(answers: dict) -> dict:
    def any_pos(*ids):
        return any(answers.get(f"q{i}", 0) >= 3 for i in ids)

    return {
        "narrow_food": any_pos(1, 2, 3, 4, 5),
        "food_fear": any_pos(6, 7, 8, 9),
        "nutrition_problem": any_pos(11, 12, 13, 14, 15),
        "social_problem": any_pos(10),
    }


def interpretation(lang: str, score: int) -> str:
    ranges = {
        "ru": [
            (0, 15, "Признаки ARFID маловероятны."),
            (16, 30, "Есть отдельные особенности пищевого поведения, стоит понаблюдать."),
            (31, 45, "Возможны выраженные признаки ARFID. Желательна консультация специалиста."),
            (46, 999, "Высокая вероятность расстройства пищевого поведения типа ARFID. Рекомендуется профессиональная диагностика."),
        ],
        "kz": [
            (0, 15, "ARFID белгілері екіталай."),
            (16, 30, "Тамақтану мінез-құлқында кейбір ерекшеліктер бар, бақылап жүрген жөн."),
            (31, 45, "ARFID белгілері айқын болуы мүмкін. Маманмен кеңесу ұсынылады."),
            (46, 999, "ARFID типті тамақтану бұзылысының ықтималдығы жоғары. Кәсіби диагностика ұсынылады."),
        ],
        "en": [
            (0, 15, "Signs of ARFID are unlikely."),
            (16, 30, "There are some notable eating-behaviour features worth watching."),
            (31, 45, "There may be pronounced signs of ARFID. Talking to a specialist would be a good idea."),
            (46, 999, "High likelihood of an ARFID-type eating disorder. Professional evaluation is recommended."),
        ],
    }
    for low, high, text in ranges[lang]:
        if low <= score <= high:
            return text
    return ""


async def show_result(chat_id: int, lang: str):
    t = TEXTS[lang]
    answers = users[chat_id]["answers"]
    score = sum(answers.values())
    compute_flags(answers)  # флаги посчитаны, доступны для дальнейшего расширения логики

    positive = [q for q in QUESTIONS if answers.get(f"q{q['id']}", 0) >= 3]

    lines = [t["result_title"], "", f"{t['result_score']}: {score}", "", interpretation(lang, score), ""]

    lines.append(t["attention_title"])
    if positive:
        lines.append(t["attention_intro"])
        for q in positive:
            lines.append(f"• Q{q['id']} — {q[lang]}")
    else:
        lines.append(t["no_attention"])
    lines.append("")
    lines.append(t["disclaimer"])

    if positive:
        lines.append("")
        lines.append(t["specialists_title"])
        for s in t["specialists"]:
            lines.append(f"• {s}")

    await send_message(chat_id, "\n".join(lines))
    users[chat_id]["state"] = "main_menu"
    await show_main_menu(chat_id, lang)


@app.post("/webhook")
async def webhook(request: Request):
    update = await request.json()

    if "message" in update:
        chat_id = update["message"]["chat"]["id"]
        text = update["message"].get("text", "")

        if chat_id not in users:
            users[chat_id] = {"lang": None, "state": "choose_language", "answers": {}}

        if text == "/start" or users[chat_id]["state"] == "choose_language":
            users[chat_id]["state"] = "choose_language"
            await send_message(chat_id, "🇰🇿 / 🇷🇺 / 🇬🇧\n" + TEXTS["ru"]["choose_language"], language_keyboard())

    elif "callback_query" in update:
        cq = update["callback_query"]
        chat_id = cq["message"]["chat"]["id"]
        data = cq["data"]
        await answer_callback(cq["id"])

        if chat_id not in users:
            users[chat_id] = {"lang": None, "state": "choose_language", "answers": {}}

        lang = users[chat_id]["lang"] or "ru"

        if data.startswith("lang_"):
            lang = data.split("_")[1]
            users[chat_id]["lang"] = lang
            await show_main_menu(chat_id, lang)

        elif data.startswith("menu_"):
            t = TEXTS[lang]
            if data == "menu_test":
                await start_test(chat_id, lang)
            elif data == "menu_quest":
                await send_message(chat_id, t["coming_soon"])
            elif data == "menu_info":
                await send_message(chat_id, t["coming_soon"])
            elif data == "menu_help":
                await send_message(chat_id, t["coming_soon"])

        elif data.startswith("ans_"):
            _, qnum_str, value_str = data.split("_")
            qnum = int(qnum_str)
            value = int(value_str)
            users[chat_id]["answers"][f"q{qnum}"] = value

            if qnum < 18:
                await send_question(chat_id, lang, qnum + 1)
            else:
                await show_result(chat_id, lang)

    return {"ok": True}


@app.get("/")
async def health():
    return {"status": "ARFID bot is running"}
