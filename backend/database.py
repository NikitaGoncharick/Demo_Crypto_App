# 🔗 Подключение к БД
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,declarative_base

# 🔗 Подключение к SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///./database.db"

# 🚀 Создаем движок БД
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# 🎭 Фабрика сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 🏗️ Базовый класс для моделей
Base = declarative_base()

# 🔄 Dependency для FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()