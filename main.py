import os
import asyncio
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.types import LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton, Update
from aiogram.filters import Command
from aiogram import F
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Controlla che il token sia configurato
token = os.getenv("TOKEN")
if not token:
    raise ValueError("❌ Errore: variabile di ambiente TOKEN non configurata!")

# Configurazione webhook
WEBHOOK_HOST = os.getenv("RENDER_EXTERNAL_URL", "http://localhost")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", 5000))

bot = Bot(token=token)
dp = Dispatcher()

PACKAGES = {
    "pack100": {"stars": 100, "price": 199, "title": "100 Stelle + Bonus"},
    "pack500": {"stars": 500, "price": 899, "title": "500 Stelle + VIP"},
    "pack1000": {"stars": 1000, "price": 1699, "title": "1000 Stelle + VIP"},
}

@dp.message(Command("start", "menu"))
async def start(message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{v['title']} — €{v['price']/100:.2f}", callback_data=f"buy_{k}")]
        for k, v in PACKAGES.items()
    ])
    await message.answer("🌟 Scegli il pacchetto Stelle che vuoi acquistare:", reply_markup=kb)

@dp.callback_query(F.data.startswith("buy_"))
async def buy(callback):
    try:
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
    except Exception as e:
        logger.error(f"Errore in buy: {e}")
        await callback.answer("❌ Errore nel processamento", show_alert=True)

@dp.pre_checkout_query()
async def precheckout(query):
    await bot.answer_pre_checkout_query(query.id, ok=True)

@dp.message(F.successful_payment)
async def paid(message):
    try:
        pack_id = message.successful_payment.invoice_payload
        pack = PACKAGES[pack_id]
        await message.answer(f"✅ Pagamento ricevuto!\n\nTi ho accreditato {pack['stars']} Stelle + il bonus!")
        logger.info(f"Pagamento ricevuto da {message.from_user.id} per {pack_id}")
    except Exception as e:
        logger.error(f"Errore in paid: {e}")

async def on_startup():
    """Configura il webhook quando l'app parte"""
    await bot.set_webhook(url=WEBHOOK_URL, drop_pending_updates=True)
    logger.info(f"✅ Webhook configurato: {WEBHOOK_URL}")

async def on_shutdown():
    """Pulisce il webhook quando l'app si ferma"""
    await bot.delete_webhook()
    logger.info("✅ Webhook rimosso")

async def main():
    # Startup
    await on_startup()
    
    # Crea l'app web
    app = web.Application()
    
    # Setup della route webhook
    SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    ).register(app, path=WEBHOOK_PATH)
    
    # Setup dell'applicazione
    setup_application(app, dp, bot=bot)
    
    # Avvia il server
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, WEBAPP_HOST, WEBAPP_PORT)
    await site.start()
    
    logger.info(f"🚀 Bot avviato su {WEBAPP_HOST}:{WEBAPP_PORT}")
    
    # Mantieni il server in esecuzione
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        await on_shutdown()
        await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
