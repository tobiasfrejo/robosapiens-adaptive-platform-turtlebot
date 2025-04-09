from typing import Iterable
from .lola import LolaStream, lola_chain, lt, leq

Stream_or_float = LolaStream | float
Point = tuple[Stream_or_float, Stream_or_float]
Circle = tuple[Point, Stream_or_float]

def connect_polygon(corners):
    walls = []
    for i in range(len(corners)):
        j = (i - 1) % len(corners)
        walls.append((corners[i], corners[j]))
        # warn(f'({i}, {j}): {corners[i]}, {corners[j]}')
    return walls

def rotate_polygon(polygon:Iterable[Point], center_of_rotation:Point, angle:Stream_or_float):
    expressions: dict[LolaStream, str] = dict()
    corner_points = []

    for n, (x, y) in enumerate(polygon):
        rc = str(n)
        px = LolaStream(f'C{rc}X')
        py = LolaStream(f'C{rc}Y')
        expressions[px] = f'((({x}) * cos({angle})) - (({y}) * sin({angle}))) + {center_of_rotation[0]}'
        expressions[py] = f'((({x}) * sin({angle})) + (({y}) * cos({angle}))) + {center_of_rotation[1]}'
        corner_points.append((px, py))

    return expressions, corner_points

def circle_line_overlap(c: Circle, wall: tuple[Point, Point]):
    """Gives a lola expression to calculate if a circle overlaps with a line. Evaluates to true in case of collision.

    Args:
        c (Circle): _description_
        wall (tuple[Point, Point]): _description_

    Returns:
        str: Lola expression
    """
    (ax, ay), (bx, by) = wall
    (cx, cy), r = c

    denom = f"(((({bx})-({ax}))*(({bx})-({ax})))+((({by})-({ay}))*(({by})-({ay}))))"
    s  = f"(((({cx})-({ax}))*(({bx})-({ax})))+((({cy})-({ay}))*(({by})-({ay}))))/{denom}"
    t_num = f"(((({ax})-({cx}))*(({by})-({ay})))+((({cy})-({ay}))*(({bx})-({ax}))))"
    t2 = f"({t_num}*{t_num})/{denom}" 

    return lola_chain([
        lt('0.0', s),
        lt(s, '1.0'),
        lt(t2, f'({r})*({r})')
    ], '&&')

def point_in_circle(p: Point, c: Circle):
    """Gives a lola expression to calculate if a point is on the border of or inside a circle. Evaluates to true when in/on.

    Args:
        p (Point): _description_
        c (Circle): _description_

    Returns:
        _type_: _description_
    """
    px, py = p
    (cx, cy), r = c

    dx = f"(({px})-({cx}))"
    dy = f"(({py})-({cy}))"

    return leq(f"({dx}*{dx}) + ({dy}*{dy})", f"({r})*({r})")

def test_points_in_circles(ps: Iterable[Point], cs: Iterable[Circle]):
    point_streams: dict[int, list[LolaStream]] = dict()
    circle_streams: dict[int, list[LolaStream]] = dict()
    expressions: dict[LolaStream, str] = dict()

    for pn, p in enumerate(ps):
        if pn not in point_streams:
            point_streams[pn] = list()
        for cn, c in enumerate(cs):
            if cn not in circle_streams:
                circle_streams[cn] = list()

            stream = LolaStream(f'Point{pn}InCircle{cn}')
            point_streams[pn].append(stream)
            circle_streams[cn].append(stream)

            expressions[stream] = point_in_circle(p, c)
    
    return expressions, point_streams, circle_streams
