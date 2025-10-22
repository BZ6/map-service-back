# app.py
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
from mock_users import MOCK_USERS

app = FastAPI(title="Auth API", version="1.0.0")

# Настройка CORS
origins = [
	"http://51.250.73.226:8000",
	"http://localhost:8000",
	"http://127.0.0.1:8000",
]

app.add_middleware(
	CORSMiddleware,
	allow_origins=origins,
	allow_credentials=True,
	allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
	allow_headers=["Content-Type"],
)

# Модели данных
class UserBase(BaseModel):
	name: str
	lastName: str
	login: str

class RegisterRequest(BaseModel):
	name: str
	lastName: str
	login: str
	password: str

class RegisterResponse(BaseModel):
	status: str
	user: UserBase

class LoginRequest(BaseModel):
	login: str
	password: str

class LoginResponse(BaseModel):
	status: str
	user: UserBase
	token: str

class ErrorResponse(BaseModel):
	status: str
	message: str

class EmailConfirmRequest(BaseModel):
	code: str

class EmailConfirmResponse(BaseModel):
	status: str
	code: str

class ExampleResponse(BaseModel):
	message: str

@app.get("/api/example", response_model=ExampleResponse)
async def example():
	return ExampleResponse(message="Hello from FastAPI!")

@app.post("/api/register", response_model=RegisterResponse, status_code=status.HTTP_200_OK)
async def register(register_data: RegisterRequest):
	# В реальном приложении здесь была бы обработка регистрации
	# (хеширование пароля, сохранение в БД и т.д.)

	# Возвращаем те же данные + статус успешной регистрации
	return RegisterResponse(
		status="success",
		user=UserBase(
			name=register_data.name,
			lastName=register_data.lastName,
			login=register_data.login
		)
	)

@app.post("/api/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(login_data: LoginRequest):
	login = login_data.login
	password = login_data.password

	if login not in MOCK_USERS:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Пользователь с таким логином не найден"
		)

	user = MOCK_USERS[login]

	if password != user['password']:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Неверный пароль"
		)

	# В реальном приложении здесь была бы проверка учетных данных
	# (поиск пользователя, проверка пароля и т.д.)

	return LoginResponse(
		status="success",
		user=UserBase(
			name=user['name'],
			lastName=user['lastName'],
			login=user['login']
		),
		token="dummy_token_for_example"
	)

@app.post("/api/emailConfirm", response_model=EmailConfirmResponse, status_code=status.HTTP_200_OK)
async def email_confirm(confirm_data: EmailConfirmRequest):
	return EmailConfirmResponse(
		status="success",
		code=confirm_data.code
	)

if __name__ == "__main__":
	import uvicorn
	uvicorn.run(app, host="0.0.0.0", port=5000)