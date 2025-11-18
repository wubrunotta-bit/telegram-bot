import os
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import LabeledPrice, PreCheckoutQuery, InlineKeyboardMarkup, InlineKeyboardButton

bot = Bot(token=os.getenv("TOKEN"))
dp = Dispatcher(bot)

PACKAGES = {
    "pack100": {"stars": 100, "price": 199, "title": "100 Stelle + Bonus"},
    "pack500": {"stars": 500, "price": 899, "title": "500 Stelle + Canale VIP 1 mese"},
    "pack1000": {"stars": 1000, "price": 1699, "title": "1000 Stelle + VIP 3 mesi"},
}

@dp.message(commands=['start', 'menu'])
async def start(msg: types.Message):
    kb = InlineKeyboardMarkup()
    for k, v in PACKAGES.items():
        kb.add(InlineKeyboardButton(text=f"{v['title']} — €{v['price']/100}", callback_data=f"buy_{k}"))
    await msg.answer("🌟 Scegli il tuo pacchetto di Stelle:", reply_markup=kb)

@dp.callback_query(lambda c: c.data.startswith('buy_'))
async def buy(cb: types.CallbackQuery):
    pack = PACKAGES[cb.data.split("_")[1]]
    await bot.send_invoice(
        chat_id=cb.from_user.id,
        title=pack["title"],
        description=f"Ricevi {pack['stars']} Telegram Stars + bonus esclusivo",
        payload=cb.data.split("_")[1],
        provider_token="",                  # vuoto per Stars
        currency="XTR",                     # obbligatorio
        prices=[LabeledPrice(label=pack["title"], amount=pack["price"])],
        start_parameter="stars"
    )

@dp.pre_checkout_query()
async def precheckout(query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(query.id, ok=True)

@dp.message(content_types=types.ContentType.SUCCESSFUL_PAYMENT)
async def paid(msg: types.Message):
    pack = PACKAGES[msg.successful_payment.invoice_payload]
    await msg.answer(f"✅ Pagamento ricevuto!\nTi ho appena dato {pack['stars']} Stelle + il tuo bonus.\nGrazie mille ❤️")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
