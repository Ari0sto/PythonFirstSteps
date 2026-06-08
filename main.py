import time
from typing import Annotated
from fastapi import FastAPI, HTTPException, status, Query, Cookie, Form, Request
from fastapi.responses import HTMLResponse
from schemas import BookCreate

app = FastAPI(title="Books API")

# Middleware для логирования запросов

@app.middleware("http")
async def log_requests_and_add_time(request: Request, call_next):
    # 1. Запись времени до того, как запрос пойдет дальше
    start_time = time.perf_counter()
    
    # 2. Вывод информации о входящем запросе в терминал
    print(f"- Входящий запрос: {request.method} {request.url.path}")
    
    # 3. Передача запроса в функции
    response = await call_next(request)
    
    # 4. Запрос вернулся. подсчет, сколько времени прошло
    process_time = time.perf_counter() - start_time
    
    # 5. Добавляем это время в заголовки ответа и выводим в лог
    response.headers["X-Process-Time"] = str(process_time)
    print(f"- Ответ отправлен. Время обработки: {process_time:.4f} сек.\n")
    
    return response

# Временные базы данных
books_db = [
    {
        "id": 1,
        "title": "White Fang",
        "author": "Jack London"
    }
]

users_db = []

# Frontend
@app.get("/register", response_class=HTMLResponse, tags=["Frontend"])
def get_register_page():
    html_content =   """
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

# Обработка данных из формы
@app.post("/register", tags=["Users"])
def register_user(
    username: Annotated[str, Form()],
    password: Annotated[str, Form()]
):
    # проверка на наличие пользователя
    for user in users_db:
        if user["username"] == username:
            raise HTTPException(status_code=400, detail="Пользователь уже существует")

    # Создание нового пользователя
    new_user = {
        "id": len(users_db) + 1,
        "username": username,
        "password": password
    }
    users_db.append(new_user)

    # Вывод информации о пользователе
    return {
        "message": f"Пользователь {username} успешно зарегистрирован!",
        "total_users": len(users_db)
    }

@app.get("/books/search", status_code=status.HTTP_200_OK)
def search_books(
    # Вот тут Валидация
    title: Annotated[
        str | None, # Параметр или строка или None
        Query(
            min_length=3, # Мин 3 символа
            max_length=50, # Макс 50 символов
            description="Введите часть названия книги для поиска (от 3 до 50 символов)",
        )
    ] = None # None делает параметр необязательным
):
   
    if not title:
        return []
        
    found_books = [book for book in books_db if title.lower() in book["title"].lower()]
    return found_books


# GET
@app.get("/books", status_code=status.HTTP_200_OK)
def get_all_books(
    # параметр куки
    session_token: Annotated[
        str | None, 
        Cookie(description="Токен сессии пользователя")
    ] = None
):

# Просто для демонстрации если куки есть, вывод в консоль
    if session_token:
        print(f"--> Токен пользователя: {session_token}")
    else:
        print("--> Токена нет")
    return books_db

# GET by ID
@app.get("/books/{book_id}", status_code=status.HTTP_200_OK)
def get_book_by_id(book_id: int):
    for book in books_db:
        if book["id"] == book_id:
            return book
    # Если цикл завершился и книга не найдена,404
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

# POST
# При создании ресурса  201 Created
@app.post("/books", status_code=status.HTTP_201_CREATED)
def create_book(book_data: BookCreate):
    new_id = 1 if not books_db else max(b["id"] for b in books_db) + 1

    new_book = {
        "id": new_id,
        **book_data.model_dump() 
    }

    books_db.append(new_book)
    return new_book

# PUT (UPDATE)
@app.put("/books/{book_id}", status_code=status.HTTP_200_OK)
def update_book(book_id: int, book_data: BookCreate):
    for book in books_db:
        if book["id"] == book_id:
            book["title"] = book_data.title
            book["author"] = book_data.author
            return book
            
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

# DELETE
@app.delete("/books/{book_id}", status_code=status.HTTP_200_OK)
def delete_book(book_id: int):
    for i, book in enumerate(books_db):
        if book["id"] == book_id:
            books_db.pop(i)
            return {"message": "Book deleted"}
            
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")