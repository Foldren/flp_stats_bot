from asyncio import run
from contextlib import asynccontextmanager
from aioclock import AioClock, At
from tortoise import Tortoise
from config import SQL_URL, APP_NAME
from modules.logger import Logger
from modules.playwright.maybank import Maybank


@asynccontextmanager
async def lifespan(_: AioClock):
    await Tortoise.init(db_url=SQL_URL, modules={"models": ["models"]})
    await Tortoise.generate_schemas(safe=True)
    await Logger(APP_NAME).success(msg="Планировщик запущен.", func_name="startup")
    yield _

app = AioClock(lifespan=lifespan)


@app.task(trigger=At(tz="Europe/Moscow", hour=3, minute=0))
async def load_stats():
    """
    Таск на подгрузку выписок, подгружает каждый день в 3 часа ночи.
    """
    await Maybank().load_stats()


if __name__ == '__main__':
    run(app.serve())
