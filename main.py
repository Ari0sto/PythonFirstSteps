import time
from typing import Annotated
from fastapi import FastAPI, HTTPException, status, Query, Cookie, Form, Request, Depends, Response
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

# ИМПОРТЫ ДЛЯ БАЗЫ ДАННЫХ 
import models
from database import engine, SessionLocal
from schemas import BookCreate, BookResponse

# 1. Создание таблиц в БД
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Books API")

# 2. Функция для стартового заполнения БД
def init_db():
    db = SessionLocal()
    # Проверка на наличие данных в таблице
    if db.query(models.Book).count() == 0:
        print("База пуста. Добавляем стартовые книги...")
        default_books = [
            models.Book(title="White Fang", author="Jack London"),
            models.Book(title="1984", author="George Orwell"),
            models.Book(title="The Great Gatsby", author="F. Scott Fitzgerald")
        ]
        db.add_all(default_books)
        db.commit()
    db.close()

# Запуск заполнения при старте файла
init_db()

def get_db():
    db = SessionLocal()
    try:
        yield db 
    finally:
        db.close()

# MIDDLEWARE И FRONTEND

@app.middleware("http")
async def log_requests_and_add_time(request: Request, call_next):
    start_time = time.perf_counter()
    print(f"- Входящий запрос: {request.method} {request.url.path}")
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    print(f"- Ответ отправлен. Время обработки: {process_time:.4f} сек.\n")
    return response

users_db = []

@app.get("/register", response_class=HTMLResponse, tags=["Frontend"])
def get_register_page():
    html_content = """
    <html>
        <head>
            <title>Регистрация</title>
            <style>
                body { font-family: Arial; margin: 40px; }
                .form-container { width: 300px; padding: 20px; border: 1px solid #ccc; border-radius: 5px; }
                input { width: 100%; margin-bottom: 10px; padding: 8px; }
                button { width: 100%; padding: 10px; background-color: #28a745; color: white; border: none; cursor: pointer; }
                button:hover { background-color: #218838; }
            </style>
        </head>
        <body>
            <div class="form-container">
                <h2>Регистрация пользователя</h2>
                <form action="/register" method="post">
                    <label>Имя пользователя:</label>
                    <input type="text" name="username" required>
                    <label>Пароль:</label>
                    <input type="password" name="password" required>
                    <button type="submit">Зарегистрироваться</button>
                </form>
            </div>
        </body>
    </html>
    """
    return html_content

@app.post("/register", tags=["Users"])
def register_user(username: Annotated[str, Form()], password: Annotated[str, Form()]):
    for user in users_db:
        if user["username"] == username:
            raise HTTPException(status_code=400, detail="Пользователь уже существует")
    new_user = {"id": len(users_db) + 1, "username": username, "password": password}
    users_db.append(new_user)
    return {"message": f"Пользователь {username} успешно зарегистрирован!", "total_users": len(users_db)}


# ФРОНТЕНД ДЛЯ ВХОДА
@app.get("/login", response_class=HTMLResponse, tags=["Frontend"])
def get_login_page():
    html_content = """
    <html>
        <head>
            <title>Вход</title>
            <style>
                body { font-family: Arial; margin: 40px; }
                .form-container { width: 300px; padding: 20px; border: 1px solid #ccc; border-radius: 5px; }
                input { width: 100%; margin-bottom: 10px; padding: 8px; }
                button { width: 100%; padding: 10px; background-color: #007bff; color: white; border: none; cursor: pointer; }
                button:hover { background-color: #0056b3; }
            </style>
        </head>
        <body>
            <div class="form-container">
                <h2>Вход в систему</h2>
                <form action="/login" method="post">
                    <label>Имя пользователя:</label>
                    <input type="text" name="username" required>
                    <label>Пароль:</label>
                    <input type="password" name="password" required>
                    <button type="submit">Войти</button>
                </form>
            </div>
        </body>
    </html>
    """
    return html_content

# ОБРАБОТКА ВХОДА И ВЫДАЧА КУКИ
@app.post("/login", tags=["Users"])
def login_user(
    response: Response,
    username: Annotated[str, Form()], 
    password: Annotated[str, Form()]
):
    user_found = None
    for user in users_db:
        if user["username"] == username and user["password"] == password:
            user_found = user
            break
            
    if not user_found:
        raise HTTPException(status_code=400, detail="Неверное имя пользователя или пароль")
        
    fake_token = f"secret_token_of_{username}"
    
    response.set_cookie(key="session_token", value=fake_token, httponly=True)
    
    return {"message": f"Добро пожаловать, {username}! Куки успешно установлены."}

# МЕТОДЫ ДЛЯ КНИГ

@app.get("/books/search", response_model=list[BookResponse], status_code=status.HTTP_200_OK)
def search_books(
    title: Annotated[str | None, Query(min_length=3, max_length=50)] = None,
    db: Session = Depends(get_db) # <--- БД
):
    if not title:
        return []
    # Поиск по БД
    found_books = db.query(models.Book).filter(models.Book.title.ilike(f"%{title}%")).all()
    return found_books

@app.get("/books", response_model=list[BookResponse], status_code=status.HTTP_200_OK)
def get_all_books(
    session_token: Annotated[str | None, Cookie()] = None,
    db: Session = Depends(get_db)
):
    if session_token:
        print(f"--> Пользователь пришел с токеном: {session_token}")
    # Вытягиваем все записи из таблицы
    return db.query(models.Book).all()

@app.get("/books/{book_id}", response_model=BookResponse, status_code=status.HTTP_200_OK)
def get_book_by_id(book_id: int, db: Session = Depends(get_db)):
    # Поиск первой записи по ID
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return book

@app.post("/books", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
def create_book(book_data: BookCreate, db: Session = Depends(get_db)):
    # Создание объекта БД
    new_book = models.Book(title=book_data.title, author=book_data.author)
    db.add(new_book)
    db.commit() # Сохранение в файл
    db.refresh(new_book) # Обновляем объект, чтобы получить ID
    return new_book

@app.put("/books/{book_id}", response_model=BookResponse, status_code=status.HTTP_200_OK)
def update_book(book_id: int, book_data: BookCreate, db: Session = Depends(get_db)):
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    
    # Обновляем поля
    book.title = book_data.title
    book.author = book_data.author
    db.commit()
    db.refresh(book)
    return book

@app.delete("/books/{book_id}", status_code=status.HTTP_200_OK)
def delete_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    
    db.delete(book)
    db.commit()
    return {"message": "Book deleted"}