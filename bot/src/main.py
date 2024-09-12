import logging
from asyncio import run
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.base import DefaultKeyBuilder
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import Message
from aiogram_dialog import setup_dialogs, DialogManager, StartMode, ShowMode
from redis.asyncio import Redis
from tortoise import run_async
from tortoise.exceptions import IntegrityError
from components.dialogs import d_menu, d_get_banks, d_create_bank, d_delete_banks
from components.states import MenuStates
from config import TOKEN, REDIS_URL
from init import init_db
from models import User

# Используемые базы данных Redis
# db0 - кеш для стейтов бота

dialogs = (d_menu, d_get_banks, d_create_bank, d_delete_banks,)
dp = Dispatcher(storage=RedisStorage(Redis.from_url(REDIS_URL, db=0), DefaultKeyBuilder(with_destiny=True)))


async def main():
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    dp.message.filter(F.chat.type == "private")
    dp.callback_query.filter(F.message.chat.type == "private")

    # Включаем логирование, чтобы не пропустить важные сообщения
    logging.basicConfig(level=logging.INFO)
    dp.include_routers(*dialogs)
    setup_dialogs(dp)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=["message", "callback_query"], skip_updates=True)


@dp.message(F.text == "/start")
async def start(message: Message, dialog_manager: DialogManager):
    try:
        await User.create(id=message.from_user.id)
    except IntegrityError:
        pass
    await dialog_manager.start(state=MenuStates.main, mode=StartMode.RESET_STACK, show_mode=ShowMode.DELETE_AND_SEND)


if __name__ == "__main__":
    run_async(init_db())
    run(main())
