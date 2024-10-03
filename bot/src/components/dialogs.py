from aiogram_dialog import Dialog, LaunchMode
from windows.banks.create import w_set_creds, w_set_name, w_select_type
from windows.banks.delete import w_select_banks
from windows.banks.get import w_get_banks
from windows.menu import w_main
from windows.upload import w_select_end_date, w_select_start_date, w_select_bank

# menu -----------------------------------------------------------------------------------------------------------------
d_menu = Dialog(w_main, launch_mode=LaunchMode.ROOT)

# dialogs --------------------------------------------------------------------------------------------------------------
d_get_banks = Dialog(w_get_banks, launch_mode=LaunchMode.SINGLE_TOP)

d_create_bank = Dialog(w_select_type, w_set_name, w_set_creds, launch_mode=LaunchMode.SINGLE_TOP)

d_delete_banks = Dialog(w_select_banks, launch_mode=LaunchMode.SINGLE_TOP)

d_upload = Dialog(w_select_bank, w_select_start_date, w_select_end_date, launch_mode=LaunchMode.SINGLE_TOP)
