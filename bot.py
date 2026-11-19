import asyncio
import os
import random
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.enums import ChatType
from aiogram.fsm.storage.memory import MemoryStorage
from openai import AsyncOpenAI

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

client = AsyncOpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

MODES = {
    "toxic": (
        "Ты очень токсичный, саркастичный и язвительный бот. "
        "Отвечай грубо, с издёвкой, но без прямой матерщины. "
        "Будь максимально едким и язвительным."
    ),
    "smart": (
        "Ты очень умный, эрудированный и вежливый ассистент. "
        "Отвечай подробно, логично, по делу и с примерами."
    ),
    "stupid": (
        "Ты очень глупый бот. Ты плохо понимаешь вопросы, путаешь слова, "
        "отвечаешь невпопад и иногда несёшь полную чушь. "
        "Говори просто, коротко и глупо."
    )
}

MODE_NAMES = {
    "toxic": "☠️ Токсичный",
    "smart": "🧠 Умный",
    "stupid": "🤪 Глупый"
}

ACTIVITY_NAMES = {
    "quiet": "🔇 Тихий",
    "medium": "⚖️ Средний",
    "talkative": "🗣️ Болтливый"
}

chat_settings = {}

def get_settings(chat_id: int):
    if chat_id not in chat_settings:
        chat_settings[chat_id] = {
            "mode": "smart",
            "activity": "medium",
            "history": []
        }
    return chat_settings[chat_id]

def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="☠️ Токсичный"), KeyboardButton(text="🧠 Умный"), KeyboardButton(text="🤪 Глупый")],
            [KeyboardButton(text="🔇 Тихий"), KeyboardButton(text="⚖️ Средний"), KeyboardButton(text="🗣️ Болтливый")],
            [KeyboardButton(text="❓ Текущие настройки"), KeyboardButton(text="🗑️ Очистить память")]
        ],
        resize_keyboard=True
    )

@dp.message(CommandStart())
async def cmd_start(message: Message):
    settings = get_settings(message.chat.id)
    text = (
        "Привет! Я бот с характерами и уровнем активности.\n\n"
        f"Сейчас:\n"
        f"• Характер: {MODE_NAMES[settings['mode']]}\n"
        f"• Активность: {ACTIVITY_NAMES[settings['activity']]}\n\n"
        "В личке используй кнопки ниже.\n"
        "В группе используй команды:\n"
        "/mode toxic | smart | stupid\n"
        "/activity quiet | medium | talkative\n"
        "/status — текущие настройки\n"
        "/clear — очистить память"
    )
    if message.chat.type == ChatType.PRIVATE:
        await message.answer(text, reply_markup=get_main_keyboard())
    else:
        await message.answer(text)

@dp.message(Command("status"))
async def cmd_status(message: Message):
    settings = get_settings(message.chat.id)
    await message.answer(
        f"Текущие настройки этого чата:\n"
        f"• Характер: {MODE_NAMES[settings['mode']]}\n"
        f"• Активность: {ACTIVITY_NAMES[settings['activity']]}"
    )

@dp.message(Command("clear"))
async def cmd_clear(message: Message):
    settings = get_settings(message.chat.id)
    settings["history"] = []
    await message.answer("Память этого чата очищена.")

@dp.message(Command("mode"))
async def cmd_mode(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Использование: /mode toxic | smart | stupid")
        return

    mode = args[1].lower().strip()
    if mode not in MODES:
        await message.answer("Доступные режимы: toxic, smart, stupid")
        return

    settings = get_settings(message.chat.id)
    settings["mode"] = mode
    await message.answer(f"Характер изменён на: {MODE_NAMES[mode]}")

@dp.message(Command("activity"))
async def cmd_activity(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Использование: /activity quiet | medium | talkative")
        return

    activity = args[1].lower().strip()
    if activity not in ACTIVITY_NAMES:
        await message.answer("Доступные уровни: quiet, medium, talkative")
        return

    settings = get_settings(message.chat.id)
    settings["activity"] = activity
    await message.answer(f"Активность изменена на: {ACTIVITY_NAMES[activity]}")

@dp.message(F.text.in_(["☠️ Токсичный", "🧠 Умный", "🤪 Глупый"]))
async def set_mode_button(message: Message):
    if message.chat.type != ChatType.PRIVATE:
        return
    mode_map = {
        "☠️ Токсичный": "toxic",
        "🧠 Умный": "smart",
        "🤪 Глупый": "stupid"
    }
    mode = mode_map[message.text]
    settings = get_settings(message.chat.id)
    settings["mode"] = mode
    await message.answer(f"Характер изменён на: {MODE_NAMES[mode]}")

@dp.message(F.text.in_(["🔇 Тихий", "⚖️ Средний", "🗣️ Болтливый"]))
async def set_activity_button(message: Message):
    if message.chat.type != ChatType.PRIVATE:
        return
    activity_map = {
        "🔇 Тихий": "quiet",
        "⚖️ Средний": "medium",
        "🗣️ Болтливый": "talkative"
    }
    activity = activity_map[message.text]
    settings = get_settings(message.chat.id)
    settings["activity"] = activity
    await message.answer(f"Активность изменена на: {ACTIVITY_NAMES[activity]}")

@dp.message(F.text == "❓ Текущие настройки")
async def current_settings_button(message: Message):
    if message.chat.type != ChatType.PRIVATE:
        return
    settings = get_settings(message.chat.id)
    await message.answer(
        f"Сейчас:\n"
        f"• Характер: {MODE_NAMES[settings['mode']]}\n"
        f"• Активность: {ACTIVITY_NAMES[settings['activity']]}"
    )

@dp.message(F.text == "🗑️ Очистить память")
async def clear_button(message: Message):
    if message.chat.type != ChatType.PRIVATE:
        return
    settings = get_settings(message.chat.id)
    settings["history"] = []
    await message.answer("Память очищена.")

@dp.message(F.text)
async def chat_handler(message: Message):
    if not message.text or message.from_user.is_bot:
        return

    settings = get_settings(message.chat.id)
    mode = settings["mode"]
    activity = settings["activity"]
    history = settings["history"]

    should_reply = False

    if message.chat.type == ChatType.PRIVATE:
        should_reply = True
    else:
        bot_me = await bot.get_me()
      text_lower = message.text.lower()
mentioned = f"@{bot_me.username}" in message.text if bot_me.username else False
called_by_name = "ишак" in text_lower
is_reply_to_bot = message.reply_to_message and message.reply_to_message.from_user.id == bot_me.id

if mentioned or called_by_name or is_reply_to_bot:
    should_reply = True
        elif activity == "talkative":
            should_reply = random.random() < 0.45
        elif activity == "medium":
            should_reply = random.random() < 0.18
        elif activity == "quiet":
            should_reply = False

    if not should_reply:
        return

    history.append({"role": "user", "content": message.text})
    if len(history) > 14:
        history = history[-14:]

    system_prompt = MODES[mode]
    messages = [{"role": "system", "content": system_prompt}] + history

    try:
        response = await client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=messages,
            temperature=0.95 if mode == "toxic" else 0.8 if mode == "stupid" else 0.7,
            max_tokens=600
        )
        answer = response.choices[0].message.content.strip()

        history.append({"role": "assistant", "content": answer})
        settings["history"] = history

        await message.answer(answer)
await message.answer(answer)

# Ставим реакцию
try:
    reaction_emoji = random.choice(REACTIONS.get(mode, ["👍"]))
    await message.react([reaction_emoji])
except Exception:
    pass
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

async def main():
    print("Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
