from dataclasses import dataclass
from dataclasses_json import DataClassJsonMixin


@dataclass
class ProjectResponse(DataClassJsonMixin):
    __slots__ = ("name", "expense", "comment", "amount", "currency")
    name: str
    expense: str
    comment: str
    amount: int
    currency: str
