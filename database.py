from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Путь к БД
SQLALCHEMY_DATABASE_URL = "sqlite:///./books.db"

# Создание движка БД
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# класс фабрики сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# базовый класс для моделей
Base = declarative_base()