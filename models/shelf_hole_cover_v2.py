from copy import copy
from math import sqrt
from build123d import *
from ocp_vscode import *


CYL_DIAMETER = 20 * MM
CYL_INNER_DIAMETER = 14.1 * MM
HOLE_INSIDE_DIAMETER = 6.5 * MM
HOLE_OUTER_DIAMETER_VERT = 18 * MM
THICKNESS = 0.6 * MM
SOCKET_THICKNESS = 1 * MM
ERROR = 0.1 * MM
SOCKET_SHIFT = 0.1

CYL_RADIUS = CYL_DIAMETER / 2
HOLE_OUTER_RADIUS_VERT = HOLE_OUTER_DIAMETER_VERT / 2
CYL_INNER_RADIUS_HORI = CYL_INNER_DIAMETER / 2
HOLE_OUTER_RADIUS_HORI = sqrt(CYL_RADIUS**2 - CYL_INNER_RADIUS_HORI**2)
HOLE_INSIDE_RADIUS = HOLE_INSIDE_DIAMETER / 2


def make_inner(radius):
    with BuildPart() as part:
        with Locations((0, CYL_RADIUS * SOCKET_SHIFT, 0)):
            Cylinder(radius, CYL_RADIUS, rotation=(90, 0, 0),
                     align=(Align.CENTER, Align.CENTER, Align.MAX))
        Cylinder(CYL_RADIUS - THICKNESS / 2, radius * 2, mode=Mode.INTERSECT)
    return part.part


def make_cover():
    with BuildPart() as part_cover:
        Cylinder(
            CYL_RADIUS,
            HOLE_OUTER_RADIUS_VERT * 4,
            arc_size=180,
            align=(Align.CENTER, Align.MIN, Align.CENTER),
        )
        Cylinder(CYL_RADIUS - THICKNESS, HOLE_OUTER_RADIUS_HORI * 4, mode=Mode.SUBTRACT)
        with BuildSketch(Plane.XZ):
            Ellipse(
                HOLE_OUTER_RADIUS_HORI,
                HOLE_OUTER_RADIUS_VERT,
            )
        thicken(amount=CYL_DIAMETER, both=True, mode=Mode.INTERSECT)
    return part_cover.part
        
def make_socket(radius):
    with BuildPart() as part_cover:
        length = CYL_DIAMETER * (1-SOCKET_SHIFT*2)
        Cylinder(radius, length)
        Cylinder(radius - SOCKET_THICKNESS, length, mode=Mode.SUBTRACT)
    return part_cover.part

part_inner = make_inner(HOLE_INSIDE_RADIUS - SOCKET_THICKNESS - ERROR)
part_cover = part_inner + make_cover()
part_socket = make_socket(HOLE_INSIDE_RADIUS)
cover = pack([part_cover, copy(part_cover), part_socket], 10 * MM, align_z=True)

exporter = Mesher()
exporter.add_shape(cover)
exporter.add_code_to_metadata()
exporter.write("exports/shelf_hole_cover_v2.stl")
exporter.write("exports/shelf_hole_cover_v2.3mf")

show_all()
