from dyn_lola.lola import LolaSpecification, LolaStream, Expression, lnot
from dyn_lola.geometry import connect_polygon
from dyn_lola.pnpoly import pnpoly

spec = LolaSpecification()

spec.inputs.append(LolaStream('Odometry'))
x = LolaStream('Px')  # Using the x coordinate of the axis of rotation directly as the point x coordinate
spec.add_expression(x, Expression('List.get(Odometry, 0)'))
y = LolaStream('Py') # Using the y coordinate of the axis of rotation directly as the point y coordinate
spec.add_expression(y, Expression('List.get(Odometry, 1)'))

# When expanding to use TB3 the angle for the axis of rotation would importated as follows:
# a = LolaStream('a') 
# spec.add_expression(a, Expression('List.get(Odometry, 2)')) 

point_streams = [(x, y)]

outer_walls = [ # Defining the corner points for the 10x10 sqaure map
    (-5, -5),
    ( 5, -5),
    ( 5,  5),
    (-5,  5),
]

map_walls = connect_polygon(outer_walls) # Connect neigbouring map corners to generate walls
wall_exprs, pnp_walls = pnpoly(point_streams, map_walls, "OuterWall") # For every point-wall pair (4 total for minimal case) generate the pnpoly expression

for k,v in wall_exprs.items():
    spec.add_expression(k,v)


# For the minimal case there is only 1 point but the loop has been included to indicte how larger specs may be generated
for corner_index in range(len(point_streams)):
    in_map = pnp_walls[corner_index]
    s = LolaStream(f'Corner{corner_index}Collision')
    spec.add_expression(s, lnot(in_map), keep_on_prune=True)

print(spec.get_specification_string())