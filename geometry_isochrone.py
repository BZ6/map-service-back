from services.iso_service import isochrone_service


class Vector:
	"""Класс для работы с 2D векторами."""

	def __init__(self, x=0.0, y=0.0):
		self.x = float(x)
		self.y = float(y)

	def __repr__(self):
		return f"Vector({self.x}, {self.y})"

	def __str__(self):
		return f"({self.x}, {self.y})"

	# Арифметические операции
	def __add__(self, other):
		"""Сложение векторов."""
		return Vector(self.x + other.x, self.y + other.y)

	def __sub__(self, other):
		"""Вычитание векторов."""
		return Vector(self.x - other.x, self.y - other.y)

	def __mul__(self, scalar):
		"""Умножение вектора на скаляр."""
		return Vector(self.x * scalar, self.y * scalar)

	def __rmul__(self, scalar):
		"""Умножение скаляра на вектор."""
		return self.__mul__(scalar)

	def __truediv__(self, scalar):
		"""Деление вектора на скаляр."""
		if scalar == 0:
			raise ZeroDivisionError("Деление вектора на ноль")
		return Vector(self.x / scalar, self.y / scalar)

	def __neg__(self):
		"""Отрицательный вектор."""
		return Vector(-self.x, -self.y)

	def __ne__(self, other):
		"""Проверка на неравенство."""
		return not self.__eq__(other)

	# Векторные операции
	def dot(self, other):
		"""Скалярное произведение."""
		return self.x * other.x + self.y * other.y

	def cross(self, other):
		"""Векторное произведение (z-компонента в 3D)."""
		return self.x * other.y - self.y * other.x

	def length_squared(self):
		"""Квадрат длины вектора (быстрее, чем length())."""
		return self.x**2 + self.y**2

	def normalize(self):
		"""Нормализация вектора (единичный вектор)."""
		length = self.length()
		if length == 0:
			raise ValueError("Невозможно нормализовать нулевой вектор")
		return Vector(self.x / length, self.y / length)

	def distance_to(self, other):
		"""Расстояние до другого вектора (точки)."""
		return (self - other).length()

	def distance_to_squared(self, other):
		"""Квадрат расстояния (быстрее, чем distance_to)."""
		return (self - other).length_squared()

	def perpendicular(self):
		"""Перпендикулярный вектор (поворот на 90° против часовой стрелки)."""
		return Vector(-self.y, self.x)

class Triangle:
	"""Класс для работы с треугольниками из центра полигона."""

	def __init__(self, с, a, b):
		"""c это центр полигона"""
		self.c = с
		self.v0 = a - self.c
		self.v1 = b - self.c
		self.dot00 = self.v0.length_squared()
		self.dot11 = self.v1.length_squared()
		self.dot01 = self.v0.dot(self.v1)
		self.denom = self.dot00 * self.dot11 - self.dot01 * self.dot01

	def is_point_in_triangle_barycentric(self, p):
		"""
		Проверка принадлежности точки треугольнику
		с использованием барицентрических координат.
		"""
		v2 = p - self.c

		dot00 = self.dot00
		dot11 = self.dot11
		dot01 = self.dot01
		dot02 = self.v0.dot(v2)
		dot12 = self.v1.dot(v2)
		denom = self.denom

		# Вычисление барицентрических координат
		u = dot11 * dot02 - dot01 * dot12
		v = dot00 * dot12 - dot01 * dot02

		# Проверка условия
		return (u >= -1e-10) and (v >= -1e-10) and (u + v <= denom + 1e-10)

class Polygon:
	"""Класс для работы с полигонами."""

	def __init__(self, center, vectors):
		self.center = center
		self.triangles = [Triangle(center, vectors[i - 1], vectors[i]) for i in range(1, len(vectors))]
		self.triangles.append(Triangle(center, vectors[0], vectors[-1]))

	def is_point_in_polygon(self, p):
		"""Проверка принадлежности точки полигону."""
		is_in = False

		for t in self.triangles:
			is_in = is_in or t.is_point_in_triangle_barycentric(p)

		return is_in

def attraction_score_by_category(atractive_category: str):
	match atractive_category:
		case "railway_station": return 15
		case "business_center": return 10
		case "education": return 8
		case "pedestrian_zone": return 7
		case "park": return 6
		case "industrial": return -12
		case "wastewater_plant": return -15
		case "military": return -10
		case "power": return -8
		case _: raise ValueError("такая категория не поддерживается")

def calculate_attraction(polygon: Polygon, point: Vector, atractive_category: str):
	if polygon.is_point_in_polygon(point):
		return attraction_score_by_category(atractive_category)
	return 0

def calculate_attractions(polygon: Polygon, points: list[tuple[float, float, str]]):
	acc_score = 0
	for x, y, atractive_category in points:
		acc_score += calculate_attraction(polygon, Vector(x, y), atractive_category)

	return acc_score

async def build_isochrone_polygon(x: float, y: float, time: int = 7) -> Polygon:
	isochrones_data = await isochrone_service.calculate_isochrones([(x, y)], time)
	isochrone_polygon = isochrones_data[0]["polygon"]

	if isochrone_polygon["type"] == "MultiPolygon":
		raise ValueError("MultiPolygon не поддерживается")

	isochrone_polygon_vectors = [Vector(coordinate[0], coordinate[1]) for coordinate in isochrone_polygon["coordinates"][0]]

	return Polygon(Vector(x, y), isochrone_polygon_vectors)

async def calculate_attractions_by_category(centers: list[tuple[float, float]], points: list[tuple[float, float, str]]) -> list[tuple[float, float, int]]:
	result = []
	for x, y in centers:
		polygon = await build_isochrone_polygon(x, y)
		score = calculate_attractions(polygon, points)
		result.append(tuple(x, y, score))

	return result


def in_polygon_default():
	V = [
		Vector(5, 0),
		Vector(3, 4),
		Vector(-3, 4),
		Vector(-5, 0),
		Vector(-3, -4),
		Vector(3, -4)
	]
	C = Vector(0, 0)

	polygon = Polygon(C, V)
	return polygon.is_point_in_polygon(0, 6)

if __name__ == "__main__":
	in_triangle = in_polygon_default()
	print(in_triangle)
