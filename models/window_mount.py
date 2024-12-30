from enum import Enum
from math import pi, sin
from build123d import *
from ocp_vscode import *


WINDOW_FRAME_HEIGHT = 50 * MM
WINDOW_FRAME_DEPTH = 14.5 * MM
WINDOW_FRAME_SECOND_LOWER_HEIGHT = 15 * MM
WINDOW_FRAME_SECOND_UPPER_HEIGHT = 20 * MM
WINDOW_FRAME_SECOND_UPPER_THICKNESS = 6 * MM
WINDOW_FRAME_SECOND_HOOK_MAX_ALLOW_LENGTH = 2 * MM

GRIDFINITY_UNIT_WIDTH = 42 * MM
GRIDFINITY_FRAME_WIDTH_HALF = 2.15 * MM
GRIDFINITY_HEIGHT_OFFSET = 0.35 * MM
GRIDFINITY_HEIGHT_BOTTOM = 0.7 * MM
GRIDFINITY_HEIGHT_MIDDLE = 1.8 * MM
GRIDFINITY_HEIGHT_TOP = 2.15 * MM


class RAIL_TYPE(Enum):
    PLAIN = 0
    GRIDFINITY_MIDDLE = 1
    GRIDFINITY_FRAME = 2


def _make_gridfinity_node_sketch(plane):
    _bottom_x = GRIDFINITY_FRAME_WIDTH_HALF
    _middle_y = GRIDFINITY_HEIGHT_BOTTOM + GRIDFINITY_HEIGHT_MIDDLE
    _top_y = _middle_y + GRIDFINITY_HEIGHT_TOP
    _height_offset = GRIDFINITY_HEIGHT_OFFSET
    with BuildSketch(plane.move(Location((0, 0, _height_offset)))) as sketch:
        with BuildLine():
            l1 = Line((-_bottom_x, 0), (_bottom_x, 0))
            l2 = Line(l1 @ 1, (_bottom_x, _middle_y))
            l3 = Line(l2 @ 1, (0, _top_y))
            l4 = Line(l3 @ 1, (-_bottom_x, _middle_y))
            l5 = Line(l4 @ 1, l1 @ 0)
        make_face()
        Rectangle(
            _bottom_x * 2,
            _height_offset,
            align=(Align.CENTER, Align.MAX),
            mode=Mode.ADD,
        )
    return sketch.sketch


def make_mount(
    gf_unit,
    mount_thickness=2 * MM,
    mount_width=10 * MM,
    slot_depth=3 * MM,
    slot_tolerance=0.1 * MM,
    primary_support_position=0.9,
    secondary_support_position=0.8,
):
    slot_number = gf_unit * 2 + 1
    slot_width = GRIDFINITY_FRAME_WIDTH_HALF * 2
    slot_interval = GRIDFINITY_UNIT_WIDTH / 2 - slot_width
    mount_outreach_length = (
        slot_width * slot_number
        + slot_interval * (slot_number - 1)
        + mount_thickness * 1.5
        + slot_width * 2
        + slot_depth * 0.5
        - WINDOW_FRAME_DEPTH
    )
    with BuildPart() as part_mount:
        with BuildSketch() as sketch_mount:
            with BuildLine():
                l0 = Line(
                    (WINDOW_FRAME_DEPTH, -WINDOW_FRAME_SECOND_LOWER_HEIGHT),
                    (WINDOW_FRAME_DEPTH, 0),
                )
                l1 = Line(l0 @ 1, (0, 0))
                l2 = Line(l1 @ 1, (0, WINDOW_FRAME_HEIGHT))
                l3 = Line(l2 @ 1, (WINDOW_FRAME_DEPTH, WINDOW_FRAME_HEIGHT))
                offset(amount=mount_thickness, side=Side.LEFT)
            make_face()
            with BuildLine():
                l4 = Line(
                    (
                        WINDOW_FRAME_DEPTH,
                        WINDOW_FRAME_HEIGHT + mount_thickness + slot_depth,
                    ),
                    (
                        -mount_outreach_length,
                        WINDOW_FRAME_HEIGHT + mount_thickness + slot_depth,
                    ),
                )
                offset(amount=mount_thickness + slot_depth, side=Side.LEFT)
            make_face()
            with BuildLine():
                _height = WINDOW_FRAME_HEIGHT + WINDOW_FRAME_SECOND_UPPER_HEIGHT
                _tmp_x = WINDOW_FRAME_DEPTH + WINDOW_FRAME_SECOND_UPPER_THICKNESS
                l8 = Line(l3 @ 1, (WINDOW_FRAME_DEPTH, _height))
                l9 = Line(l8 @ 1, (_tmp_x, _height))
                l10 = Line(
                    l9 @ 1,
                    (_tmp_x, _height - WINDOW_FRAME_SECOND_HOOK_MAX_ALLOW_LENGTH),
                )
                offset(amount=mount_thickness, side=Side.LEFT)
            make_face()
        thicken(amount=mount_width)

        def _find_shape_by_axis(shape, axis, v):
            return shape.filter_by_position(axis, v - 0.001, v + 0.001)

        fillet(
            part_mount.edges().sort_by(Axis.X)[2:4],
            (mount_thickness + slot_depth) / 2 - 0.001,
        )

        def _find_edge(edges, x, y):
            return edges.filter_by_position(Axis.X, x - 0.001, x + 0.001).filter_by_position(Axis.Y, y - 0.001, y + 0.001)[0]

        edge = _find_edge(
                part_mount.edges(),
                WINDOW_FRAME_DEPTH + WINDOW_FRAME_SECOND_UPPER_THICKNESS + mount_thickness,
                WINDOW_FRAME_HEIGHT + WINDOW_FRAME_SECOND_UPPER_HEIGHT - WINDOW_FRAME_SECOND_HOOK_MAX_ALLOW_LENGTH
            )
        chamfer(
            edge,
            length=mount_thickness - 0.001,
            length2=WINDOW_FRAME_SECOND_HOOK_MAX_ALLOW_LENGTH - 0.001,
        )

        face = _find_shape_by_axis(part_mount.faces(), Axis.Y, WINDOW_FRAME_HEIGHT + mount_thickness + slot_depth)[0]
        with BuildSketch(face) as sketch_holes:
            start = (
                -(WINDOW_FRAME_DEPTH + mount_outreach_length) / 2
                + mount_thickness
                + slot_width
                + slot_depth * 0.5
            )
            with Locations(
                *[
                    (0, start + (slot_width + slot_interval) * i)
                    for i in range(slot_number)
                ]
            ):
                RegularPolygon(slot_width + slot_tolerance / sin(pi / 3), side_count=6)
                Rectangle(mount_width + slot_tolerance * 2, slot_width)
        thicken(amount=-slot_depth, mode=Mode.SUBTRACT)

    with BuildPart() as part_mount_support:
        with BuildSketch():
            _num = slot_number // 4 + 1
            _interval = (mount_outreach_length - MOUNT_THICKNESS) * primary_support_position / _num
            for i in range(_num):
                with BuildLine():
                    l5 = EllipticalCenterArc(
                        (-MOUNT_THICKNESS, WINDOW_FRAME_HEIGHT),
                        _interval * (i + 1),
                        WINDOW_FRAME_HEIGHT * primary_support_position,
                        start_angle=180,
                        end_angle=270,
                    )
                    offset(l5, amount=mount_thickness, side=Side.LEFT)
                make_face()
            with BuildLine():
                l6 = Line(
                    l1 @ 1,
                    (
                        WINDOW_FRAME_DEPTH,
                        -WINDOW_FRAME_SECOND_LOWER_HEIGHT * secondary_support_position,
                    ),
                )
                offset(amount=mount_thickness, side=Side.RIGHT)
            make_face()
        thicken(amount=mount_width)
    
    mount = part_mount.part + part_mount_support.part
    
    return mount


