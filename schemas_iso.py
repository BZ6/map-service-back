from pydantic import BaseModel, conlist, confloat, constr
from typing import List, Optional
from typing import Dict, List, Any

class IsoPoint(BaseModel):
    lat: float
    lon: float

class IsoPolygon(BaseModel):
    minutes: int
    polygon: Dict[str, Any]  

class IsoRequest(BaseModel):
    time: int
    points: Optional[List[IsoPoint]] = None
    byCategory: Optional[str] = None
    byName: Optional[str] = None

class IsoResponse(BaseModel):
    status: str
    isochrones: List[IsoPolygon]


