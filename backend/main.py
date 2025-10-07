#🚀 FastAPI приложение и endpoints
from os import access

import uvicorn
from fastapi import FastAPI, Request, HTTPException, Depends, Form
from fastapi.middleware.cors import CORSMiddleware #Разрешает браузеру делать запросы к вашему API с других доменов.
from fastapi.templating import Jinja2Templates #Превращает HTML-шаблоны в готовые HTML-страницы с подставленными данными.
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm # PasswordBearer - Требует JWT токен в заголовках, PasswordReques - Автоматически читает данные формы, Ожидает поля username и password
from jwt.exceptions import JWTException
from starlette.staticfiles import StaticFiles
from sqlalchemy.orm import Session

import jwt #"цифровой пропуск"
import requests

from database import get_db, engine
from models import Base, User
from schemas import UserCreate
from crud import UserCRUD
from crypto_service import get_crypto_price
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from auth import create_access_token


#--------------
# 🚀 Создаем таблицы в БД
Base.metadata.create_all(bind=engine)
app = FastAPI()

#система безопасности (токены), защищает только те endpoints, где вы явно укажете зависимость от токена.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

#разрешение межсайтовых запросов
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="../frontend/css"), name="static") # ✅ Настройка статических файлов (CSS, JS, изображения) # .. — значит «выйти на один уровень вверх» (из backend в корень Demo_Crypto_App)
templates = Jinja2Templates(directory="../frontend/templates") # Настройка шаблонов




@app.get("/reg")
async def reg_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.post("/register")
async def register(user: UserCreate, db: Session = Depends(get_db)):
    new_user = UserCRUD.create_user(db, user)

    access_token = create_access_token(data={"sub": user.username}) #sub -стандартное поле в JWT токене, которое означает "субъект" - того, кому принадлежит токен.

    return {
        "id": new_user.id,
        "username": new_user.username,
        "access_token": access_token,
    }


# @app.post("/login")
# async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
#     user = UserCRUD.authenticate_user(db, form_data.username, form_data.password)
#     if not user:
#         raise HTTPException(status_code=401, detail="Incorrect username or password")
#     return user
#
#     access_token = create_access_token(data={"sub": user.username})
#     return {"access_token": access_token, "token_type": "bearer"}


@app.post("/login-simple")
async def login_simple(usrname: str = Form(..., description="Username"),
                       password: str = Form(..., description="Password"),
                       db: Session = Depends(get_db)):

    user = UserCRUD.simple_user_authenticate(db, usrname, password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    # # Создаем токен
    # access_token = create_access_token(data={"sub": user.username})
    # return {
    #     "access_token": access_token,
    #     "token_type": "bearer"
    # }


@app.get("/crypto/{symbol}")
async def get_crypto_data(symbol: str, db: Session = Depends(get_db)):
    price = get_crypto_price(symbol)
    return {"symbol": symbol, "price": f"{price} USD"}

#------


@app.get("/user/all", response_model=list[UserCreate])
async def get_all_users(db: Session = Depends(get_db)):
    return UserCRUD.get_all_users(db)

@app.get("/user/{user_id}", response_model=UserCreate)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    user = UserCRUD.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.delete("/user/delete/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")
    return UserCRUD.delete_user(db, user_id)

#------

#Dependency для проверки токена

# async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         username: str = payload.get("sub")
#         if username is None:
#             raise HTTPException(status_code=401, detail="Invalid token")
#
#         user = db.query(User).filter(User.username == username).first()
#         if user is None:
#             raise HTTPException(status_code=404, detail="User not found")
#         return user
#
#     except JWTException:
#         raise HTTPException(status_code=401, detail="Invalid token")

# --- Защищенные эндпоинты ----
@app.get("/main")
async def index (request: Request,
                 current_user: User = Depends(get_user)
                 ): # request - переменная, которая будет содержать информацию о HTTP запросе #Request - класс из FastAPI, который описывает структуру HTTP запроса

    return templates.TemplateResponse("base.html", {"request": request}) #Верни HTML страницу, подставив в шаблон данные
#--------------

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)