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

wall_exprs, pnp_walls = pnpoly(tb3_rotated_corners, map_walls, 'Wall')
obstacle_exprs, pnp_obstacles = pnpoly(tb3_rotated_corners, obstacle_wall, 'Obstacle')
pillars_expressions, pillar_point_streams, _ = test_points_in_circles(tb3_rotated_corners, turtlebot.turtle_map_pillars)

for k,v in tb3_exprs.items():
    spec.add_expression(k,v, keep_on_prune=True)

for k,v in chain.from_iterable((wall_exprs.items(), pillars_expressions.items(), obstacle_exprs.items())):
    spec.add_expression(k,v)


# For every corner:
# - InMap - we have this from pnp
# - CornerCollision
# - ObstacleCollision we have this from pnp

corner_collision_streams = []
for corner_index in range(len(tb3_rotated_corners)):
    in_map = pnp_walls[corner_index]
    pillar_collision = lola_chain(pillar_point_streams[corner_index], '||')
    obstacle_collision = pnp_obstacles[corner_index]

    exp = lola_chain([lnot(in_map), pillar_collision, obstacle_collision], '||')

    s = LolaStream(f'Corner{corner_index}Collision')
    spec.add_expression(s, exp, keep_on_prune=True)
    corner_collision_streams.append(s)
    spec.collapse_expression(s)

collision_stream = LolaStream('Collision')
collision_exp = lola_chain(corner_collision_streams, '||')
spec.add_expression(collision_stream, collision_exp, keep_on_prune=True)
spec.collapse_expression(collision_stream)

spec.prune()
#spec.write_specification('test2_collapsed.lola')

#print(spec.get_specification_string())
spec.write_specification('walls2-redux.lola')