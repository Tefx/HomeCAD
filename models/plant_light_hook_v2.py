from copy import copy
from math import cos, pi, radians, sin, sqrt, tan
from build123d import *
from ocp_vscode import *


JOINT_RADIUS_OUTER = 6 * MM
JOINT_RADIUS_INNER = 4 * MM
JOINT_ANGLE_NUMBER = 12
JOINT_SLOT_WIDTH = 3 * MM
JOINT_TOLERANCE = 0.2 * MM


class HookGearInnerSketch(BaseSketchObject):
    INNER_RADIUS_RATIO = 0.5

    def __init__(self, is_inside=False, **kwargs):
        tooth_number = JOINT_ANGLE_NUMBER
        radius = JOINT_RADIUS_INNER
        tooth_width_half = sin(pi / tooth_number) * radius * self.INNER_RADIUS_RATIO
        tooth_height = (
            radius - cos(pi / tooth_number) * radius * self.INNER_RADIUS_RATIO
        )
        inner_circle_radius = radius * self.INNER_RADIUS_RATIO
        if is_inside:
            tooth_width_half -= JOINT_TOLERANCE
            tooth_height -= JOINT_TOLERANCE
            inner_circle_radius -= JOINT_TOLERANCE
        with BuildSketch() as sketch:
            with PolarLocations(radius=radius - JOINT_TOLERANCE, count=tooth_number):
                Ellipse(
                    tooth_height,
                    tooth_width_half,
                    align=(Align.MAX, Align.CENTER),
                )
            Circle(inner_circle_radius)
        super().__init__(sketch.sketch, **kwargs)


class HookGearInnerPart(BasePartObject):
    def __init__(self, length=5 * MM, is_inside=False, **kwargs):
        with BuildPart() as part:
            with BuildSketch() as sketch:
                HookGearInnerSketch(is_inside=is_inside)
            thicken(amount=length / 2, both=True)
        super().__init__(part.part, **kwargs)


class HookGearOuterPart(BasePartObject):
    def __init__(self, thickness=5 * MM, **kwargs):
        with BuildPart() as part:
            Cylinder(JOINT_RADIUS_OUTER, thickness)
            HookGearInnerPart(length=thickness, mode=Mode.SUBTRACT)
        super().__init__(part.part, **kwargs)


class LightHookSketch(BaseSketchObject):
    LIGHT_SLICE_HEIGHT = 21 * MM
    LIGHT_SLICE_WIDTH = 21 * MM
    INSIDE_HOOK_SIZE = 4 * MM

    def __init__(self, thickness=5 * MM, **kwargs):
        with BuildSketch() as sketch:
            with BuildLine() as line:
                l1 = Line((0, 0), (self.LIGHT_SLICE_WIDTH / 2, 0))
                l2 = Line(
                    l1 @ 1, (self.LIGHT_SLICE_WIDTH / 2, -self.LIGHT_SLICE_HEIGHT)
                )
                l3 = Line(
                    l2 @ 1,
                    (
                        self.LIGHT_SLICE_WIDTH / 2 - self.INSIDE_HOOK_SIZE,
                        -self.LIGHT_SLICE_HEIGHT,
                    ),
                )
                offset(amount=thickness, side=Side.LEFT)
            s = make_face()
            chamfer(
                s.vertices().sort_by(Axis.Y)[0],
                length=thickness,
                length2=self.INSIDE_HOOK_SIZE,
            )
            Rectangle(
                min(JOINT_RADIUS_OUTER * 2, self.LIGHT_SLICE_WIDTH + thickness * 2),
                JOINT_RADIUS_OUTER + thickness,
                align=(Align.CENTER, Align.MIN),
            )
            with Locations((0, JOINT_RADIUS_OUTER + thickness, 0)):
                Circle(JOINT_RADIUS_OUTER)
                HookGearInnerSketch(mode=Mode.SUBTRACT)
            mirror(about=Plane.YZ)
        super().__init__(obj=sketch.sketch, **kwargs)


