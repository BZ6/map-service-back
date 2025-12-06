# app.py
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from geometry_isochrone import calculate_attractions_by_category
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, distinct
from contextlib import asynccontextmanager

from schemas_iso import IsoRequest, IsoResponse, IsoPolygon, IsoPointAndScore, IsoScoreRequest, PointsAndScoresResponse
from services.iso_service import isochrone_service
from config import get_async_session, AsyncSessionLocal
from bd_models import Build

from mock_users import MOCK_USERS
from models import *
from bd_models import *
from config import get_async_session


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncSessionLocal() as session:
        try:
            await isochrone_service.initialize(session)
            print(f" Граф дорог успешно загружен в кэш")
        except Exception as e:
            print(f"Ошибка при загрузке графа дорог: {e}")
            import traceback
            traceback.print_exc()
    yield


app = FastAPI(title="Auth API", version="1.0.0", lifespan=lifespan)

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
@app.get("/api/builds/by-name/{name}", response_model=BuildsListResponse, status_code=status.HTTP_200_OK)
async def get_build_by_name(
		name: str,
		session: AsyncSession = Depends(get_async_session)
	):
	query = select(Build).where(Build.name == name)
	result = await session.execute(query)
	builds = result.scalars().all()

	return BuildsListResponse(
		status="success",
		builds=[build.model_dump() for build in builds]
	)

@app.get("/api/builds/names/by-category/{category}", response_model=BuildNamesResponse, status_code=status.HTTP_200_OK)
async def get_build_names_by_category(
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

@app.get("/api/builds/categories", response_model=CategoriesResponse, status_code=status.HTTP_200_OK)
async def get_all_categories(
    session: AsyncSession = Depends(get_async_session)
):
    query = select(distinct(Build.category)).where(
        Build.category.isnot(None)
    ).order_by(Build.category)

    result = await session.execute(query)
    categories = result.scalars().all()

    return CategoriesResponse(
        status="success",
        categories=categories
    )

@app.get("/api/builds/by-category/{category}", response_model=BuildsListResponse, status_code=status.HTTP_200_OK)
async def get_builds_by_category(
    category: str,
    session: AsyncSession = Depends(get_async_session)
):
    if category:
        query = select(Build).where(Build.category == category)
    else:
        query = select(Build)

    result = await session.execute(query)
    builds = result.scalars().all()

    builds_data = [build.model_dump() for build in builds]

    return BuildsListResponse(
        status="success",
        builds=builds_data
    )

@app.get("/api/builds/{id}", response_model=DateiledBuildResponse, status_code=status.HTTP_200_OK)
async def get_build_by_id(
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
async def get_road_node_by_id(
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
async def get_road_rib_by_id(
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

@app.post("/api/isochrones", response_model=IsoResponse)
async def isochrones_api(data: IsoRequest, session: AsyncSession = Depends(get_async_session)
):
    if data.time is None or data.time <= 0 or data.time > 15:
        raise HTTPException(status_code=400, detail="time must be >0 and <= 15")

    if not (data.points or data.byCategory or data.byName):
        raise HTTPException(status_code=400, detail="send points or byCategory or byName")

    start_coords = []

    if data.points:
        for p in data.points:
            start_coords.append((p.lon, p.lat))

    if data.byCategory:
        q = await session.execute(select(Build).where(Build.category == data.byCategory))
        for b in q.scalars().all():
            try:
                lon = float(b.longtitude.replace(",", "."))
                lat = float(b.latitude.replace(",", "."))
                start_coords.append((lon, lat))
            except:
                continue

    if data.byName:
        q = await session.execute(select(Build).where(Build.name == data.byName))
        for b in q.scalars().all():
            try:
                lon = float(b.longtitude.replace(",", "."))
                lat = float(b.latitude.replace(",", "."))
                start_coords.append((lon, lat))
            except:
                continue

    if not start_coords:
        raise HTTPException(status_code=404, detail="No start points found")
    
    try:
        isochrones_data = await isochrone_service.calculate_isochrones(
            points=start_coords,
            time_minutes=data.time
        )
        
        resp_polys = [
            IsoPolygon(minutes=item["minutes"], polygon=item["polygon"])
            for item in isochrones_data
        ]
        
        return IsoResponse(status="success", isochrones=resp_polys)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail="Service not initialized")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/isochrones/score", response_model=PointsAndScoresResponse)
async def isochrones_api(data: IsoScoreRequest, session: AsyncSession = Depends(get_async_session)
):
    if data.byName:
        raise HTTPException(status_code=400, detail="calculate score by name not suported yet")
    if not data.byCategory:
        raise HTTPException(status_code=400, detail="send category")

    try:
        # достаем из бд критерии и строения

        # тут идет логика Миши

        # тут идет логика Лизы

        # пусть центры будут списком картежей с координатами
        #centers =
        # поменяйте как нужно чтобы получился список картежей с координатами и критериями (возможно один и тот же критерий для всехё)
        points_with_critery = [tuple(point.x, point.y, critery) for point in points]

        result = await calculate_attractions_by_category(centers, points_with_critery)
        points = []
        for i in range(len(result)):
            if result[i][2] > 5:
                points.append(IsoPointAndScore(i + 1, result[i][0], result[i][1], result[i][2]))

        return PointsAndScoresResponse(status="success", points=points)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail="Service not initialized")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
	import uvicorn
	uvicorn.run(app, host="0.0.0.0", port=5000)

