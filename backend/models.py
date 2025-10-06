# Описание структуры таблиц в базе данных

from sqlalchemy import ForeignKey
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship

from  database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    email = Column(String, unique=True, index=True)
    portfolio = relationship("Portfolio", back_populates="user")

class Portfolio(Base):
    __tablename__ = "portfolio"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    total_added_money = Column(Float, default=0)
    available_money = Column(Float, default=0)

    user = relationship("User", back_populates="portfolio")
    assets = relationship("Asset", back_populates="portfolio")
    transactions = relationship("Transaction", back_populates="portfolio")

class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolio.id"))
    sumbol = Column(String)
    quantity = Column(Float)
    portfolio = relationship("Portfolio", back_populates="assets")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolio.id"))
    transaction_type = Column(String)
    symbol = Column(String)
    quantity = Column(Float)
    price = Column(Float)
    date = Column(String)

    portfolio = relationship("Portfolio", back_populates="transactions")