class LightHookPart(BasePartObject):
    def __init__(self, thickness=5 * MM, width=15 * MM, **kwargs):
        self.hook_thickness = thickness
        self.hook_width = width
        with BuildPart() as part:
            with BuildSketch() as sketch:
                LightHookSketch(
                    thickness=thickness, **kwargs, align=(Align.CENTER, Align.MAX)
                )
            thicken(amount=width / 2, both=True)
            with Locations((0, -JOINT_RADIUS_OUTER, 0)):
                Box(
                    JOINT_RADIUS_OUTER * 2,
                    JOINT_RADIUS_OUTER * 2,
                    JOINT_SLOT_WIDTH,
                    mode=Mode.SUBTRACT,
                )
        super().__init__(part.part, **kwargs)

    @property
    def min_offset(self):
        return max(
            0,
            LightHookSketch.LIGHT_SLICE_WIDTH / 2
            + self.hook_thickness
            - JOINT_RADIUS_OUTER,
        )


class ConnectorPart(BasePartObject):
    def __init__(
        self, gantry_thickness=5 * MM, gantry_width=15 * MM, center_slot=True, **kwargs
    ):
        _small_offset = gantry_thickness / 4
        with BuildPart() as part:
            Box(
                JOINT_RADIUS_OUTER * 2,
                max(JOINT_RADIUS_OUTER + _small_offset, gantry_thickness),
                gantry_width,
                align=(Align.CENTER, Align.MAX, Align.CENTER),
            )
            with Locations((0, -gantry_thickness / 4, 0)):
                Cylinder(
                    JOINT_RADIUS_OUTER,
                    gantry_width,
                    align=(Align.CENTER, Align.MAX, Align.CENTER),
                )
                with Locations((0, -JOINT_RADIUS_OUTER, 0)):
                    HookGearInnerPart(
                        length=gantry_width,
                        is_inside=False,
                        mode=Mode.SUBTRACT,
                        align=(Align.CENTER, Align.CENTER, Align.CENTER),
                    )
                if center_slot:
                    Cylinder(
                        JOINT_RADIUS_OUTER,
                        align=(Align.CENTER, Align.MAX, Align.CENTER),
                        height=JOINT_SLOT_WIDTH,
                        mode=Mode.SUBTRACT,
                    )
                    with Locations((0, -JOINT_RADIUS_OUTER, 0)):
                        if gantry_thickness > JOINT_RADIUS_OUTER + _small_offset:
                            Box(
                                JOINT_RADIUS_OUTER * 2,
                                gantry_thickness - JOINT_RADIUS_OUTER - _small_offset,
                                height=JOINT_SLOT_WIDTH,
                                align=(Align.CENTER, Align.MAX, Align.CENTER),
                                mode=Mode.SUBTRACT,
                            )
                        else:
                            Box(
                                JOINT_RADIUS_OUTER * 2,
                                JOINT_RADIUS_OUTER - gantry_thickness + _small_offset,
                                height=JOINT_SLOT_WIDTH,
                                align=(Align.CENTER, Align.MIN, Align.CENTER),
                                mode=Mode.SUBTRACT,
                            )
                else:
                    Box(
                        JOINT_RADIUS_OUTER * 2,
                        max(JOINT_RADIUS_OUTER * 2, gantry_thickness) * 2,
                        align=(Align.CENTER, Align.CENTER, Align.MAX),
                        height=gantry_width / 2,
                        mode=Mode.SUBTRACT,
                    )
        super().__init__(part.part, **kwargs)


