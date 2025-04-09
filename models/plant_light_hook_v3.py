from copy import copy
from math import cos, pi, radians, sin, sqrt, tan
from build123d import *
from ocp_vscode import *

TOLERANCE = 0.2 * MM


class LightHookPart(BasePartObject):
    THICKNESS = 5 * MM
    HEAD_INNER_RADIUS = 3.4 * MM / 2
    HEAD_OUTER_RADIUS = 8 * MM / 2
    HEAD_SLOT_WIDTH = 2.3 * MM
    ARM_LENGTH = 60 * MM
    ARM_WIDTH = HEAD_OUTER_RADIUS * 2
    JOINT_OUTER_RADIUS = 6 * MM

    def __init__(self, **kwargs):
        with BuildPart() as part:
            Box(
                self.ARM_WIDTH,
                self.ARM_LENGTH - self.ARM_WIDTH / 2,
                self.THICKNESS / 2,
                align=(Align.CENTER, Align.MIN, Align.MIN),
            )
            Cylinder(
                self.HEAD_OUTER_RADIUS,
                self.THICKNESS,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            Cylinder(
                self.HEAD_INNER_RADIUS,
                self.THICKNESS,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )
            with PolarLocations(
                radius=self.HEAD_OUTER_RADIUS, count=1, start_angle=180
            ):
                Box(
                    self.HEAD_OUTER_RADIUS,
                    self.HEAD_SLOT_WIDTH,
                    self.THICKNESS,
                    align=(Align.MAX, Align.CENTER, Align.MIN),
                    mode=Mode.SUBTRACT,
                )
            with Locations(
                (0, self.ARM_LENGTH - self.JOINT_OUTER_RADIUS, self.THICKNESS)
            ):
                Cylinder(
                    self.JOINT_OUTER_RADIUS,
                    self.THICKNESS,
                    align=(Align.CENTER, Align.CENTER, Align.MAX),
                )
                Cylinder(
                    self.JOINT_OUTER_RADIUS,
                    self.THICKNESS / 2,
                    align=(Align.CENTER, Align.CENTER, Align.MAX),
                    mode=Mode.SUBTRACT,
                )
                Cylinder(
                    self.JOINT_OUTER_RADIUS / 2,
                    self.THICKNESS,
                    align=(Align.CENTER, Align.CENTER, Align.MAX),
                    mode=Mode.SUBTRACT,
                )
        super().__init__(part.part, **kwargs)


class LightHoist(BasePartObject):
    def __init__(self, hook_ins, **kwargs):
        joint_outer_radius = hook_ins.JOINT_OUTER_RADIUS
        joint_inner_radius = hook_ins.JOINT_OUTER_RADIUS / 2
        self.hole_radius = joint_inner_radius
        self.hole_wall_thickness = joint_outer_radius - joint_inner_radius
        joint_thickness = hook_ins.THICKNESS / 2
        hoist_length = (
            self.hole_wall_thickness * 2 + self.hole_radius * 2 + joint_outer_radius
        )
        hoist_width = hook_ins.JOINT_OUTER_RADIUS * 2
        self.hoist_thickness = joint_thickness * 6

        self.thread_pole_outer_radius = self.hole_radius - TOLERANCE
        self.thread_pole_inner_radius = self.thread_pole_outer_radius / 2

        with BuildPart() as part:
            Box(
                hoist_width,
                hoist_length,
                self.hoist_thickness,
                align=(Align.CENTER, Align.MIN, Align.CENTER),
            )
            Cylinder(joint_outer_radius, self.hoist_thickness)
            Box(
                hoist_width,
                hoist_width,
                joint_thickness * 2 + 3 * TOLERANCE,
                mode=Mode.SUBTRACT,
            )
            Cylinder(joint_inner_radius, self.hoist_thickness, mode=Mode.SUBTRACT)

            hole_center_height = (
                hoist_length - self.hole_wall_thickness - self.hole_radius
            )
            with BuildSketch(Plane.XY.move(Location((0, hole_center_height, 0)))):
                Circle(self.hole_radius + self.hole_wall_thickness / 2)
                Rectangle(
                    hoist_width / 2,
                    2 * self.hole_radius + self.hole_wall_thickness,
                    align=(Align.MIN, Align.CENTER),
                )
            thicken(
                amount=(self.hoist_thickness - self.hole_wall_thickness) / 2,
                # amount=self.hoist_thickness / 2,
                both=True,
                mode=Mode.SUBTRACT,
            )

            with BuildSketch(Plane.XY.move(Location((0, hole_center_height, 0)))):
                Circle(self.hole_radius)
                Rectangle(
                    self.hole_radius * 2,
                    self.hole_radius,
                    align=(Align.CENTER, Align.MIN),
                    mode=Mode.SUBTRACT,
                )
                Rectangle(
                    self.hole_radius + self.hole_wall_thickness,
                    self.hole_radius,
                    align=(Align.MIN, Align.MAX),
                )
            thicken(amount=self.hoist_thickness / 2, both=True, mode=Mode.SUBTRACT)

            with BuildSketch(Plane.ZX.move(Location((0, hoist_length, 0)))):
                Circle(1 * MM)
                Rectangle(0.6 * MM, hoist_width / 2, align=((Align.CENTER, Align.MIN)))
            thicken(
                amount=-self.hole_wall_thickness - 2 * self.hole_radius,
                mode=Mode.SUBTRACT,
            )

        super().__init__(part.part, **kwargs)


class LightThreadPole(BasePartObject):
    EXTENDED_LENGTH = 15 * MM

    def __init__(self, hoist_ins, **kwargs):
        outer_radius = hoist_ins.thread_pole_outer_radius
        inner_radius = hoist_ins.thread_pole_inner_radius
        total_length = hoist_ins.hoist_thickness + 2 * self.EXTENDED_LENGTH

        with BuildPart() as part:
            Cylinder(
                inner_radius,
                hoist_ins.hoist_thickness / 2,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            with Locations((0, 0, hoist_ins.hoist_thickness / 2)):
                Cylinder(
                    outer_radius,
                    total_length / 2 - hoist_ins.hoist_thickness,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                )
                Cylinder(
                    outer_radius,
                    hoist.hole_wall_thickness * 1,
                    align=(Align.CENTER, Align.CENTER, Align.MAX),
                )
                Box(
                    outer_radius * 2,
                    outer_radius,
                    hoist.hole_wall_thickness / 2,
                    align=(Align.CENTER, Align.MIN, Align.MAX),
                    mode=Mode.SUBTRACT,
                )
            # Box(
            #     inner_radius * 2,
            #     inner_radius,
            #     hoist.hole_wall_thickness / 2,
            #     align=(Align.CENTER, Align.MIN, Align.MIN),
            #     mode=Mode.SUBTRACT,
            # )
            mirror(about=Plane.XY)

        super().__init__(part.part, **kwargs)


class LightJointPole(BasePartObject):
    def __init__(self, hoist_ins, **kwargs):
        with BuildPart() as part:
            Cylinder(
                hoist_ins.hole_radius - TOLERANCE,
                hoist_ins.hoist_thickness,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
        super().__init__(part.part, **kwargs)


hook = LightHookPart()
hoist = LightHoist(hook)
thread_pole = LightThreadPole(hoist)
joint_pole = LightJointPole(hoist)
all_parts = pack(
    [hook, hook, hoist, thread_pole, joint_pole], padding=5 * MM, align_z=True
)

exporter = Mesher()
exporter.add_shape(all_parts)
exporter.add_code_to_metadata()
exporter.write("exports/plant_light_hook_v3.stl")
exporter.write("exports/plant_light_hook_v3.3mf")

show_all()
