from asyncio import run
from contextlib import asynccontextmanager
from aioclock import AioClock, At, Every, Once
from tortoise import Tortoise
from config import TORTOISE_CONFIG, APP_NAME
from modules.logger import Logger
from modules.playwright.maybank import Maybank


@asynccontextmanager
async def lifespan(_: AioClock):
    await Tortoise.init(TORTOISE_CONFIG)
    await Tortoise.generate_schemas(safe=True)
    await Logger(APP_NAME).success(msg="Планировщик запущен.", func_name="startup")
    yield _

app = AioClock(lifespan=lifespan)


@app.task(trigger=Every(hours=3))#At(tz="Europe/Moscow", hour=3, minute=5))
async def load_stats():
    """
    Таск на подгрузку выписок, подгружает каждый день в 3 часа ночи.
    """
    await Maybank().load_stats()


if __name__ == '__main__':
    run(app.serve())
