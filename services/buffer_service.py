import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon, MultiPolygon


def build_buffers_for_criteries(criteries, buffer_m: int = 500):
    """Строит буфер 500 м для каждой точки и возвращает список полигонов из координат в EPSG:4326."""

    rows = []
    for c in criteries:
        lon = c.get("longitude")
        lat = c.get("latitude")

        if lon is None or lat is None:
            continue

        # только is_antiattractive = False
        if not c.get("is_antiattractive", False):
            rows.append({"longitude": float(lon), "latitude": float(lat)})

    if not rows:
        return []

    df = pd.DataFrame(rows)

    # Создаем GeoDataFrame в WGS84
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df.longitude, df.latitude),
        crs="EPSG:4326"
    )

    # Перевод в метры
    gdf_m = gdf.to_crs(epsg=3857)

    # Строим буфер (в метрах)
    gdf_m["buffer"] = gdf_m.geometry.buffer(buffer_m)

    # Возвращаем в WGS84
    gdf_buffer = gdf_m.set_geometry("buffer").to_crs(epsg=4326)

    # Преобразуем каждый буфер в список координат
    buffers = []

    for geom in gdf_buffer.geometry:
        if geom.is_empty:
            continue

        if isinstance(geom, Polygon):
            buffers.append([[x, y] for x, y in geom.exterior.coords])

        elif isinstance(geom, MultiPolygon):
            # Берем крупнейший полигон (обычно единственный)
            largest = max(geom.geoms, key=lambda g: g.area)
            buffers.append([[x, y] for x, y in largest.exterior.coords])

    return buffers