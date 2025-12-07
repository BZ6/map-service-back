# app.py
import math

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

from shapely.geometry import Polygon, Point
import rtree

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

        # Использование Лизиных методов
        polygons_with_ids = add_ids_to_polygons(polygons)

        if not polygons_with_ids:
            raise Exception("Нет полигонов для обработки")

        shapely_polygons = convert_to_shapely_polygons(polygons_with_ids)

        min_intersections = 2
        max_points = 30

        # пусть центры будут списком картежей с координатами
        centers_data = find_buffer_intersection_centers(
            polygons,
            min_intersections=min_intersections,
            max_points=max_points
        )

        if not centers_data:
            return PointsAndScoresResponse(status="success", points=[])
        # поменяйте как нужно чтобы получился список картежей с координатами и критериями (возможно один и тот же критерий для всехё)
        points_with_criteria = []
        for center in centers_data:
            lon, lat = center['coordinates']
            criteria_value = center['weight']
            points_with_criteria.append((lon, lat, criteria_value))

        result = await calculate_attractions_by_category(centers_data, points_with_criteria)
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

# Реализация Лизиных методов
def add_ids_to_polygons(polygons):
    """
    Добавляет id для полигонов, чтобы была возможность их потом идентифицировать
    """
    polygons_with_ids = []

    for i, polygon in enumerate(polygons):
        polygons_with_ids.append({
            'id': i + 1,
            'polygon': polygon,
            'points_count': len(polygon)
        })

    return polygons_with_ids

def convert_to_shapely_polygons(polygons_with_ids):
    """
        Конвертирует полигоны из формата списка точек в объекты shapely.Polygon.
        Shapely - это стандартная библиотека для геометрических операций в Python.
    """

    shapely_polygons = []
    invalid_count = 0

    for item in polygons_with_ids:
        polygon_id = item['id']
        raw_polygon = item['polygon']

        try:
            # Создаем shapely полигон из списка точек
            shapely_poly = Polygon(raw_polygon)

            if shapely_poly.is_valid:
                shapely_polygons.append({
                    'id': polygon_id,
                    'polygon': shapely_poly,
                    'bounds': shapely_poly.bounds,  # Bounds хранит четыре координаты: min_x, max_x, min_y, max_y
                    'area': shapely_poly.area
                })
            else:
                invalid_count += 1
        except Exception as e:
            invalid_count += 1
            raise Exception(f"Ошибка при создании полигона {polygon_id}: {e}")

    return shapely_polygons

def build_spatial_index(shapely_polygons):
    """
    Строит R-tree пространственный индекс.
    R-tree группирует объекты по их bounding boxes.
    Позволяет быстро находить объекты, которые МОГУТ пересекаться.
    """

    idx = rtree.index.Index()

    bounding_boxes = []

    for i, poly_data in enumerate(shapely_polygons):
        bbox = poly_data['bounds']

        idx.insert(i, bbox)

        bounding_boxes.append(bbox)

    return idx, bounding_boxes

def find_intersections_with_index(shapely_polygons, spatial_idx, bounding_boxes):
    """
    Поиск пересечений с использованием пространственного индекса.
    """

    intersections = {}
    checked_pairs = 0

    for i in range(len(shapely_polygons)):
        cur_poly_data = shapely_polygons[i]
        cur_poly = cur_poly_data['polygon']
        cur_id = cur_poly_data['id']
        cur_bbox = bounding_boxes[i]

        # Используем индекс: находим только те полигоны, чьи bounding boxes пересекаются с cur_box
        candidate_indices = list(spatial_idx.intersection(cur_bbox))

        for j in candidate_indices:
            if j <= i:
                continue

            other_poly_data = shapely_polygons[j]
            other_poly = other_poly_data['polygon']
            other_id = other_poly_data['id']

            checked_pairs += 1

            if cur_poly.intersects(other_poly):
                intersection = cur_poly.intersection(other_poly)
                if not intersection.is_empty:
                    intersections[(cur_id, other_id)] = intersection
    return intersections

