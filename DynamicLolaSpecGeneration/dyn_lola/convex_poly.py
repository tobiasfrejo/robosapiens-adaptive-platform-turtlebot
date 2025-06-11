from typing import Iterable

from .lola import LolaStream, lola_chain, Expression, gt, lt
from .geometry import Point

def cpoly_check_wall(test_point: Point, wall: tuple[Point, Point], direction='clockwise') -> Expression:
    """
    for all walls when defined clockwise
    0 < (PosX-Ax)*(By-Ay) + (Ay-PosY)*(Bx-Ax)
    """

    assert direction in ['clockwise', 'counterclockwise']

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

    exp = Expression("((»PosX«)-(»Ax«))*((»By«)-(»Ay«)) + ((»Ay«)-(»PosY«))*((»Bx«)-(»Ax«))", stream_dict)

    if direction == 'clockwise':
        return Expression([
            lt('0.0', exp)
        ])
    else:
        return Expression([
            gt('0.0', exp)
        ])

def cpoly(test_points: Iterable[Point], polygons: Iterable[Iterable[tuple[Point, Point]]], stream_prefix:str="", direction='clockwise'):
    expressions: dict[LolaStream, Expression] = {}

    point_streams = [] # AND

    for i, point in enumerate(test_points):
        subpoly_checks = [] # OR

        for m, walls in enumerate(polygons):
            wall_checks = [cpoly_check_wall(point, wall, direction) for wall in walls]

            stream = LolaStream(f'{stream_prefix}P{i}inSubPoly{m}')
            expressions[stream] = lola_chain(wall_checks, '&&')
            subpoly_checks.append(stream)

        subpoly_expr = lola_chain(subpoly_checks, '||')
        subpoly_stream = LolaStream(f'{stream_prefix}P{i}inPoly')
        expressions[subpoly_stream] = subpoly_expr
        point_streams.append(subpoly_stream)

    return expressions, point_streams
