from typing import Iterable

from .lola import LolaStream, lola_chain, Expression, gt, lif, not_eq
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
    stream_dict = {
        'PosX': PosX,
        'PosY': PosY,
        'Ax': Ax,
        'Ay': Ay,
        'Bx': Bx,
        'By': By
    }

    return Expression([
        lif(
            lola_chain([
                not_eq(
                    gt(Ay, PosY),
                    gt(By, PosY)
                ),
                not_eq(By, Ay),
                Expression("(((›Bx‹) - (›Ax‹)) * ((›PosY‹) - (›Ay‹)) / ((›By‹) - (›Ay‹)) + (›Ax‹)) <= (›PosX‹)", stream_dict)
            ], '&&'),
            Expression('1'),
            Expression('0')
        )
    ])

def pnpoly_check_walls(test_points: Iterable[Point], walls: Iterable[tuple[Point, Point]], stream_prefix:str=""):    
    expressions: dict[LolaStream, Expression] = {}
    point_streams: dict[int, list[LolaStream]] = {}

    for m, P in enumerate(test_points):
        wall_streams: list[LolaStream] = []
        for n, wall in enumerate(walls):
            stream = LolaStream(f'{stream_prefix}w{n}p{m}')
            wall_streams.append(stream)
            expressions[stream] = pnpoly_check_wall(P, wall)
        point_streams[m] = wall_streams
        
    return expressions, point_streams

def pnpoly(test_points: Iterable[Point], walls: Iterable[tuple[Point, Point]], stream_prefix:str=""):
    expressions, point_streams = pnpoly_check_walls(test_points, walls, stream_prefix)
    pnp_streams: dict[int, LolaStream] = {}

    for m,ps in point_streams.items():
        named_point_inside_polygon_stream = LolaStream(f'{stream_prefix}P{m}InPoly')
        mod_exp = Expression(['((', lola_chain(ps, '+'), ') % 2) == 1'])
        expressions[named_point_inside_polygon_stream] = mod_exp
        pnp_streams[m] = named_point_inside_polygon_stream
    
    return expressions, pnp_streams


