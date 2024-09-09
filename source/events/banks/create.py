from aiogram.types import Message, CallbackQuery
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button
from cryptography.fernet import Fernet
from ujson import dumps
from config import BANKS_CREDS, SECRET_KEY
from models import Bank


async def on_select_type(callback: CallbackQuery, button: Button, dialog_manager: DialogManager, selected_type: str):
    dialog_manager.dialog_data['type'] = selected_type
    await dialog_manager.next(show_mode=ShowMode.DELETE_AND_SEND)


async def on_set_name(message: Message, widget: MessageInput, dialog_manager: DialogManager):
    dialog_manager.dialog_data['name'] = message.text
    dialog_manager.dialog_data['params'] = ", ".join(BANKS_CREDS[dialog_manager.dialog_data['type']])
    await dialog_manager.next(show_mode=ShowMode.DELETE_AND_SEND)


async def on_set_creds(message: Message, widget: MessageInput, dialog_manager: DialogManager):
    dialog_manager.show_mode = ShowMode.DELETE_AND_SEND
    creds = message.text.strip().split(",")
    params = BANKS_CREDS[dialog_manager.dialog_data['type']]

    if len(creds) != len(params):
        await message.answer("⚠️ Данные авторизации введены неверно!")
        return

    auth_data = {}
    for param, cred in zip(params, creds):
        auth_data[param] = cred

    f = Fernet(SECRET_KEY)
    auth_data = f.encrypt(dumps(auth_data).encode())

    await Bank.create(
        user_id=message.from_user.id,
        name=dialog_manager.dialog_data['name'],
        type=dialog_manager.dialog_data['type'],
        json_hash_data=auth_data
    )
    await message.answer("✅ Банк создан успешно!")
    await dialog_manager.done()
