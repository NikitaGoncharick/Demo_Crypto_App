# FastAPI приложение и endpoints
# Все что связано с HTTP (токены, куки, headers) - в эндпоинтах.

import uvicorn
from fastapi import FastAPI, Request, HTTPException, Depends, Form, Response #(Response для создания cookie)
from fastapi.responses import RedirectResponse #Чтобы перенаправлять на другую страницу вместо выброса ошибки
from fastapi.responses import JSONResponse #"упаковка" ответа в понятный для JavaScript формат
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
from crud import UserCRUD, PortfolioCRUD
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
@app.post("/register")
async def register(response: Response, username: str = Form(...), password: str = Form(...), email: str = Form(...), db: Session = Depends(get_db)):

    # Валидируем через Pydantic
    try:
        user_data = UserCreate(username=username, password=password, email=email)
    except ValueError as e:
        return RedirectResponse(url="/reg_page?error=validation_failed", status_code=303)

    new_user = UserCRUD.create_user(db, user_data)

    if not new_user:
        print("User already exists")
        return RedirectResponse(url="/reg_page?error=user_exists", status_code=303)


    access_token = create_access_token(data={"sub": user_data.username}) # Создаем токен | sub "субъект" - того, кому принадлежит токен.
    redirect = RedirectResponse(url="/user-profile", status_code=303)  # 1. Создаем "пустой" редирект
    redirect.set_cookie(key="access_token", value=access_token, httponly=True, max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60) #сохраняем ключ в куки браузера

    return redirect


@app.post("/login")
async def login(response: Response, #для передачи данных с сервера в браузер
                form_data: OAuth2PasswordRequestForm = Depends(), #внутри уже настроены все поля
                db: Session = Depends(get_db)
                ):

    user = UserCRUD.log_in_user(db, form_data.username, form_data.password)
    if not user:
        return RedirectResponse(url="/login_page?error=auth_failed", status_code=303)

    # Создаем токен
    access_token = create_access_token(data={"sub": user.username})

    redirect = RedirectResponse(url="/user-profile", status_code=303) # 1. Создаем "пустой" редирект
    redirect.set_cookie(key="access_token", value=access_token, httponly=True, max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60)  #подготавливаем куки

    return redirect #Браузер получает ОДИН ответ с двумя инструкциями: редирект + куки


#------ Dependency для проверки токена
async def check_auth (request: Request, db: Session = Depends(get_db)) -> User: # request - переменная, которая будет содержать информацию о HTTP запросе #Request - класс из FastAPI, который описывает структуру HTTP запроса
    token = request.cookies.get("access_token") # Получаем токен из куки
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        username = decode_token(token) # Декодируем токен
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        # Ищем пользователя в БД
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")

        return user # ← возвращаем User объект

    # ВАЖНО: выбрасываем исключение, а не просто печатаем!
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
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
@app.get("/user-profile")
async def user_profile(request: Request, current_user: User = Depends(check_auth), db: Session = Depends(get_db)):

    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    portfolio_data = PortfolioCRUD.get_user_portfolio_data(db, current_user.id)

    return templates.TemplateResponse(
        "user-profile.html", {"request": request,
                              "portfolio": portfolio_data["portfolio"], #объект портфеля пользователя, т.к принимаем return {"portfolio": portfolio,"assets": assets}
                              "assets": portfolio_data["assets"],
                              "user": current_user
                              })

# --- API endpoint приема данных ----
# api/ = здесь живут endpoints для данных ( user не увидит отображения названия )
# Отдельный адрес на сервере для приема данных
# Наше модальное окно должно отправлять данные на КОНКРЕТНЫЙ адрес, который знает как: Принять сумму денег. Обновить базу данных. Вернуть ответ
# Без endpoint'а форма будет пытаться отправить данные на текущую страницу, которая не умеет обрабатывать добавление денег.

@app.post("/api/add_money")
async def add_money(request:Request, amount: float = Form(...), current_user: User = Depends(check_auth), db: Session = Depends(get_db)):
    try:
        # 1. Обновляем деньги в базе
        portfolio_operation = PortfolioCRUD.add_money_to_portfolio(db, current_user.id, amount)

        if portfolio_operation:
            # ПРОСТО ПЕРЕНАПРАВЛЯЕМ на страницу профиля
            return RedirectResponse(url="/user-profile", status_code=303)
        else:
            return RedirectResponse(url="/user-profile", status_code=303)

    except Exception as e:
        return RedirectResponse(url=f"/user-profile?error={str(e)}", status_code=303)




# ---------- Обработчик ошибок ----------
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 401:
        return RedirectResponse(url="/login_page")
    return RedirectResponse(url="/login_page")  #если код ошибки другой (например 404 или 500) →
# ----------




if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)