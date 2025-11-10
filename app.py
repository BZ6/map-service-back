# app.py
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, distinct

from mock_category_build import CATEGORIES, BUILDS_BY_CATEGORY
from mock_users import MOCK_USERS
from models import *
from bd_models import *
from config import get_async_session

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

# CRUDошлепство в рамках задач
@app.get("/api/builds/by-name/{name}", response_model=BuildResponse, status_code=status.HTTP_200_OK)
async def build_by_name(
		name: str,
		session: AsyncSession = Depends(get_async_session)
	):
	query = select(Build).where(Build.name == name)
	result = await session.execute(query)
	build = result.scalars().first()

	if not build:
		raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Building not found")

	return BuildResponse(
		status="success",
		build=build.model_dump()
	)

@app.get("/api/builds/names/by-category/{category}", response_model=BuildNamesResponse, status_code=status.HTTP_200_OK)
async def build_names_by_type(
		category: str,
		session: AsyncSession = Depends(get_async_session)
	):
	query = select(distinct(Build.name)).where(
		(Build.category == category) & 
		(Build.name.isnot(None))
	).order_by(Build.name)
	result = await session.execute(query)
	names = result.scalars().all()
	
	return BuildNamesResponse(
		status="success",
		names=names
	)

@app.get("/api/builds/categories", response_model=dict)
async def get_all_categories():
	return {'categories': CATEGORIES}

@app.get("/api/builds/by-category/{category}", response_model=dict)
async def get_builds_by_category(category: str):
	return {'builds': [build for build in BUILDS_BY_CATEGORY if build['category'] == category]}

@app.get("/api/builds/{id}", response_model=DateiledBuildResponse, status_code=status.HTTP_200_OK)
async def build_by_id(
		id: str,
		session: AsyncSession = Depends(get_async_session)
	):
	try:
		build_id = int(id)
	except ValueError:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ID format")

	build = await session.get(Build, build_id)
	if not build:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Build not found")
	return DateiledBuildResponse(
		status="success",
		build=build.model_dump()
	)

@app.get("/api/road/node/{id}", response_model=RoadNodeResponse, status_code=status.HTTP_200_OK)
async def road_node_by_id(
		id: str,
		session: AsyncSession = Depends(get_async_session)
	):
	try:
		node_id = int(id)
	except ValueError:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ID format")

	node = await session.get(RoadNode, node_id)
	if not node:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Road node not found")
	return RoadNodeResponse(
		status="success",
		road_node=node.model_dump()
	)

@app.get("/api/road/rib/{id}", response_model=RoadRibResponse, status_code=status.HTTP_200_OK)
async def road_rib_by_id(
		id: str,
		session: AsyncSession = Depends(get_async_session)
	):
	try:
		rib_id = int(id)
	except ValueError:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ID format")

	rib = await session.get(RoadRib, rib_id)
	if not rib:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Road rib not found")
	return RoadRibResponse(
		status="success",
		road_rib=rib.model_dump()
	)

if __name__ == "__main__":
	import uvicorn
	uvicorn.run(app, host="0.0.0.0", port=5000)