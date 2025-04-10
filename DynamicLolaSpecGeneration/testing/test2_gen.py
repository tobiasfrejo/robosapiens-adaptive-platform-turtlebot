from itertools import chain
import dyn_lola.geometry as geometry
from dyn_lola.shapes import turtlebot
from dyn_lola.pnpoly import pnpoly
from dyn_lola.lola import LolaStream, Expression, LolaSpecification, lola_chain

spec = LolaSpecification()

spec.inputs.append(LolaStream('Odometry'))

x = LolaStream('x')
y = LolaStream('y')
a = LolaStream('a')

spec.add_expression(x, Expression('List.get(Odometry, 0)'), keep_on_prune=True)
spec.add_expression(y, Expression('List.get(Odometry, 1)'), keep_on_prune=True)
spec.add_expression(a, Expression('List.get(Odometry, 2)'), keep_on_prune=True)

tb3_exprs, tb3_rotated_corners = geometry.rotate_polygon(turtlebot.tb3_corners, (x,y), a)

obstacle_wall = geometry.connect_polygon([
    (-0.1, 2.1),
    (-0.1, 1.9),
    ( 0.1, 1.9),
    ( 0.1, 2.1),
])

wall_exprs, pnp = pnpoly(tb3_rotated_corners, obstacle_wall)

for k,v in chain.from_iterable((tb3_exprs.items(), wall_exprs.items())):
    spec.add_expression(k,v)

collision_stream = LolaStream('Collision')
collision_exp = lola_chain(pnp, '||')

spec.add_expression(collision_stream, collision_exp, keep_on_prune=True)
spec.write_specification('test2_full.lola')
print("======FULL GRAPH========")
spec.print_dependency_graph()


spec.collapse_expression(collision_stream)
spec.prune()
spec.write_specification('test2_collapsed.lola')
print("======COLLAPSED GRAPH========")
spec.print_dependency_graph()
