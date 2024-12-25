from build123d import *
from ocp_vscode import *

FRAME_HEIGHT = 8 * MM
FRAME_WITDH = 8 * MM
SIDE_ARM_LENGTH = 50 * MM
TOP_ARM_MIN_LENGTH = 40 * MM
HOLES = 6
HOLE_DIAMETER = 4 * MM
HOLE_INTERVAL = (TOP_ARM_MIN_LENGTH - HOLES * HOLE_DIAMETER) / (HOLES + 1)
HOLE_DEPTH = FRAME_WITDH * 0.2
ERROR = 0.4 * MM

with BuildPart() as part_female:
    with BuildSketch() as sketch_female:
        with BuildLine() as line:
            Line((0, 0), (TOP_ARM_MIN_LENGTH, 0))
            Line((0, 0), (0, -SIDE_ARM_LENGTH))
            offset(line.line, amount=FRAME_HEIGHT, side=Side.LEFT)
        make_face()
    thicken(amount=FRAME_WITDH)

    with Locations((0, 0, FRAME_WITDH / 2)):
        box = Box(
            TOP_ARM_MIN_LENGTH,
            FRAME_HEIGHT,
            FRAME_WITDH / 2,
            align=Align.MIN,
            mode=Mode.SUBTRACT,
        )

    with BuildSketch(box.faces().sort_by(sort_by=Axis.Z)[0]) as sketch_hole:
        hole_x = HOLE_DIAMETER / 2 + HOLE_INTERVAL - TOP_ARM_MIN_LENGTH / 2
        with Locations(
            *[
                (hole_x + (HOLE_INTERVAL + HOLE_DIAMETER) * i, 0)
                for i in range(HOLES)
            ]
        ):
            RegularPolygon(HOLE_DIAMETER / 2 + ERROR / 2, side_count=5)
    thicken(amount=HOLE_DEPTH + ERROR, mode=Mode.SUBTRACT)
    

with BuildPart() as part_male:
    with BuildSketch() as sketch_male:
        with BuildLine() as line:
            Line((0, 0), (TOP_ARM_MIN_LENGTH, 0))
            Line((TOP_ARM_MIN_LENGTH, 0), (TOP_ARM_MIN_LENGTH, -SIDE_ARM_LENGTH))
            offset(line.line, amount=FRAME_HEIGHT, side=Side.LEFT)
        make_face()
    thicken(amount=FRAME_WITDH)

    with Locations((0, 0, 0)):
        box = Box(
            TOP_ARM_MIN_LENGTH,
            FRAME_HEIGHT,
            FRAME_WITDH / 2,
            align=Align.MIN,
            mode=Mode.SUBTRACT,
        )

    with BuildSketch(box.faces().sort_by(sort_by=Axis.Z)[-1]) as sketch_hole:
        hole_x = HOLE_DIAMETER / 2 + HOLE_INTERVAL - TOP_ARM_MIN_LENGTH / 2
        with Locations(
            *[
                (hole_x + (HOLE_INTERVAL + HOLE_DIAMETER) * i, 0)
                for i in range(HOLES)
            ]
        ):
            RegularPolygon(HOLE_DIAMETER / 2, side_count=5)
    thicken(amount=-HOLE_DEPTH, mode=Mode.ADD)

part_male.part.move(Location((TOP_ARM_MIN_LENGTH + FRAME_HEIGHT + 10, 0, 0)))

exporter = Mesher()
exporter.add_shape(part_female.part)
exporter.add_shape(part_male.part)
exporter.add_code_to_metadata()
exporter.write("exports/cardboard_clip.stl")
exporter.write("exports/cardboard_clip.3mf")

show_object(part_female.part)
show_object(part_male.part)
# show_all()
