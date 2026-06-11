from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# 1 Тест для получения всех книг
def test_get_all_books():
    response = client.get("/books")

    # Проверка статус кода
    assert response.status_code == 200
    # Проверка, что ответ - это список
    assert isinstance(response.json(), list)

# 2 Тест Поиска книги
def test_search_books():
    response = client.get("/books/search?title=1984")

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["title"] == "1984"

# 3 Тест Ошибка валидации при поиске (Корткий запрос)
def test_search_books_validation_error():
    response = client.get("/books/search?title=19")


    assert response.status_code == 422

# 4 Тест Регистрация пользователя
def test_register_user():
    response = client.post(
        "/register",
        data={"username": "testuser", "password": "testpass"}
    )

    assert response.status_code in (200, 400)

# 5 Тест Вход пользователя и установка куки
def test_login_user():
    # Сначала регистрируем пользователя (на случай, если его нет)
    client.post(
        "/register",
        data={"username": "testuser2", "password": "testpass2"}
    )

    # Теперь пробуем войти
    response = client.post(
        "/login",
        data={"username": "testuser2", "password": "testpass2"}
    )

    assert response.status_code == 200
    # Проверяем, что сервер выдал нам куку session_token
    assert "session_token" in response.cookies
