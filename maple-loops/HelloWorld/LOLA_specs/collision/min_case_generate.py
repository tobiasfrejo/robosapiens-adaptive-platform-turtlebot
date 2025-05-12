from itertools import chain
from dyn_lola.lola import LolaSpecification, LolaStream, Expression, lnot, lola_chain
from dyn_lola.geometry import connect_polygon, rotate_polygon, test_points_in_circles
from dyn_lola.shapes import turtlebot
from dyn_lola.pnpoly import pnpoly

spec = LolaSpecification()

spec.inputs.append(LolaStream("Odometry"))
x = LolaStream("x")
spec.add_expression(x, Expression("List.get(Odometry, 0)"))
y = LolaStream("y")
spec.add_expression(y, Expression("List.get(Odometry, 1)"))
a = LolaStream("a")
spec.add_expression(a, Expression("List.get(Odometry, 2)"))

tb3_exprs, tb3_rotated_corners = rotate_polygon(turtlebot.tb3_corners, (x, y), a)
selected_point_coor = [tb3_rotated_corners[0]]  # For simplicity only use one point
point_exprs = {}
for c in selected_point_coor[0]:  # Extract exprs for chosen x and y streams
    point_exprs[c] = tb3_exprs[c]

outer_walls = [  # Defining the corner points for the 10x10 sqaure map
    (-5, -5),
    ( 5, -5),
    ( 5,  5),
    (-5,  5),
]
circle_obstacle = [((0.0, 0.0), 0.5)] # Defining central circle obstacle

# TB3 corner collision sub-specification - treat map as polygon. 
map_walls = connect_polygon(outer_walls)  

wall_exprs, pnp_walls = pnpoly(selected_point_coor, map_walls, "OuterWalls")  
pillars_expressions, pillar_point_streams, _ = test_points_in_circles( selected_point_coor, circle_obstacle)

for k, v in chain.from_iterable((point_exprs.items(), wall_exprs.items(), pillars_expressions.items())):
    spec.add_expression(k, v)

# For the minimal case there is only 1 point but the loop has been included to indicte how larger specs may be generated
for corner_index in range(len(selected_point_coor)):
    in_map = pnp_walls[corner_index]
    pillar_collision = lola_chain(pillar_point_streams[corner_index], "||")

    # Implements the TB3 corner collision condition
    exp = lola_chain([lnot(in_map),pillar_collision], "||")  

    s = LolaStream(f"Corner{corner_index}Collision")
    spec.add_expression(s, exp, keep_on_prune=True)

print(spec.get_specification_string())