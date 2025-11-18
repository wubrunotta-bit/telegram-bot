import os
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram import F

bot = Bot(token=os.getenv("TOKEN"))
dp = Dispatcher()

PACKAGES = {
    "pack100":  {"stars": 100,  "price": 199,  "title": "100 Stelle + Bonus piccolo"},
    "pack500":  {"stars": 500,  "price": 899,  "title": "500 Stelle + VIP 1 mese"},
    "pack1000": {"stars": 1000, "price": 1699, "title": "1000 Stelle + VIP 3 mesi"},
}

@dp.message(Command("start", "menu"))
async def start(message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{v['title']} — €{v['price']/100:.2f}", callback_data=f"buy_{k}")]
        for k, v in PACKAGES.items()
    ])
    await message.answer("🌟 Scegli il pacchetto di Stelle che vuoi acquistare:", reply_markup=kb)

@dp.callback_query(F.data.startswith("buy_"))
async def buy(callback):
    pack_id = callback.data.split("_")[1]
    pack = PACKAGES[pack_id]

    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title=pack["title"],
        description=f"Ricevi {pack['stars']} Telegram Stars + bonus esclusivo",
        payload=pack_id,
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label=pack["title"], amount=pack["price"])],
        start_parameter="stars"
    )
    await callback.answer()

@dp.pre_checkout_query()
async def precheckout(query):
    await bot.answer_pre_checkout_query(query.id, ok=True)

@dp.message(F.successful_payment)
async def paid(message):
    pack_id = message.successful_payment.invoice_payload
    pack = PACKAGES[pack_id]
    await message.answer(f"✅ Pagamento ricevuto!\n\nTi ho accreditato {pack['stars']} Stelle + il tuo bonus.\nGrazie mille ❤️")

async def main():
    print("Bot avviato e in ascolto 24/7...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
