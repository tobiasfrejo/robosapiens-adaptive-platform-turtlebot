from itertools import chain
from DynamicLolaSpecGeneration.lola import LolaSpecification, LolaStream, lola_chain, lnot, Expression
from DynamicLolaSpecGeneration.turtlebot import tb3_corners, turtle_map, turtle_map_pillars
from DynamicLolaSpecGeneration.geometry import rotate_polygon, connect_polygon, circle_line_overlap, test_points_in_circles
from DynamicLolaSpecGeneration.pnpoly import pnpoly

spec = LolaSpecification()

x = LolaStream('x')
y = LolaStream('y')
a = LolaStream('a')

spec.inputs.append(LolaStream('Odometry'))
spec.add_expression(x, Expression('List.get(Odometry, 0)'), keep_on_prune=True)
spec.add_expression(y, Expression('List.get(Odometry, 1)'), keep_on_prune=True)
spec.add_expression(a, Expression('List.get(Odometry, 2)'), keep_on_prune=True)

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

# Kinda double work since also included in wall_exprs
for stream in pnp:
    exp = spec.expressions[stream]
    spec.add_expression(stream, exp, keep_on_prune=True)

in_map = LolaStream('InMap')
spec.add_expression(in_map, lola_chain(pnp, '&&'), keep_on_prune=True)

corner_collision_streams = []
for n,streams in pillar_point_streams.items():
    s = LolaStream(f'Corner{n}Collision')
    spec.add_expression(s, lola_chain(streams, '||'), keep_on_prune=True)
    corner_collision_streams.append(s)

any_pillar_collision = lola_chain(corner_collision_streams, '||')

collision_stream = LolaStream('Collision')
collision_exp = lola_chain([lnot(in_map),any_pillar_collision], '||')

spec.add_expression(collision_stream, collision_exp, keep_on_prune=True)


spec.write_specification('walls2-redux2.lola')
# print("======BEFORE PRUNE========")
# spec.print_dependency_graph()
# print()

# prior_spec = spec.get_specification_string()

# print("======AFTER PRUNE========")
# spec.print_dependency_graph()
# print()
# print("======SPECIFICATION========")
# post_spec = spec.get_specification_string()
# print(spec.get_specification_string())
# #spec.write_specification('walls2-redux2.lola')

# print(prior_spec==post_spec)


# # point0_stream = list(pillars_expressions.keys())[0]
# # print(point0_stream)
# # print(pillars_expressions[point0_stream].get_exp_list())
spec.collapse_expression(in_map)
for stream in chain(corner_collision_streams, pnp):
    print(stream)
    print(spec.dependency_graph.nodes[stream].get('output_stream', False))
    spec.collapse_expression(stream)  
    
spec.prune()
# print()
# #print(spec.expressions[collision_stream])
collasped_spec = spec.get_specification_string()
#print(collasped_spec)
spec.write_specification('walls2-mono.lola')

# print(collasped_spec==post_spec)