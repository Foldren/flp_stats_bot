from aiogram import F
from aiogram_dialog import Window
from aiogram_dialog.widgets.kbd import Cancel, ScrollingGroup, Row, Multiselect, Button
from aiogram_dialog.widgets.text import Const, Multi, Format
from components.getters import get_banks
from components.states import DeleteBanksStates
from events.banks.delete import on_select_banks, on_confirm

w_select_banks = Window(
    Multi(
        Const("<b>Удаление банков:</b> <i>(шаг 1)</i>"),
        Const("👉 Отметьте банки, которые нужно удалить."),
        sep="\n\n"
    ),
    Row(
        Button(text=Const("Удалить выбранные 🗑"), on_click=on_confirm, id="confirm_btn", when=F['dialog_data']['are_selected']),
        Cancel(text=Const("Отмена ⛔️")),
    ),
    ScrollingGroup(
        Multiselect(
            checked_text=Format("☑️ {item.name} - {item.type.value}"),
            unchecked_text=Format("{item.name} - {item.type.value}"),
            items='banks',
            item_id_getter=lambda item: item.id,
            on_state_changed=on_select_banks,
            id="ms_banks"
        ),
        id="sc_banks",
        width=2,
        height=3,
        hide_on_single_page=True,
    ),
    state=DeleteBanksStates.select_banks,
    getter=get_banks
)
