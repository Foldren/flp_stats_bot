from tortoise import Tortoise
from config import SQL_URL


async def init_db():
    await Tortoise.init(db_url=SQL_URL, modules={"models": ["models"]})
    await Tortoise.generate_schemas(safe=True)