import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Polygon



# Sources are hexagon.dae and wall.dae from the Gazebo TurtleBot models
# Units are inches
hexagon_model_points = "-28.8675 50 100 -57.735 9.66338e-13 0 -57.735 1.13687e-12 100 -28.8675 50 0 -57.735 1.13687e-12 100 -28.8675 -50 0 -28.8675 -50 100 -57.735 9.66338e-13 0 -28.8675 -50 100 28.8675 -50 0 28.8675 -50 100 -28.8675 -50 0 28.8675 -50 100 57.735 1.7053e-12 0 57.735 1.36424e-12 100 28.8675 -50 0 57.735 1.36424e-12 100 28.8675 50 2.498e-13 28.8675 50 100 57.735 1.7053e-12 0 28.8675 50 100 -28.8675 50 0 -28.8675 50 100 28.8675 50 2.498e-13 -57.735 1.13687e-12 100 57.735 1.36424e-12 100 -28.8675 50 100 -28.8675 -50 100 28.8675 -50 100 28.8675 50 100 -57.735 9.66338e-13 0 28.8675 -50 0 -28.8675 -50 0 57.735 1.7053e-12 0 -28.8675 50 0 28.8675 50 2.498e-13"
wall_model_points = "-400 230.94 0 -400 230.94 200 4.54747e-13 461.88 200 6.25278e-13 461.88 0 6.25278e-13 461.88 0 4.54747e-13 461.88 200 400 230.94 200 400 230.94 0 400 230.94 0 400 230.94 200 400 -230.94 200 400 -230.94 0 400 -230.94 0 400 -230.94 200 -1.7053e-13 -461.88 200 2.27374e-13 -461.88 0 2.27374e-13 -461.88 0 -1.7053e-13 -461.88 200 -400 -230.94 200 -400 -230.94 0 450 259.808 200 -3.69482e-13 519.615 200 -2.27374e-13 519.615 0 450 259.808 0 -3.69482e-13 519.615 200 -450 259.808 200 -450 259.808 0 -2.27374e-13 519.615 0 -450 259.808 200 -450 -259.808 200 -450 -259.808 0 -450 259.808 0 -450 -259.808 200 -1.13687e-13 -519.615 200 -2.27374e-13 -519.615 0 -450 -259.808 0 -1.13687e-13 -519.615 200 450 -259.808 200 450 -259.808 0 -2.27374e-13 -519.615 0 450 -259.808 0 450 259.808 200 450 259.808 0 450 -259.808 200 -400 -230.94 0 -400 -230.94 200 -400 230.94 200 -400 230.94 0 -1.7053e-13 -461.88 200 -1.13687e-13 -519.615 200 -400 -230.94 200 -450 -259.808 200 -450 259.808 200 450 -259.808 200 400 -230.94 200 400 230.94 200 4.54747e-13 461.88 200 -3.69482e-13 519.615 200 -400 230.94 200 450 259.808 200 -2.27374e-13 -519.615 0 400 -230.94 0 2.27374e-13 -461.88 0 400 230.94 0 -2.27374e-13 519.615 0 6.25278e-13 461.88 0 450 -259.808 0 450 259.808 0 -400 230.94 0 -450 259.808 0 -400 -230.94 0 -450 -259.808 0"

inch_to_meter = 0.0254


# Scale factors from Gazebo world
wall_scale = 0.25


def order_poly(p: tuple[float, float]):
    return np.arctan2(p[1],p[0])

def get_model_2d_points(model: str, axes=[0,1], stride=3, epsilon=1e-10):
    all_values = []
    for v in model.split(' '):
        all_values.append(float(v))
    
    points = set()
    for i in range(0, len(all_values), stride):
        point = []
        for n in axes:
            v = all_values[i+n]
            if abs(v) < epsilon: 
                v = 0
            point.append(v)
        points.add(tuple(point))
    
    return np.array(sorted(list(points), key=order_poly))





wall_points = get_model_2d_points(wall_model_points, [1,0]) # The model is rotated, which can be done by switching the axes due to the symmetry
hexagon_points = get_model_2d_points(hexagon_model_points)

inner_wall = []
outer_wall = []

for x,y in wall_points:
    if np.sqrt(x*x + y*y) < 500.0:
        inner_wall.append((x,y))
    else:
        outer_wall.append((x,y))


hexagons = [
    # Values from Gazebo. (center_x, center_y, scale)
    (3.5, 0.0, 0.8),
    (1.8, 2.7, 0.55),
    (1.8, -2.7, 0.55),
    (-1.8, 2.7, 0.55),
    (-1.8, -2.7, 0.55),
]

features = [(hexagon_points * inch_to_meter * scale) + np.array([x, y]) for x,y,scale in hexagons]
inner_wall_m = np.array(inner_wall) * inch_to_meter * wall_scale

plt.scatter(*zip(*inner_wall_m))
for feature in features:
    plt.scatter(*zip(*feature))
    
plt.savefig("/ws/map.pdf")

world_poly = Polygon(sorted(inner_wall_m, key=order_poly))

for feat in features:
    world_poly = world_poly.difference(Polygon(feat))

print(sorted(list(world_poly.exterior.coords), key=order_poly))