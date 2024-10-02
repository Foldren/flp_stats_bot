from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.kbd.select import ManagedMultiselect
from models import Bank


async def on_select_banks(event: CallbackQuery, select: ManagedMultiselect, dialog_manager: DialogManager, bank_id: str):
    dialog_manager.dialog_data['selected'] = select.get_checked()
    dialog_manager.dialog_data['are_selected'] = True if dialog_manager.dialog_data['selected'] else False


async def on_confirm(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await Bank.filter(id__in=dialog_manager.dialog_data['selected']).delete()
    await callback.answer("✅ Банки удалены успешно!", show_alert=True)
    await dialog_manager.done()


