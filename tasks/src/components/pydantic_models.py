from pydantic import BaseModel


class MaybankData(BaseModel):
    corporate_id: str
    user_id: str
    password: str
