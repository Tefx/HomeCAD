from copy import copy
from functools import reduce
from itertools import product
from math import ceil, floor
from build123d import *
from ocp_vscode import *
from bd_warehouse.fastener import *

GF_UNIT_HEIGHT = 7 * MM
GF_UNIT_WIDTH = 42 * MM
GF_BOX_UNIT_WIDTH = 41.5 * MM
GF_BOX_RADIUS = 7.5 * MM / 2
GF_BASE_PART_SIZE = (0.8, 1.8, 2.15)
GF_BASE_SLICE_SIZE = GF_BASE_PART_SIZE[0] + GF_BASE_PART_SIZE[2]
GF_STACKING_LIP_PART_SIZE = (0.7, 1.8, 1.9)
GF_STACKING_LIP_SLICE_SIZE = GF_STACKING_LIP_PART_SIZE[0] + GF_STACKING_LIP_PART_SIZE[2]

GF_BASE_TOTAL_HEIGHT = sum(GF_BASE_PART_SIZE)
GF_STACKING_LIP_TOTAL_HEIGHT = sum(GF_STACKING_LIP_PART_SIZE)


def _cal_gf_struct_spec(unit_width, init_height, init_radius, part_size):
    half_width_4 = unit_width / 2
    half_height_4 = init_height
    corner_radius_4 = init_radius
    half_width_3 = half_width_4 - part_size[2]
    half_height_3 = half_height_4 - part_size[2]
    corner_radius_3 = corner_radius_4 - part_size[2]
    half_width_2 = half_width_3
    half_height_2 = half_height_3 - part_size[1]
    corner_radius_2 = corner_radius_3
    half_width_1 = half_width_2 - part_size[0]
    half_height_1 = half_height_2 - part_size[0]
    corner_radius_1 = corner_radius_2
    return [
        (half_width_1, half_height_1, corner_radius_1),
        (half_width_2, half_height_2, corner_radius_2),
        (half_width_3, half_height_3, corner_radius_3),
        (half_width_4, half_height_4, corner_radius_4),
    ]


GF_BASE_SIZE = _cal_gf_struct_spec(
    GF_BOX_UNIT_WIDTH,
    GF_BASE_TOTAL_HEIGHT,
    GF_BOX_RADIUS,
    GF_BASE_PART_SIZE,
)

GF_STACKING_LIP_SIZE = _cal_gf_struct_spec(
    GF_BOX_UNIT_WIDTH,
    GF_STACKING_LIP_TOTAL_HEIGHT,
    GF_BOX_RADIUS,
    GF_STACKING_LIP_PART_SIZE,
)

GF_STACKING_LIP_SIZE.insert(
    0, (GF_BOX_UNIT_WIDTH / 2, -GF_STACKING_LIP_SLICE_SIZE, GF_BOX_RADIUS)
)

GF_UNIT_WITDH_TOLERANCE = (GF_UNIT_WIDTH - GF_BOX_UNIT_WIDTH) / 2


def _make_gf_base(origin=None):
    if origin is not None:
        plane = Plane.XY.shift_origin(origin)
    else:
        plane = Plane.XY
    with BuildPart(plane) as part:
        for half_width, height, radius in GF_BASE_SIZE:
            with BuildSketch(plane.offset(height)) as sketch:
                rect = Rectangle(half_width * 2, half_width * 2)
                if radius > 0:
                    fillet(rect.vertices(), radius)
        loft(ruled=True)
    return part.part


