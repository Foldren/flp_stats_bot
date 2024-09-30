from enum import Enum


class BankType(str, Enum):
    MAYBANK = "Maybank"


class BankStatus(str, Enum):
    INVALID_DATA = "Невалидный"
    READY = "Готов"
