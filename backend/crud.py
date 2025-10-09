#⚡ Операции с БД (Create, Read, Update, Delete)

from sqlalchemy.orm import Session
from fastapi import HTTPException
from sqlalchemy.testing.suite.test_reflection import users

from models import User, Portfolio, Asset, Transaction
from schemas import UserCreate, AddMoney, TradeAsset
#from auth import verify_token


class UserCRUD:

    @staticmethod
    def log_in_user(db: Session, username: str, password: str):
        user = db.query(User).filter(User.username == username).first()
        if user and user.password == password:
            return user
        return None

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

        existing_user = db.query(User).filter(User.email == user.email).first()
        if existing_user:
            print("User already exists")
            return None # <- используем None для обработки eturn RedirectResponse в основном коде

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

        print("User created successfully")
        return new_user



class PortfolioCRUD:

    @staticmethod
    def get_portfolio_by_userd_id(db: Session, user_id: int):
        return db.query(Portfolio).filter(Portfolio.user_id == user_id).first()

    @staticmethod
    def get_user_portfolio_data(db: Session, user_id: int):

        portfolio = db.query(Portfolio).filter(Portfolio.user_id == user_id).first() #из таблицы portfolio Отфильтруй только те записи, где user_id равен переданному user_id
        if not portfolio:
            return None

        assets = db.query(Asset).filter(Asset.portfolio_id == portfolio.id).all()  #Отфильтруй активы, которые принадлежат найденному портфелю
        return {
            "portfolio": portfolio,
            "assets": assets
        }

    @staticmethod
    def add_money_to_portfolio(db: Session, user_id: int, amount: float):

        portfolio = db.query(Portfolio).filter(Portfolio.user_id == user_id).first()
        if not portfolio:
            return None

        portfolio.total_added_money += amount
        portfolio.available_money += amount

        db.commit()
        db.refresh(portfolio)

        return portfolio


