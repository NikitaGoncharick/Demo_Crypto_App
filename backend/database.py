# 🔗 Подключение к БД
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,declarative_base

# 🔗 Подключение к SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///./database.db" # SQLite не рекомендуется для production

# 🚀 Создаем движок БД
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False} # ✅ Разрешает использовать одно соединение из разных потоков
)

# 🎭 Фабрика сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) # autoflush=False - Изменения накапливаются и отправляются одной командой

# 🏗️ Базовый класс для моделей
Base = declarative_base()


# 🔄 Dependency для FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback() # Откат при ошибках и сохранение целостности данных 🔒
        raise
    finally:
        db.close() # Всегда закрываем соединение