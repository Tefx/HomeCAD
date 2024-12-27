from math import sqrt
from build123d import *
from ocp_vscode import *


CYL_DIAMETER = 20 * MM
CYL_INNER_DIAMETER = 14.1 * MM
HOLE_INSIDE_DIAMETER = 6.5 * MM
HOLE_OUTER_DIAMETER_VERT = 18 * MM
THICKNESS = 0.6 * MM
POLE_THICKNESS = 1 * MM
ERROR = 0.1 * MM
POLE_SHIFT = 0.2

CYL_RADIUS = CYL_DIAMETER / 2
HOLE_OUTER_RADIUS_VERT = HOLE_OUTER_DIAMETER_VERT / 2
CYL_INNER_RADIUS_HORI = CYL_INNER_DIAMETER / 2
HOLE_OUTER_RADIUS_HORI = sqrt(CYL_RADIUS**2 - CYL_INNER_RADIUS_HORI**2)
HOLE_INSIDE_RADIUS = HOLE_INSIDE_DIAMETER / 2


def make_inner(outer_radius, thinkness, position=1):
    with BuildPart() as part:
        with Locations((0, CYL_RADIUS * POLE_SHIFT * position, 0)):
            Cylinder(outer_radius, CYL_DIAMETER, rotation=(90, 0, 0))
            if position > 0:
                Cylinder(
                    outer_radius - thinkness,
                    CYL_DIAMETER,
                    rotation=(90, 0, 0),
                    mode=Mode.SUBTRACT,
                )
        Cylinder(CYL_RADIUS - THICKNESS / 2, outer_radius * 2, mode=Mode.INTERSECT)
    return part.part


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

part_left_inner = make_inner(HOLE_INSIDE_RADIUS + ERROR, POLE_THICKNESS, 1)
part_right_inner = make_inner(HOLE_INSIDE_RADIUS - POLE_THICKNESS, POLE_THICKNESS, -1)
part_cover_left = part_cover.part
part_cover_right = mirror(part_cover_left, about=Plane.XZ)
part_left = (part_left_inner + part_cover_left).rotate(Axis.X, 90)
part_right = (part_right_inner + part_cover_right).rotate(Axis.X, 90)
cover = pack([part_left, part_right], 10 * MM, align_z=True)

exporter = Mesher()
exporter.add_shape(cover)
exporter.add_code_to_metadata()
exporter.write("exports/shelf_hole_cover_v1.stl")
exporter.write("exports/shelf_hole_cover_v1.3mf")

show_all()
