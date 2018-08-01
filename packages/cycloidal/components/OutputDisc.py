# Copyright (C) 2018  Martin Muehlhaeuser <github@mmone.de>

import adsk.core, adsk.fusion, traceback
import math
from . import helpers

class OutputDisc:
    def __init__(self, parent_compo, ui, ring_inner_radius, pin_circle_radius, bearing_plane, drive_config, printer_config):
        self.ui = ui
        self.ring_inner_radius = ring_inner_radius
        self.pin_circle_radius = pin_circle_radius
        self.bearing_plane = bearing_plane
        self.drive_config = drive_config
        self.printer_config = printer_config

        self.cage_race_gap = self.printer_config.ewToCm(2)
        self.cage_width = self.printer_config.ewToCm(3)

        occs = parent_compo.occurrences
        mat = adsk.core.Matrix3D.create()
        mat.translation = adsk.core.Vector3D.create(0.0, 0.0, self.bearing_plane.geometry.origin.z)
        newOcc = occs.addNewComponent(mat)

        self.compo = adsk.fusion.Component.cast(newOcc.component)
        self.compo.name = "Output Disc"
        self.CreateDisc()

    def CreateDisc(self):
        sketch = helpers.CreateSketch(self.compo, "Output Disc", True, False)

        helpers.AddCircle(sketch, 0,0,0, self.drive_config.shaft_diameter * 0.5 )
        helpers.AddCircle(sketch, 0,0,0, self.ring_inner_radius - self.cage_width - 2 * self.cage_race_gap )

        helpers.AddCircle(sketch,
            0, self.pin_circle_radius, 0,
            (self.drive_config.output_pin_diameter + self.drive_config.roller_diameter * 0.5) * 0.5
        )
        
        sketch.isComputeDeferred = False
        
        #self.ui.messageBox("origin {0} {1} {2}: ".format(self.bearing_plane.geometry.origin.x, self.bearing_plane.geometry.origin.y, self.bearing_plane.geometry.origin.z))

        extrude0 = helpers.SymmetricExtrude(self.compo,
            helpers.CreateCollection(
                sketch.profiles.item(1),
                sketch.profiles.item(2)
            ),
            self.drive_config.output_bearing_ball_diameter + 2 * 0.08,
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        )

        extrude2 = helpers.SymmetricExtrude(self.compo,
            helpers.CreateCollection(
                sketch.profiles.item(2)
            ),
            self.drive_config.output_bearing_ball_diameter + 2 * 0.08,
            adsk.fusion.FeatureOperations.CutFeatureOperation,
            0,
            [extrude0.bodies.item(0)]
        )

        out = helpers.CircularPattern(
            self.compo,
            helpers.CreateCollection(
                extrude2
            ),
            self.compo.zConstructionAxis,
            self.drive_config.disc_bolt_count,
            adsk.fusion.PatternComputeOptions.IdenticalPatternCompute
        )

        #filletEdges = adsk.core.ObjectCollection.create()

        #for e in range(0, out.bodies.item(0).concaveEdges.count):
        #    filletEdges.add(out.bodies.item(0).convexEdges.item(e))

        #out = helpers.FilletEdgesSimple(self.compo, filletEdges, 0.06)
        
        out.bodies.item(0).name = "Output Disc"

        self.CreateRace(out.bodies.item(0))
        self.CreateCage(sketch)

    def CreateRace(self, body):
        sketch = helpers.CreateSketch(self.compo,
            "Ball Profile", True, False, self.compo.xZConstructionPlane
        )
        sketch.isComputeDeferred = False
        helpers.AddCircle(
            sketch,
            self.ring_inner_radius - self.cage_width * 0.5 - self.cage_race_gap,
            0,
            0,
            self.drive_config.output_bearing_ball_diameter * 0.5,
            True
        )
        helpers.Revolve(self.compo,
            sketch.profiles.item(0),
            self.compo.zConstructionAxis,
            adsk.fusion.FeatureOperations.CutFeatureOperation
        )

    def CreateCage(self, sketch):
        helpers.AddCircle(sketch,
            0,0,0,
            self.ring_inner_radius - self.cage_width - self.cage_race_gap
        )

        helpers.AddCircle(sketch,
            0,0,0,
            self.ring_inner_radius - self.cage_race_gap
        )

        ball = helpers.CreateSketch(self.compo,
            "Ball", True, False, self.compo.xZConstructionPlane
        )

        hole_size = self.drive_config.output_bearing_ball_diameter + 0.02

        helpers.AddCircle(
            ball,
            0, 0, 0,
            hole_size * 0.5,
            True
        )
        ball.isComputeDeferred = False

        cage = helpers.SymmetricExtrude(self.compo,
            helpers.CreateCollection(
                sketch.profiles.item(4)
            ),
            hole_size + 2 * 0.06,
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
        )

        hole = helpers.OneSideExtrude(self.compo,
            helpers.CreateCollection(
                ball.profiles.item(0)
            ),
            0,
            10,
            adsk.fusion.ExtentDirections.PositiveExtentDirection,
            adsk.fusion.FeatureOperations.CutFeatureOperation,
            [cage.bodies.item(0)]
        )

        out = helpers.CircularPattern(
            self.compo,
            helpers.CreateCollection(
                hole
            ),
            self.compo.zConstructionAxis,
            self.drive_config.disc_bolt_count
        )

        out.bodies.item(0).name = "Cage"