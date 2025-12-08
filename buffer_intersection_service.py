import math
from shapely.geometry import Polygon
import rtree

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
    """
    Группирует центроиды попарных пересечений по координатам
    """

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
    """
    Фильтрация точек по минимальному количеству пересечений
    """

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
    """
    Сортировка точек по количеству пересечений. Берет из них только ограниченное количество
    """

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

