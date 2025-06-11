from itertools import chain
import itertools
from dyn_lola.convex_poly import cpoly
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

tb3_exprs, tb3_rotated_corners = rotate_polygon(turtlebot.tb3_corners_offset(0.01), (x,y), a)

print([connect_polygon(p) for p in turtlebot.turtle_map_convex])

obstacle_wall = [[
    ((-1.0, 1.0), (-1.0,  -1.0)),
    ((1.0,  -1.0), (1.0, 1.0)),
]]

expressions, streams = cpoly(tb3_rotated_corners, obstacle_wall, 'Obstacle', 'counterclockwise')

for k,v in tb3_exprs.items():
    spec.add_expression(k,v, keep_on_prune=True)

for k,v in expressions.items():
    spec.add_expression(k,v)

obstacle_stream = LolaStream('ObstacleCollision')
obstacle_collision = lola_chain(streams, '||')
spec.add_expression(obstacle_stream, obstacle_collision)

spec.write_specification('cpoly-test.lola')

# # wall_exprs, pnp_walls = pnpoly(tb3_rotated_corners, map_walls, 'Wall')
# wall_exprs, wall_streams = cpoly(tb3_rotated_corners, [connect_polygon(p) for p in turtlebot.turtle_map_convex], 'map', 'counterclockwise')

# # obstacle_exprs, pnp_obstacles = pnpoly(tb3_rotated_corners, obstacle_wall, 'Obstacle')
# obstacle_exprs, obstacle_streams = cpoly(tb3_rotated_corners, obstacle_wall, 'Obstacle', 'counterclockwise')
# pillars_expressions, pillar_point_streams, _ = test_points_in_circles(tb3_rotated_corners, turtlebot.turtle_map_pillars)

# for k,v in tb3_exprs.items():
#     spec.add_expression(k,v, keep_on_prune=True)

# for k,v in chain.from_iterable((wall_exprs.items(), pillars_expressions.items(), obstacle_exprs.items())):
#     spec.add_expression(k,v)

# in_map = lola_chain(wall_streams, '&&')
# obstacle_collision = lola_chain(obstacle_streams, '||')
# pillar_collisions = lola_chain(list(itertools.chain.from_iterable(pillar_point_streams.values())), '||')


# in_map_stream = LolaStream('InMap')
# obstacle_stream = LolaStream('ObstacleCollision')
# pillar_collision_stream = LolaStream('PillarCollision')
# spec.add_expression(in_map_stream, in_map)
# spec.add_expression(obstacle_stream, obstacle_collision)
# spec.add_expression(pillar_collision_stream, pillar_collisions)

# collision_stream = LolaStream('Collision')
# collision_exp = lola_chain([lnot(in_map_stream), obstacle_stream, pillar_collision_stream], '||')
# spec.add_expression(collision_stream, collision_exp, keep_on_prune=True)

# # print(spec.get_specification_string())
# spec.write_specification('walls2-redux-cpoly-uncollapsed.lola')

# spec.collapse_expression(collision_stream)
# spec.prune()

# # print(spec.get_specification_string())
# spec.write_specification('walls2-redux-cpoly.lola')
