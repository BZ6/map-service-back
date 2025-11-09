from pydantic import BaseModel
from typing import Dict, Any, Optional, List

# Модели данных
class UserBase(BaseModel):
	name: str
	lastName: str
	login: str

class BuildBase(BaseModel):
	id: str
	name: str
	category: str
	opening_hours: str

class DateiledBuildBase(BaseModel):
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

class BuildResponse(BaseModel):
	status: str
	build: BuildBase

class DateiledBuildResponse(BaseModel):
	status: str
	build: DateiledBuildBase
