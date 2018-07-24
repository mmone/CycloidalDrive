# Copyright (C) 2018  Martin Muehlhaeuser <github@mmone.de>

import adsk.core, adsk.fusion, traceback
import math
from . import helpers

class OutputDisc:
    def __init__(self, parent_compo, ui, main_diameter, axis_diameter, circle_radius, pin_diameter, pin_count):
        self.ui = ui
        self.main_dia = main_diameter
        self.axis_dia = axis_diameter
        self.circle_radius = circle_radius
        self.pin_dia = pin_diameter
        self.pin_count = pin_count

        occs = parent_compo.occurrences
        mat = adsk.core.Matrix3D.create()
        newOcc = occs.addNewComponent(mat)

        self.compo = adsk.fusion.Component.cast(newOcc.component)
        self.compo.name = "Output Disc"
        self.CreateDisc()

    def CreateDisc(self):
        sketch = helpers.CreateSketch(self.compo, "Output Disc", True, False)

        helpers.AddCircle(sketch, 0,0,0, self.axis_dia * 0.5 )
        helpers.AddCircle(sketch, 0,0,0, self.main_dia * 0.5 )

        helpers.AddCircle(sketch, 0, self.circle_radius, 0, self.pin_dia * 0.5 )
        helpers.AddCircle(sketch, 0, self.circle_radius, 0, self.pin_dia * 0.6 )
        
        sketch.isComputeDeferred = False

        extrude0 = helpers.OneSideExtrude(self.compo,
            helpers.CreateCollection(
                sketch.profiles.item(1),
                sketch.profiles.item(2),
                sketch.profiles.item(3)
            ),
            0, 0.12,
            adsk.fusion.ExtentDirections.PositiveExtentDirection,
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        )
        
        profiles = adsk.core.ObjectCollection.create()
        profiles.add(sketch.profiles.item(2))
        profiles.add(sketch.profiles.item(3))

        extrude1 = helpers.OneSideExtrude(self.compo,
            profiles,
            0, 0.2,
            adsk.fusion.ExtentDirections.PositiveExtentDirection,
            adsk.fusion.FeatureOperations.JoinFeatureOperation,
            [extrude0.bodies.item(0)]
        )
        
        profiles = adsk.core.ObjectCollection.create()
        profiles.add(sketch.profiles.item(2))

        extrude2 = helpers.OneSideExtrude(self.compo,
            profiles,
            0, 0.2,
            adsk.fusion.ExtentDirections.PositiveExtentDirection,
            adsk.fusion.FeatureOperations.CutFeatureOperation,
            [extrude1.bodies.item(0)]
        )
        
        inputEntites = adsk.core.ObjectCollection.create()
        inputEntites.add(extrude1)
        inputEntites.add(extrude2)

        out = helpers.CircularPattern(
            self.compo,
            helpers.CreateCollection(
                extrude1,
                extrude2
            ),
            self.compo.zConstructionAxis,
            self.pin_count,
            adsk.fusion.PatternComputeOptions.IdenticalPatternCompute
        )

        filletEdges = adsk.core.ObjectCollection.create()

        for e in range(0, out.bodies.item(0).concaveEdges.count):
            filletEdges.add(out.bodies.item(0).convexEdges.item(e))

        out = helpers.FilletEdgesSimple(self.compo, filletEdges, 0.06)
        
        out.bodies.item(0).name = "Output Disc"