def find_multi_intersections(intersections_dict):
    """Группирует центроиды попарных пересечений по координатам"""

    point_groups = {}

    for (id1, id2), intersection in intersections_dict.items():
        centroid = intersection.centroid

        rounded_x = round(centroid.x, 6)
        rounded_y = round(centroid.y, 6)
        key = (rounded_x, rounded_y)

        if key not in point_groups:
            point_groups[key] = set()

        point_groups[key].add(id1)
        point_groups[key].add(id2)

    return point_groups

def filter_points_by_intersections(point_groups, min_intersections=2):
    """Фильтрация точек по минимальному количеству пересечений"""

    filtered_points = []

    for (lon, lat), buffer_ids in point_groups.items():
        intersection_count = len(buffer_ids)

        if intersection_count >= min_intersections:
            filtered_points.append({
                'coordinates': [lon, lat],
                'weight': intersection_count,
                'buffer_ids': list(buffer_ids),
                'buffer_count': intersection_count
            })

    return filtered_points

def sort_and_limit_points(points, max_points=30):
    """Сортировка точек по количеству пересечений. Берет из них только ограниченное количество"""

    sorted_points = sorted(points, key=lambda p: p['weight'], reverse=True)
    result = sorted_points[:max_points]
    return result


def haversine_distance(lon1, lat1, lon2, lat2):
    R = 6371.0

    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = (math.sin(dlat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def cluster_points(points, max_points=30, cluster_distance_km=0.05):
    """
    Объединяет близко расположенные точки
    """

    if not points:
        return []

    sorted_points = sorted(points, key=lambda p: p['weight'], reverse=True)

    clustered = []
    used_indices = set()

    for i, main_point in enumerate(sorted_points):
        if i in used_indices:
            continue

        if len(clustered) >= max_points:
            break

        cluster_buffer_ids = set(main_point['buffer_ids'])

        close_points_indices = []
        for j, other_point in enumerate(sorted_points[i + 1:], start=i + 1):
            if j in used_indices:
                continue

            lon1, lat1 = main_point['coordinates']
            lon2, lat2 = other_point['coordinates']
            distance = haversine_distance(lon1, lat1, lon2, lat2)

            if distance <= cluster_distance_km:
                close_points_indices.append(j)
                cluster_buffer_ids.update(other_point['buffer_ids'])

        clustered_point = {
            'coordinates': main_point['coordinates'],
            'weight': len(cluster_buffer_ids),
            'buffer_ids': list(cluster_buffer_ids),
            'buffer_count': len(cluster_buffer_ids),
            'clustered_points': 1 + len(close_points_indices)
        }

        clustered.append(clustered_point)

        used_indices.add(i)
        for idx in close_points_indices:
            used_indices.add(idx)

    return clustered


def find_buffer_intersection_centers(polygons, min_intersections=2, max_points=30):
    """
    Находит точки пересечений буферов, где min_intersections минимальное количество пересекающихся буферов
    """
    if min_intersections < 2:
        min_intersections = 2

    if max_points < 1:
        max_points = 30

    if len(polygons) < 2:
        return []

    polygons_with_ids = add_ids_to_polygons(polygons)
    if not polygons_with_ids:
        return []

    shapely_polygons = convert_to_shapely_polygons(polygons_with_ids)
    if not shapely_polygons:
        return []

    spatial_idx, bboxes = build_spatial_index(shapely_polygons)
    intersections = find_intersections_with_index(shapely_polygons, spatial_idx, bboxes)
    if not intersections:
        return []

    point_groups = find_multi_intersections(intersections)
    filtered_points = filter_points_by_intersections(point_groups, min_intersections)

    if not filtered_points:
        return []

    clustered_points = cluster_points(filtered_points, max_points, cluster_distance_km=0.05)

    result_points = sort_and_limit_points(clustered_points, max_points)

    return result_points

