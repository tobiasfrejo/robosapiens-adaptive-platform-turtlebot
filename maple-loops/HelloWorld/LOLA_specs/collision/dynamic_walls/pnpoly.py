from typing import Iterable

from .lola import LolaStream, lola_chain
from .geometry import Point

def pnpoly_check_wall(test_point: Point, wall: tuple[Point, Point]) -> str:
    """
    https://wrfranklin.org/Research/Short_Notes/pnpoly.html

    (Ay > Py  !=  By > Py) && !(By == Ay)
    &&  (Px  <  (Bx-Ax) * (Py-Ay) / (By-Ay) + Ax)
    """

    PosX, PosY = test_point
    Ax, Ay = wall[0]
    Bx, By = wall[1]

    return f"""\
if !(\
!({Ay} <= {PosY}) == !({By} <= {PosY})\
) && !({By} == {Ay}) \
&& !(\
((({Bx}) - ({Ax})) * (({PosY}) - ({Ay})) / (({By}) - ({Ay})) + ({Ax})) <= ({PosX})) \
then 1 \
else 0 \
"""

def pnpoly_check_walls(test_points: Iterable[Point], walls: Iterable[tuple[Point, Point]]):    
    expressions: dict[LolaStream, str] = {}
    point_streams: dict[int, list[LolaStream]] = {}

    for m, P in enumerate(test_points):
        wall_streams: list[LolaStream] = []
        for n, wall in enumerate(walls):
            stream = LolaStream(f'w{n}p{m}')
            wall_streams.append(stream)
            expressions[stream] = pnpoly_check_wall(P, wall)
        point_streams[m] = wall_streams
        
    return expressions, point_streams

def pnpoly(test_points: Iterable[Point], walls: Iterable[tuple[Point, Point]]):
    expressions, point_streams = pnpoly_check_walls(test_points, walls)

    points_in_polygon: list[LolaStream] = []
    for m,ps in point_streams.items():
        named_point_inside_polygon_stream = LolaStream(f'P{m}InPoly')
        expressions[named_point_inside_polygon_stream] = f"(({lola_chain(ps, '+')}) % 2) == 1"
        points_in_polygon.append(named_point_inside_polygon_stream)
    
    return expressions, points_in_polygon


