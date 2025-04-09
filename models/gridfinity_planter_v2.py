from copy import copy
from enum import Enum
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

WATER_LEVEL_INDICATOR_SIZE = 15 * MM
WATER_LEVEL_INDICATOR_BLOCK_HEIGHT = 10 * MM
WATER_LEVEL_INDICATOR_TOLERANCE = 0.5 * MM
WATER_LEVEL_INDICATOR_POLE_RADIUS = 1.5 * MM


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


class SurfaceDecro(BasePartObject):
    def __init__(self, length, height, thickness, **kwargs):
        num = floor(length / thickness * 2)
        decro_radius = length / num / 2

        def _hole_locations(mode=Mode.ADD):
            for i in range(0 if mode == Mode.ADD else 1, num + 1, 2):
                yield i * 2 * decro_radius - length / 2, 0, 0

        with BuildPart() as part:
            with BuildSketch(Plane.XZ.move(Location((0, height / 2, decro_radius)))):
                Rectangle(length, thickness / 4 * 3, align=(Align.CENTER, Align.MAX))
                for mode in (Mode.ADD, Mode.SUBTRACT):
                    with Locations(list(_hole_locations(mode=mode))):
                        Circle(decro_radius, mode=mode)
                Rectangle(
                    length,
                    thickness * 2,
                    align=(Align.CENTER, Align.CENTER),
                    mode=Mode.INTERSECT,
                )
            thicken(amount=height)

        super().__init__(part.part, **kwargs)


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
    with_surface_decro=False,
    with_water_level_indicator=False,
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
        if with_water_level_indicator:
            wli_plane_shift_z = (
                GF_BASE_TOTAL_HEIGHT
                + bottom_thickness
            )
            wli_plane = Plane.XY.move(
                    Location(
                        (
                            (width_x - WATER_LEVEL_INDICATOR_SIZE) / 2,
                            (width_y - WATER_LEVEL_INDICATOR_SIZE) / 2,
                            wli_plane_shift_z,
                        )
                    )
                )
            with BuildSketch(wli_plane) as sketch_water_level_indicator_slot:
                rect = Rectangle(WATER_LEVEL_INDICATOR_SIZE, WATER_LEVEL_INDICATOR_SIZE)
                if round_conner:
                    fillet(rect.vertices(), radius=GF_BOX_RADIUS)
                offset(amount=-wall_thickness, mode=Mode.SUBTRACT)
            thicken_length = (
                height_unit * GF_UNIT_HEIGHT
                - wli_plane_shift_z
                - GF_STACKING_LIP_SLICE_SIZE
                + wall_thickness
                - WATER_LEVEL_INDICATOR_BLOCK_HEIGHT
                - WATER_LEVEL_INDICATOR_TOLERANCE * 2
            )
            thicken(
                sketch_water_level_indicator_slot.sketch,
                amount=thicken_length,
                mode=Mode.ADD,
            )
            with BuildPart(wli_plane, mode=Mode.SUBTRACT):
                Box(wall_thickness, WATER_LEVEL_INDICATOR_SIZE / 2, height=WATER_LEVEL_INDICATOR_SIZE,
                    align=(Align.CENTER, Align.MAX, Align.MIN))
                Box(WATER_LEVEL_INDICATOR_SIZE / 2, wall_thickness, height=WATER_LEVEL_INDICATOR_SIZE,
                    align=(Align.MAX, Align.CENTER, Align.MIN))

        if with_surface_decro:
            decro_height = (
                height_unit * GF_UNIT_HEIGHT - GF_BASE_TOTAL_HEIGHT - wall_thickness
            )
            decro_center_z = (
                decro_height / 2 + GF_BASE_TOTAL_HEIGHT + wall_thickness / 2
            )
            _x_shift = width_x / 2 - wall_thickness / 2
            _y_shift = width_y / 2 - wall_thickness / 2
            planes = (
                (Plane.YZ.move(Location((_x_shift, 0, decro_center_z)))),
                (-Plane.YZ.move(Location((-_x_shift, 0, decro_center_z)))),
                (-Plane.XZ.move(Location((0, _y_shift, decro_center_z)))),
                (Plane.XZ.move(Location((0, -_y_shift, decro_center_z)))),
            )
            with BuildPart(*planes, mode=Mode.SUBTRACT) as part_decro:
                Box(width_y - 2 * GF_BOX_RADIUS, decro_height, wall_thickness)
                SurfaceDecro(
                    width_y - 2 * GF_BOX_RADIUS,
                    decro_height,
                    wall_thickness,
                    mode=Mode.SUBTRACT,
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
    with_water_level_indicator=True,
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
        with_surface_decro=False,
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
    if with_water_level_indicator:
        with BuildPart(
            Plane.XY.move(Location(
                (
                    (size_x * GF_UNIT_WIDTH - WATER_LEVEL_INDICATOR_SIZE) / 2,
                    (size_y * GF_UNIT_WIDTH - WATER_LEVEL_INDICATOR_SIZE) / 2,
                    0
                )
            ))
        ) as part_wli_hole:
            Cylinder(WATER_LEVEL_INDICATOR_POLE_RADIUS + WATER_LEVEL_INDICATOR_TOLERANCE, GF_UNIT_HEIGHT * 2)
        box -= part_wli_hole.part
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


def _make_hydroponic_hole(
    radius, cover_thickness, thicken_times=2, fillet_bottom=False
):
    with BuildPart() as part_1:
        with BuildSketch():
            circle = Circle(radius + cover_thickness)
        shape = thicken(amount=-cover_thickness * thicken_times)
    with BuildPart() as part_2:
        with BuildSketch():
            circle = Circle(radius + cover_thickness)
            offset(amount=-cover_thickness, mode=Mode.SUBTRACT)
        shape = thicken(amount=-cover_thickness * thicken_times)
        fillet(shape.edges().sort_by(Axis.Z)[-1], radius=cover_thickness / 2 - 0.01)
        if fillet_bottom:
            fillet(shape.edges().sort_by(Axis.Z)[1], radius=cover_thickness / 2 - 0.01)
    return part_1.part - part_2.part


def _make_hydroponic_holes(
    radius,
    cover_thickness,
    num_x,
    num_y,
    hole_locator,
):
    locations = [hole_locator(i, j) for j, i in product(range(num_y), range(num_x))]
    holes = [
        _make_hydroponic_hole(
            radius, cover_thickness, fillet_bottom=True, thicken_times=1
        ).move(Location(location))
        for location in locations
    ]
    return sum(holes[1:], start=holes[0])


def make_water_level_indicator(gf_unit, wall_thickness=1 * MM):
    with BuildPart() as part:
        box_size = WATER_LEVEL_INDICATOR_SIZE - wall_thickness * 2 - WATER_LEVEL_INDICATOR_TOLERANCE * 2
        box_corner_radius = GF_BOX_RADIUS - wall_thickness - WATER_LEVEL_INDICATOR_TOLERANCE
        with BuildSketch(Plane.XY):
            rect = Rectangle(box_size, box_size)
            fillet(rect.vertices(), radius=box_corner_radius)
        thicken(amount=WATER_LEVEL_INDICATOR_BLOCK_HEIGHT / 2, both=True)
        # Box(box_size - wall_thickness, box_size - wall_thickness,
        #     WATER_LEVEL_INDICATOR_BLOCK_HEIGHT - wall_thickness, 
        #     mode=Mode.SUBTRACT)
        pole_height = gf_unit * GF_UNIT_HEIGHT - WATER_LEVEL_INDICATOR_BLOCK_HEIGHT
        with Locations((0, 0, WATER_LEVEL_INDICATOR_BLOCK_HEIGHT / 2)):
            Cylinder(WATER_LEVEL_INDICATOR_POLE_RADIUS, pole_height,
                        align=(Align.CENTER, Align.CENTER, Align.MIN))
        # with Locations((0, 0, (WATER_LEVEL_INDICATOR_BLOCK_HEIGHT-wall_thickness) / 2)):
        #     Cylinder(WATER_LEVEL_INDICATOR_POLE_RADIUS - wall_thickness / 2, pole_height,
        #             align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    return part.part


def make_planter_plate(
    gf_unit_x=4,
    gf_unit_y=3,
    gf_unit_z=6,
    cover_thickness=1 * MM,
    wall_thickness=1 * MM,
    with_stack_lip=True,
    with_surface_decro=False,
    with_water_level_indicator=False,
    plant_min_width=55 * MM,
    hole_radius=18 * MM,
):
    box = make_gf_box(
        gf_unit_x,
        gf_unit_y,
        gf_unit_z,
        wall_thickness=wall_thickness,
        bottom_thickness=cover_thickness,
        with_surface_decro=with_surface_decro,
        with_water_level_indicator=with_water_level_indicator
    )

    edge_delta = GF_UNIT_WITDH_TOLERANCE * 2
    if with_stack_lip:
        edge_delta += GF_STACKING_LIP_SLICE_SIZE * 2
    else:
        edge_delta += wall_thickness * 2
    cover_x_max = gf_unit_x * GF_UNIT_WIDTH - edge_delta
    cover_y_max = gf_unit_y * GF_UNIT_WIDTH - edge_delta
    hole_width = hole_radius * 2
    num_x = floor((cover_x_max - hole_width) / plant_min_width) + 1
    num_y = floor((cover_y_max - hole_width) / plant_min_width) + 1

    def _cal_gap(total, num):
        gap_fix = 0
        total -= hole_width * num
        interval_num = num + 1
        gap = total / interval_num
        if gap < (plant_min_width - hole_width):
            gap_fix = plant_min_width - hole_width
            gap = (total - gap_fix * (num - 1)) / 2
            gap_fix -= gap
        return gap, gap_fix

    gap_x, gap_fix_x = _cal_gap(cover_x_max, num_x)
    gap_y, gap_fix_y = _cal_gap(cover_y_max, num_y)

    def _support_pillar_locator(i, j):
        x = (
            gap_x
            - cover_x_max / 2
            + hole_width
            + (gap_x + gap_fix_x) / 2
            + i * (hole_width + gap_x + gap_fix_x)
        )
        y = (
            gap_y
            - cover_y_max / 2
            + hole_width
            + (gap_y + gap_fix_y) / 2
            + j * (hole_width + gap_y + gap_fix_y)
        )
        return (x, y)

    plate = make_gf_cover(
        gf_unit_x,
        gf_unit_y,
        cover_thickness=cover_thickness,
        wall_thickness=wall_thickness,
        with_stack_lip=with_stack_lip,
        with_water_level_indicator=with_water_level_indicator,
        supporting_pillar_locations=[
            _support_pillar_locator(i, j)
            for i, j in product(range(num_x - 1), range(num_y - 1))
        ],
    )

    def _hole_locator(i, j):
        x = hole_width / 2 - cover_x_max / 2 + gap_x
        y = hole_width / 2 - cover_y_max / 2 + gap_y
        x += i * (hole_width + gap_x + gap_fix_x)
        y += j * (hole_width + gap_y + gap_fix_y)
        return (x, y)

    plate -= _make_hydroponic_holes(
        radius=hole_radius,
        cover_thickness=cover_thickness,
        num_x=num_x,
        num_y=num_y,
        hole_locator=_hole_locator,
    ).move(Location((0, 0, GF_BASE_TOTAL_HEIGHT + cover_thickness)))

    parts = [box, plate]

    if with_water_level_indicator:
        water_level_indicator = make_water_level_indicator(
            gf_unit=gf_unit_z,
            wall_thickness=wall_thickness,
        )
        parts.append(water_level_indicator)

    return parts


# box = make_gf_box(
#     2,
#     2,
#     10,
#     round_conner=True,
#     wall_thickness=2 * MM,
#     bottom_thickness=2 * MM,
#     with_stack_lip=True,
#     with_surface_decro=True,
#     with_water_level_indicator=True,
# )

# cover = make_gf_cover(
#     2,
#     2,
#     wall_thickness=2 * MM,
#     cover_thickness=2 * MM,
#     with_stack_lip=True,
#     with_water_level_indicator=True,
# )

# indicator = make_water_level_indicator(
#     gf_unit=10,
#     wall_thickness=2 * MM,
# )

kit = make_planter_plate(
    gf_unit_x=2,
    gf_unit_y=2,
    gf_unit_z=10,
    cover_thickness=2 * MM,
    wall_thickness=2 * MM,
    with_stack_lip=False,
    with_surface_decro=False,
    with_water_level_indicator=True,
    plant_min_width=48 * MM,
    hole_radius=18 * MM,
)

seed_starter_kit = pack([x for x in kit if x], 10 * MM, align_z=True)

exporter = Mesher()
exporter.add_shape(seed_starter_kit)
exporter.add_code_to_metadata()
exporter.write("exports/gridfinity_planter_v2.stl")
exporter.write("exports/gridfinity_planter_v2.3mf")

show_all()
