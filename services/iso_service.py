import asyncio
from typing import List, Tuple, Optional, Dict, Any
import networkx as nx
from shapely.ops import unary_union
from shapely.geometry import LineString, Point, mapping
import geopandas as gpd
import numpy as np
from scipy.spatial import cKDTree

from bd_models import RoadNode, RoadRib
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

WALKING_SPEED_M_PER_MIN = 80.0  # 80 метров/мин
BUFFER_METERS = 50  # ширина буфера вокруг дорог


class IsochroneService:
    def __init__(self):
        self._graph: Optional[nx.Graph] = None
        self._initialized = False
    
    async def initialize(self, session: AsyncSession):
        if self._initialized:
            return
        self._graph = await self._build_graph_from_db(session)
        self._init_graph_attributes()
        self._initialized = True
  
    async def _build_graph_from_db(self, session: AsyncSession) -> nx.Graph:

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
    
    def _init_graph_attributes(self):
        if self._graph is None:
            return
        
        node_ids = list(self._graph.nodes)
        coords = [(self._graph.nodes[nid]['lon'], self._graph.nodes[nid]['lat']) 
                  for nid in node_ids]
        arr = np.array(coords)
        
        if len(arr) > 0:
            kdtree = cKDTree(arr)
            self._graph.kdtree = kdtree
            self._graph.node_index_to_id = node_ids
            self._graph.node_pos = {nid: (lon, lat) for nid, (lon, lat) in zip(node_ids, coords)}
        else:
            self._graph.kdtree = None
            self._graph.node_index_to_id = []
            self._graph.node_pos = {}
    
    def _nearest_node_kdtree(self, lon: float, lat: float) -> Optional[int]:
        if self._graph is None or not hasattr(self._graph, "kdtree") or self._graph.kdtree is None:
            return None
        dist, idx = self._graph.kdtree.query([lon, lat], k=1)
        return self._graph.node_index_to_id[int(idx)]
    
    def _build_isochrones_from_graph(self, start_nodes: List[int], time_min: int):
        """Построение изохрон из графа"""
        if self._graph is None:
            return []
        
        lengths = nx.multi_source_dijkstra_path_length(
            self._graph, 
            sources=start_nodes, 
            weight='time'
        )
        reachable_nodes = {nid for nid, t in lengths.items() if t <= time_min}
        
        if not reachable_nodes:
            return []
        
        lines = []
        for u, v, data in self._graph.edges(data=True):
            if u in reachable_nodes or v in reachable_nodes:
                udata = self._graph.nodes[u]
                vdata = self._graph.nodes[v]
                lines.append(LineString([(udata['lon'], udata['lat']), 
                                         (vdata['lon'], vdata['lat'])]))
        
        if not lines:
            points = [Point(self._graph.nodes[n]['lon'], self._graph.nodes[n]['lat']) 
                      for n in reachable_nodes]
            geom = unary_union([p.buffer(0.0005) for p in points])
            return [(time_min, mapping(geom))]
        
        gdf = gpd.GeoSeries(lines, crs="EPSG:4326")
        gdf_proj = gdf.to_crs(epsg=3857)
        buffered = [geom.buffer(BUFFER_METERS) for geom in gdf_proj.geometry]
        unioned = unary_union(buffered)
        joined = gpd.GeoSeries([unioned], crs="EPSG:3857").to_crs(epsg=4326).iloc[0]
        return [(time_min, mapping(joined))]
    
    async def calculate_isochrones(
        self,
        points: List[Tuple[float, float]],
        time_minutes: int
    ) -> List[Dict[str, Any]]:

        if not self._initialized:
            raise RuntimeError("IsochroneService не инициализирован. Запустите initialize() при старте приложения.")
        
        if time_minutes <= 0 or time_minutes > 15:
            raise ValueError("Время должно быть >0 и <= 15 минут")

        start_nodes = set()
        for lon, lat in points:
            nid = self._nearest_node_kdtree(lon, lat)
            if nid:
                start_nodes.add(nid)
        
        if not start_nodes:
            raise ValueError("Не найдены ближайшие узлы дорожной сети")

        results = self._build_isochrones_from_graph(list(start_nodes), time_minutes)

        isochrones = []
        for minutes, geom in results:
            if hasattr(geom, "geom_type"):
                geom = mapping(geom)
            isochrones.append({
                "minutes": minutes,
                "polygon": geom
            })
        
        return isochrones

isochrone_service = IsochroneService()