from itertools import chain
from dyn_lola.lola import LolaSpecification, LolaStream, lola_chain, Expression
from dyn_lola.shapes import turtlebot
from dyn_lola.geometry import rotate_polygon, connect_polygon, test_circles_walls_overlaps
from dyn_lola.pnpoly import pnpoly

spec = LolaSpecification()

x = LolaStream('x')
y = LolaStream('y')
a = LolaStream('a')

spec.inputs.append(LolaStream('Odometry'))
spec.add_expression(x, Expression('List.get(Odometry, 0)'), keep_on_prune=True)
spec.add_expression(y, Expression('List.get(Odometry, 1)'), keep_on_prune=True)
spec.add_expression(a, Expression('List.get(Odometry, 2)'), keep_on_prune=True)

tb3_exprs, tb3_rotated_corners = rotate_polygon(turtlebot.tb3_corners_offset(0.01), (x,y), a)

# map_walls = connect_polygon(turtle_map)
# obstacle_wall = connect_polygon([
#     (-0.1, 2.1),
#     (-0.1, 1.9),
#     ( 0.1, 1.9),
#     ( 0.1, 2.1),
# ])

world_points = turtlebot.turtle_map + [
    (-0.1, 2.1),
    (-0.1, 1.9),
    ( 0.1, 1.9),
    ( 0.1, 2.1),
] + list(map(lambda p: p[0], turtlebot.turtle_map_pillars))

tb3_edges = connect_polygon(tb3_rotated_corners)

wall_exprs, pnp = pnpoly(world_points, tb3_edges)
pillars_expressions, _, pillar_point_streams = test_circles_walls_overlaps(turtlebot.turtle_map_pillars, tb3_edges)

for k,v in chain.from_iterable((tb3_exprs.items(), wall_exprs.items(), pillars_expressions.items())):
    spec.add_expression(k,v)

corner_collision = LolaStream('PointCollision')
spec.add_expression(corner_collision, lola_chain(pnp, '||'))

pillar_collision_streams = []
for n,streams in pillar_point_streams.items():
    s = LolaStream(f'Pillar{n}Collision')
    spec.add_expression(s, lola_chain(streams, '||'), keep_on_prune=True)
    pillar_collision_streams.append(s)

any_pillar_collision = lola_chain(pillar_collision_streams, '||')

collision_stream = LolaStream('Collision')
collision_exp = lola_chain([corner_collision,any_pillar_collision], '||')
spec.add_expression(collision_stream, collision_exp, keep_on_prune=True)

# print(spec.get_specification_string())
spec.write_specification('walls3-redux-uncollapsed.lola')

for s in pillar_collision_streams:
    spec.collapse_expression(s)
spec.collapse_expression(collision_stream)
spec.prune()

# print(spec.get_specification_string())
spec.write_specification('walls3-redux.lola')