def make_rail(
    rail_type=RAIL_TYPE.PLAIN,
    gf_unit=1,
    slot_depth=3 * MM,
):
    num_archor = gf_unit + 1
    rail_length = GRIDFINITY_UNIT_WIDTH * gf_unit
    rail_width = GRIDFINITY_FRAME_WIDTH_HALF * 2

    def _archor_location(i):
        return i * GRIDFINITY_UNIT_WIDTH

    with BuildPart() as rail:
        with BuildSketch():
            Rectangle(rail_length, rail_width, align=(Align.MIN, Align.CENTER))
            with Locations(*[(_archor_location(i), 0) for i in range(num_archor)]):
                RegularPolygon(rail_width, side_count=6)
        _thicken_both = rail_type == RAIL_TYPE.PLAIN
        thicken(amount=-slot_depth, mode=Mode.ADD, both=_thicken_both)

        if rail_type in (RAIL_TYPE.GRIDFINITY_MIDDLE, RAIL_TYPE.GRIDFINITY_FRAME):
            _node_width = rail_width * sin(pi / 3)
            for i in range(num_archor):
                _sketch = _make_gridfinity_node_sketch(
                    Plane.XZ.shift_origin((_archor_location(i), 0, 0))
                )
                thicken(_sketch, amount=_node_width, mode=Mode.ADD, both=True)

        if rail_type == RAIL_TYPE.GRIDFINITY_FRAME:
            _sketch = _make_gridfinity_node_sketch(Plane.YZ)
            thicken(_sketch, amount=rail_length, mode=Mode.ADD)

    return rail.part


GRID_SIZE = 4, 2
MOUNT_THICKNESS = 5 * MM
MOUNT_WIDTH = 10 * MM
SLOT_DEPTH = 3 * MM

mount = make_mount(
    gf_unit=GRID_SIZE[1],
    mount_thickness=MOUNT_THICKNESS,
    mount_width=MOUNT_WIDTH,
    slot_depth=SLOT_DEPTH,
)
rails = [
    make_rail(rail_type=i, gf_unit=GRID_SIZE[0], slot_depth=SLOT_DEPTH)
    for i in RAIL_TYPE
]
model_set = pack([mount] + rails, 10 * MM, align_z=True)

exporter = Mesher()
exporter.add_shape(model_set)
exporter.add_code_to_metadata()
exporter.write("exports/window_mount.stl")
exporter.write("exports/window_mount.3mf")

show_all()