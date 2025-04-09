from itertools import chain
import lola
from turtlebot import tb3_corners, turtle_map
from geometry import rotate_polygon, connect_polygon, circle_line_overlap
from pnpoly import pnpoly

spec = lola.LolaSpecification()

x = lola.LolaStream('x')
y = lola.LolaStream('y')
a = lola.LolaStream('a')

spec.inputs.append(lola.LolaStream('Odometry'))
spec.add_expression(x, 'List.get(Odometry, 0)')
spec.add_expression(y, 'List.get(Odometry, 1)')
spec.add_expression(a, 'List.get(Odometry, 2)')

tb3_exprs, tb3_rotated_corners = rotate_polygon(tb3_corners, (x,y), a)

map_walls = connect_polygon(turtle_map)

wall_exprs, pnp = pnpoly(tb3_rotated_corners, map_walls)

for k,v in chain.from_iterable((tb3_exprs.items(), wall_exprs.items())):
    spec.add_expression(k,v)

spec.add_expression(lola.LolaStream('collision'), lola.lola_chain(pnp, '||'))

spec.add_expression(lola.LolaStream('pillar'), circle_line_overlap(((x,y), 0.3), map_walls[0]))

# spec.add_expression(lola.LolaStream('collision'), lola.lola_chain(tb3_exprs.keys(), '^'))

print(spec.get_specification_string())