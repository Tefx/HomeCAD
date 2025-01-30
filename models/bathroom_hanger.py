from copy import copy
from math import sqrt
from build123d import *
from ocp_vscode import *

GLASS_THICKNESS = 10 * MM
TOLERANCE = 0.5 * MM
HANGER_UPPER_WIDTH = GLASS_THICKNESS + TOLERANCE
HANGER_THICKNESS = 3 * MM
HANGER_WIDTH = 6 * MM

with BuildPart() as part:
    with BuildSketch() as sketch:
        with BuildLine() as line:
            l1 = Line((0, 70), (HANGER_UPPER_WIDTH / 2, 70))
            l2 = Line(l1 @ 1, (HANGER_UPPER_WIDTH / 2, 0))
            l3 = Line(l2 @ 1, (40 + (GLASS_THICKNESS + TOLERANCE) / 2, 0))
            l4 = Line(l3 @ 1, (40 + (GLASS_THICKNESS + TOLERANCE) / 2, 20))
            offset(amount=HANGER_THICKNESS, side=Side.LEFT)
        make_face()
        for x in (20 - HANGER_THICKNESS * 2, 30 - HANGER_THICKNESS):
            with BuildLine() as line2:
                l5 = Line(
                    (x + (GLASS_THICKNESS + TOLERANCE) / 2, HANGER_THICKNESS),
                    (x + (GLASS_THICKNESS + TOLERANCE) / 2, 5 + HANGER_THICKNESS),
                )
                offset(amount=HANGER_THICKNESS / 2, side=Side.LEFT)
            make_face()
        mirror(about=Plane.YZ)
    thicken(amount=HANGER_WIDTH)

exporter = Mesher()
exporter.add_shape(part.part)
exporter.add_code_to_metadata()
exporter.write("exports/bathroom_hanger.stl")
exporter.write("exports/bathroom_hanger.3mf")

show_all()
