from copy import copy
from math import sqrt
from build123d import *
from ocp_vscode import *


HOOK_WIDTH = 20 * MM
HOOK_HEITHG_INNER = 40.9 * MM
HOOK_THICKNESS = 5 * MM
HOOK_DEPTH = 40.8 * MM
END_HOOK_HEIGHT = 10 * MM

with BuildPart() as part_ball:
    with BuildSketch() as sketch:
        with BuildLine() as line:
            l0 = Line((0, END_HOOK_HEIGHT), (0, 0))
            l1 = Line(l0 @ 1, (HOOK_DEPTH, 0))
            l2 = Line(l1 @ 1, (HOOK_DEPTH, HOOK_HEITHG_INNER))
            l3 = Line(l2 @ 1, (-HOOK_DEPTH, HOOK_HEITHG_INNER))
            offset(amount=HOOK_THICKNESS, side=Side.RIGHT)
        make_face()
    thicken(amount=HOOK_WIDTH)


exporter = Mesher()
exporter.add_shape(part_ball.part)
exporter.add_code_to_metadata()
exporter.write("exports/plant_light_hook.stl")
exporter.write("exports/plant_light_hook.3mf")

show_all()
