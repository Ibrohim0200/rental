import asyncio
import json
import os
from datetime import datetime
from aiogram.client.default import DefaultBotProperties
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import (
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton,
    WebAppInfo,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from flask import Flask

from bot.config.env import BOT_TOKEN, WEBAPP_URL, CHANNEL_ID
from bot.database.db import init_db, save_order
from bot.locale.get_lang import get_localized_text


app = Flask(__name__)

@app.route("/")
def index():
    return "🤖 Bot ishlamoqda!"

bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


# 1️⃣ START — til tanlash
@dp.message(CommandStart())
async def start_handler(message: types.Message, state: FSMContext):
    # Til tanlash tugmalari
    lang_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇺🇿 O‘zbekcha", callback_data="lang_uz"),
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
                InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en"),
            ]
        ]
    )
    await message.answer("🌐 Iltimos, tilni tanlang / Please choose language:", reply_markup=lang_kb)


# 2️⃣ Til tanlanganda
@dp.callback_query(F.data.startswith("lang_"))
async def set_language(callback: CallbackQuery, state: FSMContext):
    lang = callback.data.split("_")[1]
    await state.update_data(lang=lang)

    welcome_text = get_localized_text(lang, "start.welcome")
    choose_car = get_localized_text(lang, "start.choose_car")
    rental_button = get_localized_text(lang, "start.rental_button")

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=rental_button, web_app=WebAppInfo(url=f"{WEBAPP_URL}?lang={lang}"))]
        ],
        resize_keyboard=True,
    )

    await callback.message.answer(f"{welcome_text}\n\n{choose_car}", reply_markup=kb)
    await callback.answer()



@dp.message(F.web_app_data)
async def webapp_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")

    try:
        form = json.loads(message.web_app_data.data)

        name = form["name"]
        phone = form["phone"]
        date_from = form["date_from"]
        date_to = form["date_to"]
        car = form["car"]
        price = int("".join([c for c in form["price"] if c.isdigit()]))

        days = (datetime.strptime(date_to, "%Y-%m-%d") - datetime.strptime(date_from, "%Y-%m-%d")).days
        total = price * days

        text_user = (
            f"📋 <b>{get_localized_text(lang, 'start.choose_car')}</b>\n\n"
            f"👤 {name}\n📞 {phone}\n🚘 {car}\n💰 {price:,} / kun\n📅 {date_from} → {date_to}\n\n"
            f"{get_localized_text(lang, 'order.send_passport')}"
        )

        await message.answer(text_user)

        text_channel = (
            f"🟡 Mijoz form to‘ldirdi!\n\n"
            f"👤 {name}\n📞 {phone}\n📅 {date_from} → {date_to}\n🚘 {car}\n💰 {price:,}/kun\n📊 Jami: {total:,}"
        )

        await message.bot.send_message(CHANNEL_ID, text_channel)

        await state.update_data(
            name=name,
            phone=phone,
            car=car,
            date_from=date_from,
            date_to=date_to,
            price=price,
            total=total,
        )

    except Exception as e:
        await message.answer(f"❌ {e}")


# 4️⃣ Passport rasmi kelganda
@dp.message(F.photo)
async def handle_passport(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")

    if not data:
        await message.answer("❌ Avval formni to‘ldiring.")
        return

    photo = message.photo[-1].file_id
    await state.update_data(passport_photo=photo)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=get_localized_text(lang, "answers.confirm"), callback_data="approve")],
            [InlineKeyboardButton(text=get_localized_text(lang, "answers.cancel"), callback_data="cancel")],
        ]
    )

    await message.answer(get_localized_text(lang, "order.rules"), reply_markup=kb)


# 5️⃣ Tasdiqlash
@dp.callback_query(F.data == "approve")
async def approve_order(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")

    if not data:
        await callback.answer(get_localized_text(lang, "answers.not_found"), show_alert=True)
        return

    text = (
        f"🟢 Buyurtma tasdiqlandi!\n\n"
        f"👤 {data['name']} | 📞 {data['phone']}\n"
        f"🚘 {data['car']}\n📅 {data['date_from']} → {data['date_to']}\n📊 Jami: {data['total']:,}"
    )

    if "passport_photo" in data:
        await callback.bot.send_photo(CHANNEL_ID, data["passport_photo"], caption=text)
    else:
        await callback.bot.send_message(CHANNEL_ID, text)

    await save_order(data)

    confirm_text = get_localized_text(lang, "order.confirm")
    await callback.message.answer(confirm_text)
    await state.clear()


# 6️⃣ Bekor qilish
@dp.callback_query(F.data == "cancel")
async def cancel_order(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")

    if not data:
        await callback.answer(get_localized_text(lang, "answers.not_found"), show_alert=True)
        return

    text = f"🔴 Buyurtma bekor qilindi!\n👤 {data['name']} | 📞 {data['phone']}"
    await callback.bot.send_message(CHANNEL_ID, text)

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=get_localized_text(lang, "start.rental_button"), web_app=WebAppInfo(url=WEBAPP_URL))]
        ],
        resize_keyboard=True,
    )

    cancel_text = get_localized_text(lang, "order.cancel")
    await callback.message.answer(cancel_text, reply_markup=kb)
    await state.clear()


# 7️⃣ Run
async def start_bot():
    await init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    print("🤖 Bot ishga tushdi...")
    await dp.start_polling(bot)

# -----------------------------
# Flask + asyncio bot
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    loop = asyncio.get_event_loop()
    loop.create_task(start_bot())
    app.run(host="0.0.0.0", port=port)
