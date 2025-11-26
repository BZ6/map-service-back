import asyncio
from typing import List, Tuple, Optional
import networkx as nx
from shapely.ops import unary_union
from shapely.geometry import LineString, Point, mapping
import geopandas as gpd
import numpy as np
from scipy.spatial import cKDTree

WALKING_SPEED_M_PER_MIN = 80.0  # 80 метров/мин
BUFFER_METERS = 50  # ширина буфера вокруг дорог

_graph_lock = asyncio.Lock()
_GRAPH = None

from bd_models import RoadNode, RoadRib, Build 
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession


async def build_graph_from_db(session: AsyncSession) -> nx.Graph:
    G = nx.Graph()

    q = await session.execute(select(RoadNode))
    nodes = q.scalars().all()
    for n in nodes:
        try:
            lon = float(n.longtitude)
            lat = float(n.latitude)
        except Exception:
            continue
        G.add_node(n.node_id, lon=lon, lat=lat)

    q = await session.execute(select(RoadRib))
    ribs = q.scalars().all()
    for r in ribs:
        try:
            length = float(r.length)
        except Exception:
            continue
        time_min = length / WALKING_SPEED_M_PER_MIN
        if r.start_node_id in G.nodes and r.end_node_id in G.nodes:
            G.add_edge(r.start_node_id, r.end_node_id,
                       length=length,
                       time=time_min)
    return G


async def get_graph_cached(session: AsyncSession) -> nx.Graph:
    """
    Lazy-load граф и кэшировать в памяти. Использовать asyncio.Lock чтобы избежать гонок.
    """
    global _GRAPH
    if _GRAPH is not None:
        return _GRAPH

    async with _graph_lock:
        if _GRAPH is None:
            G = await build_graph_from_db(session)

            node_ids = list(G.nodes)
            coords = [(G.nodes[nid]['lon'], G.nodes[nid]['lat']) for nid in node_ids]
            arr = np.array(coords)
            if len(arr) > 0:
                kdtree = cKDTree(arr)
                node_index_to_id = node_ids
                node_pos = {nid: (lon, lat) for nid, (lon, lat) in zip(node_ids, coords)}
            else:
                kdtree = None
                node_index_to_id = []
                node_pos = {}

            G.kdtree = kdtree
            G.node_index_to_id = node_index_to_id
            G.node_pos = node_pos

            _GRAPH = G

    return _GRAPH


def nearest_node_kdtree(G: nx.Graph, lon: float, lat: float) -> Optional[int]:
    """
    Использовать KD-tree, хранящийся в графе. Возвращает id ближайшего узла.
    """
    if not hasattr(G, "kdtree") or G.kdtree is None:
        return None
    dist, idx = G.kdtree.query([lon, lat], k=1)
    return G.node_index_to_id[int(idx)]


def build_isochrones_from_graph(G: nx.Graph, start_nodes: List[int], time_min: int):
    lengths = nx.multi_source_dijkstra_path_length(G, sources=start_nodes, weight='time')
    reachable_nodes = {nid for nid, t in lengths.items() if t <= time_min}
    if not reachable_nodes:
        return []

    lines = []
    for u, v, data in G.edges(data=True):
        if u in reachable_nodes or v in reachable_nodes:
            udata = G.nodes[u]
            vdata = G.nodes[v]
            lines.append(LineString([(udata['lon'], udata['lat']), (vdata['lon'], vdata['lat'])]))

    if not lines:
        points = [Point(G.nodes[n]['lon'], G.nodes[n]['lat']) for n in reachable_nodes]
        geom = unary_union([p.buffer(0.0005) for p in points])
        return [(time_min, mapping(geom))]

    gdf = gpd.GeoSeries(lines, crs="EPSG:4326")
    gdf_proj = gdf.to_crs(epsg=3857)
    buffered = [geom.buffer(BUFFER_METERS) for geom in gdf_proj.geometry]
    unioned = unary_union(buffered)
    joined = gpd.GeoSeries([unioned], crs="EPSG:3857").to_crs(epsg=4326).iloc[0]
    return [(time_min, mapping(joined))]
