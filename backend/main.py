# FastAPI приложение и endpoints
# Все что связано с HTTP (токены, куки, headers) - в эндпоинтах.

import uvicorn
from fastapi import FastAPI, Request, HTTPException, Depends, Form, Response #(Response для создания cookie)
from fastapi.responses import RedirectResponse #Чтобы перенаправлять на другую страницу вместо выброса ошибки
from fastapi.middleware.cors import CORSMiddleware #Разрешает браузеру делать запросы к вашему API с других доменов.
from fastapi.templating import Jinja2Templates #Превращает HTML-шаблоны в готовые HTML-страницы с подставленными данными.
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm # PasswordBearer - Требует JWT токен в заголовках, PasswordReques - Автоматически читает данные формы, Ожидает поля username и password
from starlette.staticfiles import StaticFiles
from sqlalchemy.orm import Session

import requests
from jose import jwt, ExpiredSignatureError

from database import get_db, engine
from models import Base, User
from schemas import UserCreate
from crud import UserCRUD
from crypto_service import get_crypto_price
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from auth import create_access_token, decode_token


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


@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/reg_page")
async def reg_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/login_page")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/register")
async def register(user: UserCreate, response: Response, db: Session = Depends(get_db)):

    new_user = UserCRUD.create_user(db, user)

    # Создаем токен
    access_token = create_access_token(data={"sub": user.username}) #sub "субъект" - того, кому принадлежит токен.
    response.set_cookie(key="access_token", value=access_token, httponly=True, max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60) #сохраняем ключ в куки браузера
    return { "id": new_user.id, "username": new_user.username, "access_token": access_token }


@app.post("/login")
async def login(response: Response,
                form_data: OAuth2PasswordRequestForm = Depends(), #внутри уже настроены все поля
                db: Session = Depends(get_db)
                ):

    user = UserCRUD.log_in_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    # Создаем токен
    access_token = create_access_token(data={"sub": user.username})
    response.set_cookie(key="access_token", value=access_token, httponly=True, max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60) #сохраняем ключ в куки браузера
    return { "id": user.id, "username": user.username, "userpass":user.password, "access_token": access_token }


#------ Dependency для проверки токена
async def check_auth (request: Request, db: Session = Depends(get_db)) -> bool: # request - переменная, которая будет содержать информацию о HTTP запросе #Request - класс из FastAPI, который описывает структуру HTTP запроса
    token = request.cookies.get("access_token") # Получаем токен из куки
    if not token: return False
    try:
        # Декодируем токен
        username = decode_token(token)
        if username is None:
            return False

        # Ищем пользователя в БД
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            return False

        return True # ← возвращаем User объект
    # ВАЖНО: выбрасываем исключение, а не просто печатаем!
    except ExpiredSignatureError:
        return False
    except Exception as e:
        return False
#------
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



# --- Защищенные эндпоинты ----
@app.get("/main")
async def index(request: Request, auth: bool = Depends(check_auth)):
   if auth:
        return templates.TemplateResponse("base.html",{"request": request})  # Верни HTML страницу, подставив в шаблон данные

   return RedirectResponse(url="/login_page")  # ← явно создаем редирект


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)