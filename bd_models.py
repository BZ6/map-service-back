from sqlmodel import SQLModel, Field
from typing import Optional
from decimal import Decimal

class Build(SQLModel, table=True):
	__tablename__ = "builds"
	
	id: Optional[int] = Field(default=None, primary_key=True)
	name: Optional[str] = Field(default=None, max_length=255)
	category: Optional[str] = Field(default=None, max_length=100)
	opening_hours: Optional[str] = Field(default=None, max_length=150)
	website: Optional[str] = Field(default=None)
	phone: Optional[str] = Field(default=None, max_length=100)
	addr_street: Optional[str] = Field(default=None, max_length=255)
	addr_housenumber: Optional[str] = Field(default=None, max_length=100)
	geometry: Optional[str] = Field(default=None)
	longtitude: Optional[str] = Field(default=None)
	latitude: Optional[str] = Field(default=None)

class RoadNode(SQLModel, table=True):
	__tablename__ = "road_nodes"
	
	node_id: int = Field(primary_key=True)
	longtitude: Optional[Decimal] = Field(default=None, max_digits=20, decimal_places=8)
	latitude: Optional[Decimal] = Field(default=None, max_digits=20, decimal_places=8)

class RoadRib(SQLModel, table=True):
	__tablename__ = "road_ribs"
	
	id: Optional[int] = Field(default=None, primary_key=True)
	start_node_id: Optional[int] = Field(default=None, foreign_key="road_nodes.node_id")
	end_node_id: Optional[int] = Field(default=None, foreign_key="road_nodes.node_id")
	length: Optional[Decimal] = Field(default=None, max_digits=20, decimal_places=8)
	max_speed: Optional[str] = Field(default=None, max_length=30)
