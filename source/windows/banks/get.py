from aiogram import F
from aiogram_dialog import Window, ShowMode
from aiogram_dialog.widgets.kbd import Cancel, Row, ScrollingGroup, Select, Start
from aiogram_dialog.widgets.text import Multi, Const, Format
from components.getters import get_banks
from components.states import GetBanksStates, CreateBankStates, DeleteBanksStates
from config import BANKS

w_get_banks = Window(
    Multi(
        Const("<b>Банки</b>"),
        Const(f"📋 Панель управления банками, здесь можно добавить новые\n"
              f"для подгрузки <i>(пока доступны: {", ". join(BANKS)})</i>."),
        Const(f"<u>Кнопки управления:</u>\n"
              f"➕ - добавить банк.\n"
              f"⛔️ - отменить операцию."),
        sep="\n\n"
    ),
    Row(
        Start(text=Const("➕"), id="create_bank", state=CreateBankStates.select_type, show_mode=ShowMode.DELETE_AND_SEND),
        Start(text=Const("🗑"), id="delete_bank", state=DeleteBanksStates.select_banks, show_mode=ShowMode.DELETE_AND_SEND, when=F["not_empty"]),
        Cancel(text=Const("⛔️"))
    ),
    ScrollingGroup(
        Select(
            text=Format("{item.name} - {item.type.value}"),  # Показываем название вместе со статусом
            items='banks',
            item_id_getter=lambda item: item.id,
            id="s_bank"
        ),
        id="sc_banks",
        width=2,
        height=3,
        hide_on_single_page=True
    ),
    state=GetBanksStates.render,
    getter=get_banks
)
