import asyncio
import logging

from aiogram import Bot, Dispatcher, Router
from config import TOKEN

from app.survey_handlers import router as survey_router
from app.vac_handlers import router as vac_router
from app.searcher_handlers import router as searcher_router

async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(survey_router)
    dp.include_router(vac_router)
    dp.include_router(searcher_router)
    await dp.start_polling(bot)

# --- RUN BOT ---
if __name__ == '__main__':

    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Bot stopped')


