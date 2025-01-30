from copy import copy
from math import sqrt
from build123d import *
from ocp_vscode import *


TOLERANCE = 0.1 * MM
BALL_RADIUS = 30 * MM
CYLINDER_RADIUS = 5 * MM
CYLINDER_LENGTH = BALL_RADIUS / 2

with BuildPart() as part_ball:
    with Locations((0, 0, BALL_RADIUS / 2)):
        Sphere(
            BALL_RADIUS,
            arc_size3=180,
            rotation=(90, 0, 0),
        )
    d = BALL_RADIUS / 2
    with Locations(
        [
            (-d, 0, 0),
            (d, 0, 0),
        ]
    ):
        Cylinder(CYLINDER_RADIUS, CYLINDER_LENGTH, mode=Mode.SUBTRACT)

with BuildPart() as part_pillar:
    Cylinder(CYLINDER_RADIUS - TOLERANCE, CYLINDER_LENGTH, mode=Mode.ADD)

parts = pack([part_ball.part, part_pillar.part], 10 * MM, align_z=True)

exporter = Mesher()
exporter.add_shape(parts)
exporter.add_code_to_metadata()
exporter.write("exports/ball.stl")
exporter.write("exports/ball.3mf")

show_all()
