from build123d import *
from ocp_vscode import *

FRAME_SIZE = 86 * MM
FRAME_ERROR = 0.2 * MM
FRAME_OUTER_SIZE_VERT = 88 * MM
FRAME_OUTER_SIZE_HORI = 93 * MM
FRAME_THICKNESS = 14 * MM
HOLE_WIDTH = 2 * MM
HOLE_HEIGHT = 4 * MM
HOLE_INTERVAL = 6 * MM
HOLE_ERROR = 0.2 * MM
HOLE_DISTANCE = HOLE_HEIGHT + HOLE_INTERVAL
HOLE_DEPTH = FRAME_THICKNESS * 0.9
PILLAR_HEIGHT = HOLE_DEPTH * 0.5
COVER_THICKNESS = 1 * MM
COVER_INNER_THICKNESS = 1 * MM

frame_center = (FRAME_SIZE + HOLE_WIDTH) / 2
cover_height = (FRAME_OUTER_SIZE_VERT - FRAME_SIZE) + HOLE_DISTANCE * 2 + HOLE_INTERVAL

with BuildPart() as frame_part:
    Box(FRAME_OUTER_SIZE_HORI, FRAME_OUTER_SIZE_VERT, FRAME_THICKNESS)
    Box(
        FRAME_SIZE + FRAME_ERROR,
        FRAME_SIZE + FRAME_ERROR,
        FRAME_THICKNESS,
        mode=Mode.SUBTRACT,
    )

    frame_top = frame_part.faces().sort_by(sort_by=Axis.Z)[-1]
    with BuildSketch(frame_top) as hole_sketch:
        hole_start_y = -FRAME_SIZE / 2 + HOLE_INTERVAL + HOLE_HEIGHT / 2
        with Locations(
            *[
                (frame_center, hole_start_y + i * HOLE_DISTANCE)
                for i in range(int(FRAME_SIZE / HOLE_DISTANCE))
            ]
        ) as hole_locations:
            hole = Rectangle(HOLE_WIDTH + HOLE_ERROR, HOLE_HEIGHT + HOLE_ERROR)
            mirror(hole, about=Plane.YZ)
    thicken(amount=-HOLE_DEPTH, mode=Mode.SUBTRACT)

with BuildPart() as cover_part:
    move_y_offset = (FRAME_OUTER_SIZE_VERT + cover_height) / 2 + 10
    with Locations(((0, -move_y_offset, -COVER_THICKNESS))):
        Box(FRAME_OUTER_SIZE_HORI, cover_height, COVER_THICKNESS)

    cover_part_top = cover_part.faces().sort_by(sort_by=Axis.Z)[-1]
    with BuildSketch(cover_part_top) as cover_pole_sketch:
        with Locations(((frame_center, -(HOLE_INTERVAL + HOLE_HEIGHT) / 2))):
            pillars = [Rectangle(HOLE_WIDTH, HOLE_HEIGHT)]
            pillars.extend(mirror(pillars, about=Plane.YZ))
        mirror(pillars, about=Plane.XZ)
    thicken(amount=PILLAR_HEIGHT)

    with BuildSketch(cover_part_top) as cover_hole_sketch:
        height = (
            cover_height - (FRAME_OUTER_SIZE_VERT - FRAME_SIZE) / 2 - FRAME_ERROR * 2
        )
        Rectangle(FRAME_SIZE - FRAME_ERROR * 2, height)
    thicken(amount=COVER_INNER_THICKNESS)

# compounded = Compound((frame_part.part, cover_part.part))

exporter = Mesher()
exporter.add_shape(frame_part.part)
exporter.add_shape(cover_part.part)
exporter.add_code_to_metadata()
exporter.write("exports/socket_cover.stl")
exporter.write("exports/socket_cover.3mf")

# show_all()
show_object(Compound((frame_part.part, cover_part.part)))
