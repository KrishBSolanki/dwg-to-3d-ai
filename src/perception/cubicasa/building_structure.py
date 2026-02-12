from dataclasses import dataclass, field
from typing import List, Tuple
from shapely.geometry import Polygon, LineString

Point2D = Tuple[float, float]


@dataclass
class Wall:
    id: int
    centerline: LineString
    thickness: float
    height: float
    is_exterior: bool = False


@dataclass
class Door:
    wall_id: int
    position: float  # distance along wall
    width: float
    height: float


@dataclass
class Window:
    wall_id: int
    position: float
    width: float
    height: float
    sill_height: float


@dataclass
class Room:
    class_id: int
    polygon: Polygon


@dataclass
class BuildingStructure:
    walls: List[Wall] = field(default_factory=list)
    rooms: List[Room] = field(default_factory=list)
    doors: List[Door] = field(default_factory=list)
    windows: List[Window] = field(default_factory=list)
