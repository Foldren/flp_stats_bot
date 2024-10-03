from aiogram.enums import ContentType
from aiogram_dialog import Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Cancel, ScrollingGroup, Select, Row, Back
from aiogram_dialog.widgets.text import Multi, Const, Format
from config import BANKS
from components.states import CreateBankStates
from events.banks.create import on_select_type, on_set_name, on_set_creds

w_select_type = Window(
    Multi(
        Const(f"<b>Создание банка:</b> <i>(шаг 1)</i>"),
        Const(f"👉 Выберите тип банка."),
        sep="\n\n"
    ),
    Cancel(text=Const("Отмена ⛔️️")),
    ScrollingGroup(
        Select(
            text=Format("{item}"),
            items=BANKS,
            item_id_getter=str,
            on_click=on_select_type,
            id="s_banks"
        ),
        id="sc_banks",
        width=2,
        height=3,
        hide_on_single_page=True
    ),
    state=CreateBankStates.select_type,
)

w_set_name = Window(
    Multi(
        Const(f"<b>Создание банка:</b> <i>(шаг 2)</i>"),
        Const(f"👉 Введите название банка."),
        Format("<u>Задан тип</u>: {dialog_data[type]}"),
        sep="\n\n"
    ),
    Row(
        Back(text=Const("Назад ⬅️")),
        Cancel(text=Const("Отмена ⛔️"))
    ),
    MessageInput(func=on_set_name, content_types=[ContentType.TEXT]),
    state=CreateBankStates.set_name,
)

w_set_creds = Window(
    Multi(
        Const(f"<b>Создание банка:</b> <i>(шаг 3)</i>"),
        Multi(
            Format("👉 Введите по очереди через запятую данные авторизации: {dialog_data[params]}.\n"
                   "<i>(мы их зашифруем)</i>")
        ),
        Multi(
            Format("<u>Задан тип</u>: {dialog_data[type]}"),
            Format("<u>Задано название</u>: {dialog_data[name]}"),
        ),
        sep="\n\n"
    ),
    Row(
        Back(text=Const("Назад ⬅️")),
        Cancel(text=Const("Отмена ⛔️"))
    ),
    MessageInput(func=on_set_creds, content_types=[ContentType.TEXT]),
    state=CreateBankStates.set_creds,
)
