from aiogram_dialog import DialogManager
from models import Bank


async def get_banks(**kwargs):
    dialog_manager: DialogManager = kwargs['dialog_manager']
    banks = await Bank.filter(user_id=dialog_manager.event.from_user.id)

    return {
        "banks": banks,
        "not_empty": True if banks else False
    }
