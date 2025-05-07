from itertools import chain
from dyn_lola.lola import LolaSpecification, LolaStream, lola_chain, Expression, lnot
from dyn_lola.shapes import turtlebot
from dyn_lola.geometry import rotate_polygon, connect_polygon
from dyn_lola.pnpoly import pnpoly

spec = LolaSpecification()

spec.inputs.append(LolaStream('Odometry'))
x = LolaStream('x')
spec.add_expression(x, Expression('List.get(Odometry, 0)'), keep_on_prune=True)
y = LolaStream('y')
spec.add_expression(y, Expression('List.get(Odometry, 1)'), keep_on_prune=True)
a = LolaStream('a')
spec.add_expression(a, Expression('List.get(Odometry, 2)'), keep_on_prune=True)

tb3_exprs, tb3_rotated_corners = rotate_polygon(turtlebot.tb3_corners, (x,y), a)
map_walls = connect_polygon(turtlebot.turtle_map)
wall_exprs, pnp_walls = pnpoly(tb3_rotated_corners, map_walls, 'Wall')

for k,v in chain.from_iterable([tb3_exprs.items(), wall_exprs.items()]):
    spec.add_expression(k,v)

corner_collision_streams = []
for corner_index in range(len(tb3_rotated_corners)):
    in_map = pnp_walls[corner_index]
    s = LolaStream(f'Corner{corner_index}Collision')
    spec.add_expression(s, lnot(in_map))
    corner_collision_streams.append(s)

collision_stream = LolaStream('Collision')
collision_exp = lola_chain(corner_collision_streams, '||')
spec.add_expression(collision_stream, collision_exp, keep_on_prune=True)
spec.collapse_expression(collision_stream)

spec.prune()

print(spec.get_specification_string())