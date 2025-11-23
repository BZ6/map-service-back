from unicodedata import category

from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from decimal import Decimal

# Модели данных
class UserBase(BaseModel):
	name: str
	lastName: str
	login: str

class BuildBase(BaseModel):
	id: int
	name: Optional[str] = None
	category: Optional[str] = None
	opening_hours: Optional[str] = None
	website: Optional[str] = None
	phone: Optional[str] = None
	addr_street: Optional[str] = None
	addr_housenumber: Optional[str] = None
	geometry: Optional[str] = None
	longtitude: Optional[str] = None
	latitude: Optional[str] = None

class RoadNodeBase(BaseModel):
	node_id: int
	longtitude: Optional[Decimal] = None
	latitude: Optional[Decimal] = None

class RoadRibBase(BaseModel):
	id: int
	start_node_id: Optional[int] = None
	end_node_id: Optional[int] = None
	length: Optional[Decimal] = None
	max_speed: Optional[str] = None

# Модели запроса и ответа
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

# CRUDошлепство в рамках задач
class BuildNamesResponse(BaseModel):
	status: str
	names: list[str]

class CategoriesResponse(BaseModel):
    status: str
    categories: list[str]

class BuildsListResponse(BaseModel):
    status: str
    builds: list[BuildBase]

class BuildResponse(BaseModel):
	status: str
	build: BuildBase

class DateiledBuildResponse(BaseModel):
	status: str
	build: BuildBase

class RoadNodeResponse(BaseModel):
	status: str
	road_node: RoadNodeBase

class RoadRibResponse(BaseModel):
	status: str
	road_rib: RoadRibBase
