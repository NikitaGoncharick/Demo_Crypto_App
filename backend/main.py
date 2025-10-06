#🚀 FastAPI приложение и endpoints

import uvicorn
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware #Разрешает браузеру делать запросы к вашему API с других доменов.
from fastapi.templating import Jinja2Templates #Превращает HTML-шаблоны в готовые HTML-страницы с подставленными данными.
from starlette.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from database import get_db, engine
from models import Base
from schemas import UserCreate
from crud import UserCRUD

# 🚀 Создаем таблицы в БД
Base.metadata.create_all(bind=engine)
app = FastAPI()

# ✅ Настройка статических файлов (CSS, JS, изображения) # .. — значит «выйти на один уровень вверх» (из backend в корень Demo_Crypto_App)

app.mount("/static", StaticFiles(directory="../frontend/css"), name="static")

# Настройка шаблонов
templates = Jinja2Templates(directory="../frontend/templates")

@app.get("/")
async def index (request: Request): # request - переменная, которая будет содержать информацию о HTTP запросе
                                    #Request - класс из FastAPI, который описывает структуру HTTP запроса
    return templates.TemplateResponse("base.html", {"request": request}) #Верни HTML страницу, подставив в шаблон данные


@app.get("/user/all", response_model=list[UserCreate])
async def get_all_users(db: Session = Depends(get_db)):
    return UserCRUD.get_all_users(db)

@app.get("/user/{user_id}", response_model=UserCreate)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    user = UserCRUD.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.post("/user/add", response_model=UserCreate)
async def add_new_user(user: UserCreate, db: Session = Depends(get_db)):
    new_user = UserCRUD.create_user(db, user)
    return new_user


@app.delete("/user/delete/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")
    return UserCRUD.delete_user(db, user_id)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)