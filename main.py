import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.strategy import FSMStrategy
from handlers import user, admin, order
import asyncio
from config import TOKEN
import logging
from database.models import setup_db

API_TOKEN = TOKEN


async def main():
    bot = Bot(token=API_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage, fsm_strategy=FSMStrategy.USER_IN_CHAT)
    setup_db()
    dp.include_router(order.order_router)
    dp.include_router(user.user_router)
    dp.include_router(admin.router)
    try:
        await dp.start_polling(bot, skip_updates=True)
        await bot.delete_webhook(drop_pending_updates=True)
    finally:
        await bot.session.close()

if __name__ == '__main__':

    try:
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            handlers=[logging.FileHandler('logs/bot.log'), logging.StreamHandler(sys.stdout)])
        logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            handlers=[logging.FileHandler('logs/errors.log'), logging.StreamHandler(sys.stdout)])
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print('Bye!')
