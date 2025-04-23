from itertools import chain
from dyn_lola.lola import LolaSpecification, LolaStream, lola_chain, Expression, lnot
from dyn_lola.shapes import turtlebot
from dyn_lola.geometry import rotate_polygon, connect_polygon, circle_line_overlap, test_points_in_circles
from dyn_lola.pnpoly import pnpoly

spec = LolaSpecification()

x = LolaStream('x')
y = LolaStream('y')
a = LolaStream('a')

spec.inputs.append(LolaStream('Odometry'))
spec.add_expression(x, Expression('List.get(Odometry, 0)'), keep_on_prune=True)
spec.add_expression(y, Expression('List.get(Odometry, 1)'), keep_on_prune=True)
spec.add_expression(a, Expression('List.get(Odometry, 2)'), keep_on_prune=True)

tb3_exprs, tb3_rotated_corners = rotate_polygon(turtlebot.tb3_corners, (x,y), a)

map_walls = connect_polygon(turtlebot.turtle_map)
obstacle_wall = connect_polygon([
    (-0.1, 2.1),
    (-0.1, 1.9),
    ( 0.1, 1.9),
    ( 0.1, 2.1),
])

wall_exprs, pnp = pnpoly(tb3_rotated_corners, map_walls + obstacle_wall)
pillars_expressions, pillar_point_streams, _ = test_points_in_circles(tb3_rotated_corners, turtlebot.turtle_map_pillars)

for k,v in chain.from_iterable((tb3_exprs.items(), wall_exprs.items(), pillars_expressions.items())):
    spec.add_expression(k,v)

in_map = LolaStream('InMap')
spec.add_expression(in_map, lola_chain(pnp, '&&'), keep_on_prune=True)
spec.collapse_expression(in_map)

corner_collision_streams = []
for n,streams in pillar_point_streams.items():
    s = LolaStream(f'Corner{n}Collision')
    spec.add_expression(s, lola_chain(streams, '||'), keep_on_prune=True)
    corner_collision_streams.append(s)
    spec.collapse_expression(s)

any_pillar_collision = lola_chain(corner_collision_streams, '||')

collision_stream = LolaStream('Collision')
collision_exp = lola_chain([lnot(in_map),any_pillar_collision], '||')
spec.add_expression(collision_stream, collision_exp, keep_on_prune=True)
spec.collapse_expression(collision_stream)

spec.prune()
#spec.write_specification('test2_collapsed.lola')

#print(spec.get_specification_string())
spec.write_specification('walls2-redux.lola')