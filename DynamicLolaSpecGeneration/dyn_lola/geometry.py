from typing import Iterable
from .lola import LolaStream, lola_chain, lt, leq, Expression

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

def rotate_polygon(polygon:Iterable[Point], center_of_rotation:Point, angle:Stream_or_float, stream_prefix:str=""):
    expressions: dict[LolaStream, Expression] = dict()
    corner_points = []

    for n, (x, y) in enumerate(polygon):
        stream_dict = {'x': x, 'y': y, 'angle': angle, 'center_of_rotation0': center_of_rotation[0], 'center_of_rotation1': center_of_rotation[1]}
        rc = str(n)
        px = LolaStream(f'{stream_prefix}C{rc}X')
        py = LolaStream(f'{stream_prefix}C{rc}Y')
        expressions[px] = Expression('(((›x‹) * cos(›angle‹)) - ((›y‹) * sin(›angle‹))) + ›center_of_rotation0‹',stream_dict)
        expressions[py] = Expression('(((›x‹) * sin(›angle‹)) + ((›y‹) * cos(›angle‹))) + ›center_of_rotation1‹',stream_dict)
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
    
    stream_dict = {'ax': ax, 'ay': ay, 'bx': bx, 'by': by, 'cx': cx, 'cy': cy, 'r': r}

    denom = "((((›bx‹)-(›ax‹))*((›bx‹)-(›ax‹)))+(((›by‹)-(›ay‹))*((›by‹)-(›ay‹))))"
    s  = Expression(f"((((›cx‹)-(›ax‹))*((›bx‹)-(›ax‹)))+(((›cy‹)-(›ay‹))*((›by‹)-(›ay‹))))/{denom}", stream_dict)
    t_num = "((((›ax‹)-(›cx‹))*((›by‹)-(›ay‹)))+(((›cy‹)-(›ay‹))*((›bx‹)-(›ax‹))))"
    t2 = Expression(f"({t_num}*{t_num})/{denom}",stream_dict)

    return lola_chain([
        lt('0.0', s),
        lt(s, '1.0'),
        lt(t2, Expression(f'(›r‹)*(›r‹)',stream_dict)),
    ], '&&')

def test_circles_walls_overlaps(cs: Iterable[Circle], ws: Iterable[tuple[Point, Point]], stream_prefix:str=""):
    wall_streams: dict[int, list[LolaStream]] = dict()
    circle_streams: dict[int, list[LolaStream]] = dict()
    expressions: dict[LolaStream, Expression] = dict()

    for cn, c in enumerate(cs):
        if cn not in circle_streams:
            circle_streams[cn] = list()
        for wn, w in enumerate(ws):
            if wn not in wall_streams:
                wall_streams[wn] = list()
            
            stream = LolaStream(f'{stream_prefix}Circle{cn}CollidesWall{wn}')
            wall_streams[wn].append(stream)
            circle_streams[cn].append(stream)

            expressions[stream] = circle_line_overlap(c, w)

    return expressions, wall_streams, circle_streams

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
    stream_dict = {'px': px, 'py': py, 'cx': cx, 'cy': cy, 'r': r}

    dx = "((›px‹)-(›cx‹))"
    dy = "((›py‹)-(›cy‹))"
    r2 = "(›r‹)*(›r‹)"

    return leq(Expression(f"({dx}*{dx}) + ({dy}*{dy})", stream_dict), Expression(r2, stream_dict))

def test_points_in_circles(ps: Iterable[Point], cs: Iterable[Circle], stream_prefix:str=""):
    point_streams: dict[int, list[LolaStream]] = dict()
    circle_streams: dict[int, list[LolaStream]] = dict()
    expressions: dict[LolaStream, Expression] = dict()

    for pn, p in enumerate(ps):
        if pn not in point_streams:
            point_streams[pn] = list()
        for cn, c in enumerate(cs):
            if cn not in circle_streams:
                circle_streams[cn] = list()

            stream = LolaStream(f'{stream_prefix}Point{pn}InCircle{cn}')
            point_streams[pn].append(stream)
            circle_streams[cn].append(stream)

            expressions[stream] = point_in_circle(p, c)
    
    return expressions, point_streams, circle_streams