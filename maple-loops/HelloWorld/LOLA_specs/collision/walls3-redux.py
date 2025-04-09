from itertools import chain
from dynamic_walls.lola import LolaSpecification, LolaStream, lola_chain
from dynamic_walls.turtlebot import tb3_corners, turtle_map, turtle_map_pillars
from dynamic_walls.geometry import rotate_polygon, connect_polygon, test_circles_walls_overlaps
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

# map_walls = connect_polygon(turtle_map)
# obstacle_wall = connect_polygon([
#     (-0.1, 2.1),
#     (-0.1, 1.9),
#     ( 0.1, 1.9),
#     ( 0.1, 2.1),
# ])

world_points = turtle_map + [
    (-0.1, 2.1),
    (-0.1, 1.9),
    ( 0.1, 1.9),
    ( 0.1, 2.1),
] + list(map(lambda p: p[0], turtle_map_pillars))

tb3_edges = connect_polygon(tb3_rotated_corners)

wall_exprs, pnp = pnpoly(world_points, tb3_edges)
pillars_expressions, _, pillar_point_streams = test_circles_walls_overlaps(turtle_map_pillars, tb3_edges)

for k,v in chain.from_iterable((tb3_exprs.items(), wall_exprs.items(), pillars_expressions.items())):
    spec.add_expression(k,v)

corner_collision = LolaStream('PointCollision')
spec.add_expression(corner_collision, lola_chain(pnp, '||'))

pillar_collision_streams = []
for n,streams in pillar_point_streams.items():
    s = LolaStream(f'Pillar{n}Collision')
    spec.add_expression(s, lola_chain(streams, '||'))
    pillar_collision_streams.append(s)

any_pillar_collision = lola_chain(pillar_collision_streams, '||')

spec.add_expression(LolaStream('Collision'), f"{corner_collision} || ({any_pillar_collision})")

print(spec.get_specification_string())
spec.write_specification('walls3-redux.lola')
