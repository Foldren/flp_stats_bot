from tortoise import Model
from tortoise.fields import BigIntField, \
    CharEnumField, ForeignKeyRelation, ForeignKeyField, OnDelete, ReverseRelation, CharField, BinaryField
from components import enums


class User(Model):
    id = BigIntField(pk=True)  # chat_id
    banks: ReverseRelation['Bank']


class Bank(Model):
    id = BigIntField(pk=True)
    user: ForeignKeyRelation['User'] = ForeignKeyField('models.User', on_delete=OnDelete.CASCADE, related_name="banks")
    name = CharField(max_length=20)
    type = CharEnumField(enum_type=enums.BankType)
    json_hash_data = BinaryField()