def _make_gf_stacking_lip(size_x, size_y, height_unit, cut_before_height=0):
    plane = Plane.XY.offset(height_unit * GF_UNIT_HEIGHT - GF_STACKING_LIP_SLICE_SIZE)
    with BuildPart(plane) as part_1:
        width_x = size_x * GF_UNIT_WIDTH - GF_UNIT_WITDH_TOLERANCE * 2
        width_y = size_y * GF_UNIT_WIDTH - GF_UNIT_WITDH_TOLERANCE * 2
        box = Box(
            width_x,
            width_y,
            GF_STACKING_LIP_TOTAL_HEIGHT + GF_STACKING_LIP_SLICE_SIZE,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        fillet(box.edges().sort_by()[4:8], radius=GF_BOX_RADIUS)
        plane = plane.offset(GF_STACKING_LIP_SLICE_SIZE)
        for half_width, height, radius in GF_STACKING_LIP_SIZE:
            width_x = (size_x - 1) * GF_UNIT_WIDTH + half_width * 2
            width_y = (size_y - 1) * GF_UNIT_WIDTH + half_width * 2
            with BuildSketch(plane.offset(height)):
                rect = Rectangle(width_x, width_y)
                if radius > 0:
                    fillet(rect.vertices(), radius)
        loft(ruled=True, mode=Mode.SUBTRACT)
    part = part_1.part
    if cut_before_height > 0:
        box = Box(
            size_x * GF_UNIT_WIDTH,
            size_y * GF_UNIT_WIDTH,
            cut_before_height,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        part -= box
    return part


def make_gf_box(
    size_x,
    size_y,
    height_unit=1,
    wall_thickness=1 * MM,
    bottom_thickness=1 * MM,
    round_conner=True,
    with_stack_lip=True,
):
    parts = []
    for i, j in product(range(size_x), range(size_y)):
        origin_x = i * GF_UNIT_WIDTH - size_x * GF_UNIT_WIDTH / 2 + GF_UNIT_WIDTH / 2
        origin_y = j * GF_UNIT_WIDTH - size_y * GF_UNIT_WIDTH / 2 + GF_UNIT_WIDTH / 2
        parts.append(_make_gf_base(origin=(origin_x, origin_y, 0)))
    with BuildPart() as part_upper:
        width_x = size_x * GF_UNIT_WIDTH - GF_UNIT_WITDH_TOLERANCE * 2
        width_y = size_y * GF_UNIT_WIDTH - GF_UNIT_WITDH_TOLERANCE * 2
        if bottom_thickness > 0:
            with BuildSketch(Plane.XY.offset(GF_BASE_TOTAL_HEIGHT)) as sketch_bottom:
                rect = Rectangle(width_x, width_y)
                if round_conner:
                    fillet(rect.vertices(), radius=GF_BOX_RADIUS)
            thicken(sketch_bottom.sketch, amount=bottom_thickness, mode=Mode.ADD)
        with BuildSketch(Plane.XY.offset(GF_BASE_TOTAL_HEIGHT)) as sketch_wall:
            rect = Rectangle(width_x, width_y)
            if round_conner:
                fillet(rect.vertices(), radius=GF_BOX_RADIUS)
            offset(amount=-wall_thickness, mode=Mode.SUBTRACT)
        thicken(
            sketch_wall.sketch,
            amount=height_unit * GF_UNIT_HEIGHT - GF_BASE_TOTAL_HEIGHT,
            mode=Mode.ADD,
        )
    part = sum(parts, start=part_upper.part)
    if with_stack_lip:
        part += _make_gf_stacking_lip(
            size_x, size_y, height_unit, cut_before_height=GF_BASE_TOTAL_HEIGHT
        )
    return part


def make_gf_cover(
    size_x,
    size_y,
    wall_thickness=1,
    cover_thickness=1,
    with_stack_lip=True,
    supporting_pillar_locations=None,
    supporting_pillar_radius=3.5 * MM,
    supporting_pillar_tolerance=0.1 * MM,
):
    box = make_gf_box(
        size_x,
        size_y,
        1,
        round_conner=True,
        bottom_thickness=cover_thickness,
        with_stack_lip=with_stack_lip,
    )
    with BuildPart() as part_hole_lower:
        with BuildSketch(Plane.XY.offset(GF_BASE_TOTAL_HEIGHT)):
            in_buffer = 2 * (
                GF_UNIT_WITDH_TOLERANCE + GF_BASE_SLICE_SIZE + wall_thickness
            )
            rect = Rectangle(
                size_x * GF_UNIT_WIDTH - in_buffer, size_y * GF_UNIT_WIDTH - in_buffer
            )
            # fillet(rect.vertices(), radius=GF_BOX_RADIUS - in_buffer / 2)
        thicken(amount=-GF_UNIT_HEIGHT)
    box -= part_hole_lower.part
    if supporting_pillar_locations:
        with BuildPart(Plane.XY.offset(GF_BASE_TOTAL_HEIGHT)) as part_support_pillar:
            with Locations(*supporting_pillar_locations):
                Cylinder(
                    supporting_pillar_radius + wall_thickness,
                    GF_BASE_TOTAL_HEIGHT,
                    align=(Align.CENTER, Align.CENTER, Align.MAX),
                )
                Cylinder(
                    supporting_pillar_radius + supporting_pillar_tolerance,
                    GF_BASE_TOTAL_HEIGHT,
                    align=(Align.CENTER, Align.CENTER, Align.MAX),
                    mode=Mode.SUBTRACT,
                )
        box += part_support_pillar.part
    return box


def _make_supporting_pillar(
    radius,
    height_unit,
    cover_thickness,
):
    height = (
        height_unit * GF_UNIT_HEIGHT
        - cover_thickness
        + GF_STACKING_LIP_TOTAL_HEIGHT
        - GF_BASE_TOTAL_HEIGHT
    )
    pillar = Cylinder(radius, height, align=(Align.CENTER, Align.CENTER, Align.MIN))
    base = Cone(
        radius * 2,
        radius,
        GF_UNIT_HEIGHT,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    return pillar + base


def _make_filling_hole(
    radius,
    outer_radius,
    cover_thickness,
):
    return Cone(
        radius,
        outer_radius,
        cover_thickness,
        align=(Align.CENTER, Align.CENTER, Align.MAX),
    )


def _make_filling_hole_cover(
    radius,
    cover_thickness,
    tolerance=0.2,
    indicator_radius=0,
):
    outer_radius = radius + cover_thickness
    with BuildPart() as part_cover:
        Cone(
            radius - tolerance,
            outer_radius - tolerance,
            cover_thickness,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        Cylinder(
            radius - tolerance,
            cover_thickness,
            align=(Align.CENTER, Align.CENTER, Align.MAX),
        )
        Cylinder(
            indicator_radius,
            cover_thickness * 2,
            mode=Mode.SUBTRACT,
        )
    return part_cover.part


def _make_water_indicator(
    cover_thickness,
    radius=2.5,
    height_unit=3,
    tolerance=0.5,
    floating_block_radius=10,
    floating_block_height=6,
):
    indicator_height = (
        height_unit * GF_UNIT_HEIGHT - GF_BASE_TOTAL_HEIGHT - cover_thickness + 5 * MM
    )
    with BuildPart() as part_indicator:
        Cylinder(
            floating_block_radius - tolerance,
            floating_block_height,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        Cylinder(
            radius - tolerance,
            indicator_height,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
    return part_indicator.part


def _make_seed_starter_hole(
    width, conner_radius, cover_thickness, thicken_times=2, fillet_bottom=False
):
    with BuildPart() as part_1:
        with BuildSketch():
            rect = Rectangle(width + cover_thickness * 2, width + cover_thickness * 2)
            fillet(rect.vertices(), radius=conner_radius + cover_thickness)
        shape = thicken(amount=-cover_thickness * thicken_times)
    with BuildPart() as part_2:
        with BuildSketch():
            rect = Rectangle(width + cover_thickness * 2, width + cover_thickness * 2)
            fillet(rect.vertices(), radius=conner_radius + cover_thickness)
            offset(amount=-cover_thickness, mode=Mode.SUBTRACT)
        shape = thicken(amount=-cover_thickness * thicken_times)
        fillet(shape.edges().sort_by(Axis.Z)[-1], radius=cover_thickness / 2 - 0.01)
        if fillet_bottom:
            fillet(
                shape.edges().sort_by(Axis.Z)[8:16], radius=cover_thickness / 2 - 0.01
            )
    return part_1.part - part_2.part


def _make_seed_starter_hole_cover(
    width,
    conner_radius,
    cover_thickness,
    handler_radius,
    handler_height,
    tolerance=0.1,
    handler_tolerance=0.1,
):
    cover_base = _make_seed_starter_hole(
        width - 2 * tolerance, conner_radius - tolerance, cover_thickness
    )
    handler = Cylinder(
        handler_radius,
        handler_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    def _make_center_part(_tolerance):
        with BuildPart() as part_cover:
            Cone(
                handler_radius * 2 - _tolerance,
                handler_radius - _tolerance,
                height=cover_thickness,
                align=(Align.CENTER, Align.CENTER, Align.MAX),
            )
            with Locations((0, 0, -cover_thickness)):
                Cylinder(
                    handler_radius * 2 - _tolerance,
                    cover_thickness,
                    align=(Align.CENTER, Align.CENTER, Align.MAX),
                )
        return part_cover.part

    return cover_base - _make_center_part(0), handler + _make_center_part(
        handler_tolerance
    )


def _make_seed_starter_hole_screw_cover(
    width,
    conner_radius,
    tolerance,
    cover_thickness,
    handler_radius,
    handler_height,
):
    cover_thicken_times = min(ceil(3 / cover_thickness), 2)
    screw = SetScrew(
        size="M6-1",
        length=cover_thickness * cover_thicken_times,
        simple=False,
        align=(Align.CENTER, Align.CENTER, Align.MAX),
    )
    handler = (
        Cylinder(
            handler_radius,
            handler_height,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        + Cylinder(
            2 * MM,
            cover_thickness * (cover_thicken_times + 1),
            align=(Align.CENTER, Align.CENTER, Align.MAX),
        )
        + screw
    )
    hole = Cylinder(
        screw.thread_diameter / 2 + 0.2,
        cover_thickness * cover_thicken_times,
        align=(Align.CENTER, Align.CENTER, Align.MAX),
    )
    thread = IsoThread(
        major_diameter=screw.thread_diameter + 0.1,
        pitch=screw.thread_pitch,
        length=screw.length,
        external=False,
        align=(Align.CENTER, Align.CENTER, Align.MAX),
        end_finishes=("square", "square"),
    )
    cover_base = (
        _make_seed_starter_hole(
            width - 2 * tolerance,
            conner_radius - tolerance,
            cover_thickness,
            thicken_times=cover_thicken_times,
        )
        - hole
    )
    return cover_base + thread, handler.move(Location((0, width / 2 + 10, 0)))


def _make_seed_starter_holes(
    width,
    conner_radius,
    cover_thickness,
    num_x,
    num_y,
    hole_locator,
    reserve_last=False,
):
    locations = [hole_locator(i, j) for j, i in product(range(num_y), range(num_x))]
    if reserve_last:
        locations.pop(num_x - 1)
    holes = [
        _make_seed_starter_hole(
            width, conner_radius, cover_thickness, fillet_bottom=True, thicken_times=1
        ).move(Location(location))
        for location in locations
    ]
    return sum(holes[1:], start=holes[0])


def make_seed_starter_plate(
    gf_unit_x=4,
    gf_unit_y=3,
    gf_unit_z=6,
    cover_thickness=1 * MM,
    wall_thickness=1 * MM,
    with_stack_lip=True,
    starter_min_width=55 * MM,
    support_hole_width=41.5 * MM,
    support_hole_conner_radius=10 * MM,
    filling_hole=True,
    filling_hole_in_new_row=True,
    filling_hole_radius=10 * MM,
    hole_cover_tolerance=0.2 * MM,
    hole_cover_hander_with_screw=True,
    hole_cover_handler_radius=3 * MM,
    hole_cover_handler_height=10 * MM,
    hole_cover_handler_tolerance=0.1 * MM,
    water_indicator_tolerance=0.5 * MM,
    water_indicator_floating_block_radius=None,
    water_indicator_floating_block_height=6 * MM,
    internal_supporting_pillar_radius=3.5 * MM,
    internal_supporting_pillar_tolerance=0.1 * MM,
):
    box = make_gf_box(
        gf_unit_x,
        gf_unit_y,
        gf_unit_z,
        wall_thickness=wall_thickness,
        bottom_thickness=cover_thickness,
    )

    edge_delta = GF_UNIT_WITDH_TOLERANCE * 2
    if with_stack_lip:
        edge_delta += GF_STACKING_LIP_SLICE_SIZE * 2
    else:
        edge_delta += wall_thickness * 2
    cover_x_max = gf_unit_x * GF_UNIT_WIDTH - edge_delta
    cover_y_max = gf_unit_y * GF_UNIT_WIDTH - edge_delta
    filling_hole_in_new_row = filling_hole_in_new_row and filling_hole
    filling_hole_outer_radius = filling_hole_radius + cover_thickness
    num_x = floor((cover_x_max - support_hole_width) / starter_min_width) + 1
    if filling_hole_in_new_row:
        num_y = (
            floor(
                (cover_y_max - support_hole_width - filling_hole_outer_radius * 2)
                / starter_min_width
            )
            + 1
        )
    else:
        num_y = floor((cover_y_max - support_hole_width) / starter_min_width) + 1

    def _cal_gap(total, num, filling_hole_num):
        gap_fix = 0
        total -= (
            filling_hole_outer_radius * 2 * filling_hole_num + support_hole_width * num
        )
        interval_num = num + filling_hole_num + 1
        gap = total / interval_num
        if gap < (starter_min_width - support_hole_width):
            gap_fix = starter_min_width - support_hole_width
            # gap = (total - starter_min_width * num + gap_fix) / interval_num
            gap = (total - gap_fix * (num - 1)) / (filling_hole_num + 2)
            gap_fix -= gap
        return gap, gap_fix

    gap_x, gap_fix_x = _cal_gap(cover_x_max, num_x, 0)
    gap_y, gap_fix_y = _cal_gap(cover_y_max, num_y, 1 if filling_hole_in_new_row else 0)

    def _support_pillar_locator(i, j):
        x = (
            gap_x
            - cover_x_max / 2
            + support_hole_width
            + (gap_x + gap_fix_x) / 2
            + i * (support_hole_width + gap_x + gap_fix_x)
        )
        y = (
            gap_y
            - cover_y_max / 2
            + support_hole_width
            + (gap_y + gap_fix_y) / 2
            + j * (support_hole_width + gap_y + gap_fix_y)
        )
        if filling_hole_in_new_row:
            y += filling_hole_outer_radius * 2 + gap_y
        return (x, y)

    plate = make_gf_cover(
        gf_unit_x,
        gf_unit_y,
        cover_thickness=cover_thickness,
        wall_thickness=wall_thickness,
        with_stack_lip=with_stack_lip,
        supporting_pillar_locations=[
            _support_pillar_locator(i, j)
            for i, j in product(range(num_x - 1), range(num_y - 1))
        ],
        supporting_pillar_radius=internal_supporting_pillar_radius,
        supporting_pillar_tolerance=internal_supporting_pillar_tolerance,
    )

    def _hole_locator(i, j):
        x = support_hole_width / 2 - cover_x_max / 2 + gap_x
        y = support_hole_width / 2 - cover_y_max / 2 + gap_y
        if filling_hole_in_new_row:
            y += filling_hole_outer_radius * 2 + gap_y
        x += i * (support_hole_width + gap_x + gap_fix_x)
        y += j * (support_hole_width + gap_y + gap_fix_y)
        return (x, y)

    plate -= _make_seed_starter_holes(
        width=support_hole_width,
        conner_radius=support_hole_conner_radius,
        cover_thickness=cover_thickness,
        num_x=num_x,
        num_y=num_y,
        hole_locator=_hole_locator,
        reserve_last=filling_hole and not filling_hole_in_new_row,
    ).move(Location((0, 0, GF_BASE_TOTAL_HEIGHT + cover_thickness)))

    if filling_hole:
        if filling_hole_in_new_row:
            filling_hole_position = Location(
                (
                    cover_x_max / 2 - gap_x - support_hole_width / 2,
                    -cover_y_max / 2 + gap_y + filling_hole_outer_radius,
                    GF_BASE_TOTAL_HEIGHT + cover_thickness,
                )
            )
        else:
            filling_hole_position = Location(
                (
                    *_hole_locator(num_x - 1, 0),
                    GF_BASE_TOTAL_HEIGHT + cover_thickness,
                )
            )

        plate -= _make_filling_hole(
            radius=filling_hole_radius,
            outer_radius=filling_hole_outer_radius,
            cover_thickness=cover_thickness,
        ).move(filling_hole_position)

    if hole_cover_hander_with_screw:
        starter_hole_cover, starter_hole_cover_handler = (
            _make_seed_starter_hole_screw_cover(
                width=support_hole_width,
                conner_radius=support_hole_conner_radius,
                tolerance=hole_cover_tolerance,
                cover_thickness=cover_thickness,
                handler_radius=hole_cover_handler_radius,
                handler_height=hole_cover_handler_height,
            )
        )
    else:
        starter_hole_cover, starter_hole_cover_handler = _make_seed_starter_hole_cover(
            width=support_hole_width,
            conner_radius=support_hole_conner_radius,
            cover_thickness=cover_thickness,
            handler_radius=hole_cover_handler_radius,
            handler_height=hole_cover_handler_height,
            tolerance=hole_cover_tolerance,
            handler_tolerance=hole_cover_handler_tolerance,
        )

    filling_hole_cover = _make_filling_hole_cover(
        radius=filling_hole_radius,
        cover_thickness=cover_thickness,
        tolerance=hole_cover_tolerance,
        indicator_radius=hole_cover_handler_radius,
    )

    if water_indicator_floating_block_radius is None:
        if filling_hole:
            water_indicator_floating_block_radius = filling_hole_radius - 0.2 * MM
        else:
            water_indicator_floating_block_radius = support_hole_width / 2 - 2 * MM

    water_indicator = _make_water_indicator(
        cover_thickness=cover_thickness,
        radius=2.5 * MM if hole_cover_hander_with_screw else hole_cover_handler_radius,
        height_unit=gf_unit_z,
        tolerance=water_indicator_tolerance,
        floating_block_radius=water_indicator_floating_block_radius,
        floating_block_height=water_indicator_floating_block_height,
    )

    supporting_pillar = _make_supporting_pillar(
        radius=internal_supporting_pillar_radius,
        height_unit=gf_unit_z,
        cover_thickness=cover_thickness,
    )

    return (
        box,
        plate,
        starter_hole_cover,
        starter_hole_cover_handler,
        filling_hole_cover,
        water_indicator,
        supporting_pillar,
    )


kit = make_seed_starter_plate(
    gf_unit_x=4,
    gf_unit_y=3,
    gf_unit_z=6,
    cover_thickness=2 * MM,
    wall_thickness=2 * MM,
    with_stack_lip=True,
    starter_min_width=55 * MM,
    # support_hole_width=42.23 * MM,
    # support_hole_conner_radius=10.44 * MM,
    support_hole_width=43 * MM,
    support_hole_conner_radius=10.825 * MM,
    filling_hole=True,
    filling_hole_in_new_row=True,
    filling_hole_radius=7.5 * MM,
    hole_cover_hander_with_screw=True,
    hole_cover_tolerance=0.2 * MM,
    hole_cover_handler_radius=3.5 * MM,
    hole_cover_handler_height=20 * MM,
    hole_cover_handler_tolerance=0.05 * MM,
    # water_indicator_tolerance=0.5 * MM,
    # water_indicator_floating_block_radius=10 * MM,
    # water_indicator_floating_block_height=6 * MM,
)

seed_starter_kit = pack([x for x in kit if x], 10 * MM, align_z=True)

exporter = Mesher()
exporter.add_shape(seed_starter_kit)
exporter.add_code_to_metadata()
exporter.write("exports/gridfinity_seed_starter.stl")
exporter.write("exports/gridfinity_seed_starter.3mf")

show_all()
