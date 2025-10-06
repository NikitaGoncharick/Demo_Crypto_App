#⚡ Операции с БД (Create, Read, Update, Delete)

from sqlalchemy.orm import Session
from fastapi import HTTPException
from sqlalchemy.testing.suite.test_reflection import users

from models import User, Portfolio, Asset, Transaction
from schemas import UserCreate, AddMoney, TradeAsset
from auth import verify_token


class UserCRUD:

    # @staticmethod
    # def get_user_by_token(db: Session, token: str):
    #     try:
    #         payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    #         users = db.query(User).filter(User.username == payload["payload"]).first()
    #         return users
    #     except:
    #         return HTTPException(status_code=401, detail="Invalid token")

    @staticmethod
    def get_user(db: Session, user_id: int):
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_user_by_email(db: Session, email: str):
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def delete_user(db: Session, user_id: int):
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        db.delete(user)
        db.commit()
        return {"message": "User deleted successfully"}

    @staticmethod
    def get_all_users(db: Session):
        return db.query(User).all()



    @staticmethod
    def create_user(db: Session, user: UserCreate):
        if UserCRUD.get_user_by_email(db, user.email): # Проверяем существует ли пользователь
            raise HTTPException(status_code=400, detail="User already exists")

        # Создаем пользователя
        new_user = User(
            username=user.username,
            email=user.email,
            password=user.password
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Создаем портфель для пользователя
        new_portfolio = Portfolio(
            user_id=new_user.id,
            total_added_money=0,
            available_money=0
        )
        db.add(new_portfolio)
        db.commit()


        return new_user




