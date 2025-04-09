from itertools import chain
from dynamic_walls.lola import LolaSpecification, LolaStream, lola_chain
from dynamic_walls.turtlebot import tb3_corners, turtle_map, turtle_map_pillars
from dynamic_walls.geometry import rotate_polygon, connect_polygon, circle_line_overlap, test_points_in_circles
from dynamic_walls.pnpoly import pnpoly

spec = LolaSpecification()

x = LolaStream('x')
y = LolaStream('y')
a = LolaStream('a')

spec.inputs.append(LolaStream('Odometry'))
spec.add_expression(x, 'List.get(Odometry, 0)')
spec.add_expression(y, 'List.get(Odometry, 1)')
spec.add_expression(a, 'List.get(Odometry, 2)')

tb3_exprs, tb3_rotated_corners = rotate_polygon(tb3_corners, (x,y), a)

map_walls = connect_polygon(turtle_map)
obstacle_wall = connect_polygon([
    (-0.1, 2.1),
    (-0.1, 1.9),
    ( 0.1, 1.9),
    ( 0.1, 2.1),
])

wall_exprs, pnp = pnpoly(tb3_rotated_corners, map_walls + obstacle_wall)
pillars_expressions, pillar_point_streams, _ = test_points_in_circles(tb3_rotated_corners, turtle_map_pillars)

for k,v in chain.from_iterable((tb3_exprs.items(), wall_exprs.items(), pillars_expressions.items())):
    spec.add_expression(k,v)

in_map = LolaStream('InMap')
spec.add_expression(in_map, lola_chain(pnp, '&&'))

corner_collision_streams = []
for n,streams in pillar_point_streams.items():
    s = LolaStream(f'Corner{n}Collision')
    spec.add_expression(s, lola_chain(streams, '||'))
    corner_collision_streams.append(s)

any_pillar_collision = lola_chain(corner_collision_streams, '||')

spec.add_expression(LolaStream('Collision'), f"!{in_map} || ({any_pillar_collision})")

print(spec.get_specification_string())
spec.write_specification('walls2-redux2.lola')