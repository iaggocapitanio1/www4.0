import numpy
from geojson import Polygon


def create_polygon(x: float, y: float, width: float, height: float) -> Polygon:
    p1 = x, y
    p2 = x + width, y
    p3 = x + width, y + height
    p4 = x, y + height
    p5 = p1
    return Polygon([p1, p2, p3, p4, p5])


def normalized_corners(corners: dict, decimals=7):
    coord = corners.get('coordinates')
    x_max = max(coord, key=lambda point: point[0])[0]
    y_max = max(coord, key=lambda point: point[1])[1]
    return Polygon(numpy.round([[point[0]/x_max, point[1]/y_max] for point in coord], decimals=decimals).tolist())