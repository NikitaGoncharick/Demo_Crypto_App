#Формат аутентификации данных для API (Pydantic)
from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    password: str
    email: str

class AddMoney(BaseModel):
    amount: float

class TradeAsset(BaseModel):
    symbol: str
    quantity: float