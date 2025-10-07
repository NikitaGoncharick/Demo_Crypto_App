# логика токенов
# Токен сохраняется у клиента в LocalStorage браузера / Cookies
# Токен состоит из 3 частей | sub - владелец, exp - время истечения, iat - время создания
from jose import jwt
from datetime import datetime, timedelta
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

def create_access_token(data: dict):
    to_encode = data.copy() # Создаем КОПИЮ данных, чтобы не испортить оригинал
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES) # Создаем время истечения
    to_encode.update({"exp":expire}) # exp - expiration time" (время истечения) | expire - перменная которая хранит значение expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM) #Кодируем все в JWT токен

# def verify_token(token: str):
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         return payload
#     except jwt.JWTError:
#         return None

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        return username
    except Exception:
        return None

