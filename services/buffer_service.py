import pandas as pd
import geopandas as gpd
from shapely.geometry import Point


def build_buffers_for_criteries(criteries, buffer_m: int = 500):
    """Получает список критериев и возвращает список буферов в виде координат."""

    rows = []
    for c in criteries:
        # обращаемся к словарю через ключи
        if c.get("longitude") is None or c.get("latitude") is None:
            continue

        # только is_antiattractive = False
        if not c.get("is_antiattractive", False):
            rows.append({
                "longitude": float(c["longitude"]),
                "latitude": float(c["latitude"])
            })

    if not rows:
        return []

    df = pd.DataFrame(rows)

    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df.longitude, df.latitude),
        crs="EPSG:4326"
    )

    gdf_m = gdf.to_crs(epsg=3857)
    gdf_m["buffer"] = gdf_m.geometry.buffer(buffer_m)

    # Преобразуем в список координат
    buffers = [
        [[x, y] for x, y in geom.exterior.coords]
        for geom in gdf_m["buffer"]
        if not geom.is_empty
    ]

    return buffers
