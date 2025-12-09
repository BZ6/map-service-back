from typing import List
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from bd_models import Criteria


async def get_all_criteries(session: AsyncSession) -> List[Criteria]:
    """Возвращает все объекты таблицы criteries."""
    result = await session.execute(select(Criteria))
    return result.scalars().all()

async def get_all_criteries_light(session: AsyncSession) -> list[dict]:
    q = select(
        Criteria.id,
        Criteria.longitude,
        Criteria.latitude,
        Criteria.category,
        Criteria.is_antiattractive
    )
    result = await session.execute(q)
    rows = result.mappings().all()

    # Преобразуем RowMapping в dict с float
    criteries = []
    for row in rows:
        criteries.append({
            "id": row["id"],
            "longitude": float(row["longitude"]) if row["longitude"] is not None else None,
            "latitude": float(row["latitude"]) if row["latitude"] is not None else None,
            "category": row["category"],
            "is_antiattractive": row["is_antiattractive"],
        })

    return criteries