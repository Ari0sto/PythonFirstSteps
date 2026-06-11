from pydantic import BaseModel

# Схема для получения данных ОТ пользователя
class BookCreate(BaseModel):
    title: str
    author: str

# Схема для отправки данных ПОЛЬЗОВАТЕЛЮ 
class BookResponse(BookCreate):
    id: int

    class Config:
        from_attributes = True