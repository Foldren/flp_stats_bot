# from typing import Union
# from aiogram.filters import BaseFilter
# from aiogram.types import Message, CallbackQuery
# from config import USERS_NAMES
#
#
# class IsParticipantFilter(BaseFilter):
#     async def __call__(self, event: Union[Message, CallbackQuery]) -> bool:
#         return event.from_user.id in USERS_NAMES.keys()