class ShelfMountGantryHalfPart(BasePartObject):
    SHELF_PLANE_WIDTH = 216 * MM
    SHELF_PLANE_THINKNESS = 20 * MM
    INSIDE_HOOK_SIZE = 10 * MM

    def __init__(
        self,
        thickness=10 * MM,
        width=10 * MM,
        hook_number=2,
        light_hook=None,
        **kwargs,
    ):
        self.mount_thickness = thickness
        self.mount_width = width
        with BuildPart() as part:
            with BuildSketch() as sketch:
                with BuildLine():
                    l1 = Line((0, 0), (self.SHELF_PLANE_WIDTH / 2, 0))
                    l2 = Line(
                        l1 @ 1, (self.SHELF_PLANE_WIDTH / 2, self.SHELF_PLANE_THINKNESS)
                    )
                    l3 = Line(
                        l2 @ 1,
                        (
                            self.SHELF_PLANE_WIDTH / 2 - self.INSIDE_HOOK_SIZE,
                            self.SHELF_PLANE_THINKNESS,
                        ),
                    )
                    offset(amount=thickness, side=Side.RIGHT)
                s = make_face()
                fillet(
                    s.vertices().sort_by(Axis.Y)[-2],
                    radius=min(self.INSIDE_HOOK_SIZE, thickness),
                )
            thicken(amount=width / 2, both=True)
            _reserved = JOINT_RADIUS_OUTER
            if light_hook is not None:
                _reserved += light_hook.min_offset
            joint_gap = (self.SHELF_PLANE_WIDTH / 2 - _reserved) / hook_number
            for i in range(hook_number + 1):
                if i == 0:
                    align = (Align.CENTER, Align.MAX, Align.MAX)
                    center_slot = False
                else:
                    align = (Align.CENTER, Align.MAX, Align.CENTER)
                    center_slot = True
                with Locations((joint_gap * i, 0, 0)):
                    Box(
                        JOINT_RADIUS_OUTER * 2,
                        thickness,
                        width,
                        align=(Align.CENTER, Align.MAX, Align.CENTER),
                        mode=Mode.SUBTRACT,
                    )
                    ConnectorPart(
                        gantry_thickness=thickness,
                        gantry_width=width,
                        mode=Mode.ADD,
                        center_slot=center_slot,
                        align=align,
                    )
        super().__init__(part=part.part, **kwargs)


class ShelfMountHoistPart(BasePartObject):
    def __init__(self, width=10 * MM, length=0, light_hook=None, **kwargs):
        if light_hook is not None:
            length = max(length, light_hook.min_offset)
        with BuildPart() as part:
            if length > 0:
                Box(
                    length / 2,
                    JOINT_RADIUS_OUTER * 2,
                    width,
                    align=(Align.MIN, Align.CENTER, Align.CENTER),
                )
            with Locations((length / 2 + JOINT_RADIUS_OUTER, 0, 0)):
                Box(
                    JOINT_RADIUS_OUTER,
                    JOINT_RADIUS_OUTER * 2,
                    JOINT_SLOT_WIDTH,
                    align=(Align.MAX, Align.CENTER, Align.CENTER),
                )
                Cylinder(JOINT_RADIUS_OUTER, JOINT_SLOT_WIDTH, mode=Mode.SUBTRACT)
                HookGearOuterPart(thickness=JOINT_SLOT_WIDTH, mode=Mode.ADD)
            mirror(about=Plane.YZ)
        super().__init__(part=part.part, **kwargs)


light_hook = LightHookPart(thickness=3 * MM, width=10 * MM)
gantry = ShelfMountGantryHalfPart(
    thickness=6 * MM, width=10 * MM, light_hook=light_hook
)
hoist = ShelfMountHoistPart(width=10 * MM, light_hook=light_hook)
hook_inner = HookGearInnerPart(length=light_hook.hook_width, is_inside=True)

all_parts = pack([gantry, light_hook, hoist, hook_inner], 10 * MM, align_z=True)

exporter = Mesher()
exporter.add_shape(all_parts)
exporter.add_code_to_metadata()
exporter.write("exports/plant_light_hook_v2.stl")
exporter.write("exports/plant_light_hook_v2.3mf")

show_all()
