# Copyright (C) 2018  Martin Muehlhaeuser <github@mmone.de>

import adsk.core, adsk.fusion, traceback
import math
from . import helpers

class Brace:
    def __init__(self, parentCompo, ui, bolt_circle_radius, bolt_diameter, axis_diameter, arm_count):
        self.ui = ui
        self.bolt_circle_radius = bolt_circle_radius
        self.bolt_dia = bolt_diameter
        self.axis_dia = axis_diameter
        self.arm_count = arm_count

        occs = parentCompo.occurrences
        mat = adsk.core.Matrix3D.create()
        newOcc = occs.addNewComponent(mat)

        self.compo = adsk.fusion.Component.cast(newOcc.component)
        self.compo.name = "Brace"

        self.CreateBrace()

    def CreateBrace(self):
        hubDia = 1.2

        sketch = helpers.CreateSketch(self.compo, "Brace", True, False)

        # bolt
        bolt = helpers.AddCircle( sketch,
            0, self.bolt_circle_radius,0,
            self.bolt_dia * 0.5,
            False
        )

        boltRing = helpers.AddCircle( sketch,
            0, self.bolt_circle_radius, 0,
            self.bolt_dia * 1.2,
            False
        )

        # hub
        centerHole = helpers.AddCircle( sketch,
            0,0,0,
            self.axis_dia * 0.5,
            False
        )
        
        centerBushing =  helpers.AddCircle( sketch,
            0,0,0,
            hubDia * 0.25,
            False
        )

        hub =helpers.AddCircle( sketch,
            0,0,0,
            hubDia * 0.5,
            False
        )

        left = helpers.AddLine(sketch,
            -(self.bolt_dia + 0.4) * 0.5, self.bolt_circle_radius, 0,
            -hubDia * 0.5, 0, 0,
            False
        )

        right = helpers.AddLine(sketch,
            (self.bolt_dia + 0.4) * 0.5, self.bolt_circle_radius, 0,
            hubDia * 0.5, 0, 0,
            False
        )

        construction = helpers.AddLine(sketch,
            0, 0, 0,
            0, self.bolt_circle_radius * 1.3, 0,
            False
        )
        construction.isConstruction = True

        sketch.geometricConstraints.addVertical(construction)
        sketch.geometricConstraints.addCoincident(construction.startSketchPoint, sketch.originPoint)

        sketch.geometricConstraints.addCoincident(bolt.centerSketchPoint, boltRing.centerSketchPoint)
        sketch.geometricConstraints.addCoincident(centerBushing.centerSketchPoint, hub.centerSketchPoint)
        sketch.geometricConstraints.addCoincident(centerHole.centerSketchPoint, hub.centerSketchPoint)

        sketch.geometricConstraints.addCoincident(hub.centerSketchPoint, construction)
        sketch.geometricConstraints.addCoincident(bolt.centerSketchPoint, construction)
            
        sketch.geometricConstraints.addCoincident(hub.centerSketchPoint, sketch.originPoint)

        sketch.geometricConstraints.addTangent(left, boltRing)
        sketch.geometricConstraints.addTangent(left, hub)
        sketch.geometricConstraints.addTangent(right, boltRing)
        sketch.geometricConstraints.addTangent(right, hub)

        sketch.geometricConstraints.addCoincident(left.startSketchPoint, hub)
        sketch.geometricConstraints.addCoincident(right.startSketchPoint, hub)
        sketch.geometricConstraints.addCoincident(left.endSketchPoint, boltRing)
        sketch.geometricConstraints.addCoincident(right.endSketchPoint, boltRing)

        sketch.isComputeDeferred = False

        # arms
        feat1 =  helpers.OneSideExtrude(
            self.compo,
            helpers.CreateCollection(
                sketch.profiles.item(2),
                sketch.profiles.item(3),
                sketch.profiles.item(4),
                sketch.profiles.item(5),
            ),
            0, 0.2,
            adsk.fusion.ExtentDirections.NegativeExtentDirection,
            adsk.fusion.FeatureOperations.JoinFeatureOperation
        )

        # bolt bushings
        profiles = adsk.core.ObjectCollection.create()
        profiles.add(sketch.profiles.item(3))
        feat2 = helpers.OneSideExtrude(
            self.compo,
            profiles, 0, 0.5,
            adsk.fusion.ExtentDirections.PositiveExtentDirection,
            adsk.fusion.FeatureOperations.JoinFeatureOperation
        )

        helpers.CircularPattern(self.compo,
            helpers.CreateCollection(
                feat1,
                feat2
            ),
            self.compo.zConstructionAxis,
            self.arm_count
        )

        # center bushing
        profiles = adsk.core.ObjectCollection.create()
        profiles.add(sketch.profiles.item(2))
        out = helpers.OneSideExtrude(
            self.compo,
            profiles, 0, 0.2,
            adsk.fusion.ExtentDirections.PositiveExtentDirection,
            adsk.fusion.FeatureOperations.JoinFeatureOperation
        )

        filletEdges = adsk.core.ObjectCollection.create()

        for e in range(0, out.bodies.item(0).convexEdges.count):
            #self.ui.messageBox('len:\n{}'.format(out.bodies.item(b).convexEdges.item(e).length))
            filletEdges.add(out.bodies.item(0).convexEdges.item(e))
        
        out = helpers.FilletEdgesSimple(self.compo, filletEdges, 0.1)
        out.bodies.item(0).name = "Brace"

        #self.LighteningHoles(out.bodies.item(0))
    
    def LighteningHoles(self, input_body):
        sketch = helpers.CreateSketch(self.compo, "Lightening", True, False)

        top_y = self.bolt_circle_radius * 0.55
        top_rad = self.bolt_circle_radius * 0.1
        bottom_y = self.bolt_circle_radius * 0.3
        bottom_rad = self.bolt_circle_radius * 0.05

        top = helpers.AddCircle( sketch,
            0, top_y, 0,
            top_rad,
            False
        )

        bottom = helpers.AddCircle( sketch,
            0, bottom_y, 0,
            bottom_rad,
            False
        )

        left = helpers.AddLine(sketch,
            -top_rad, top_y, 0,
            -bottom_rad, bottom_y, 0,
            False
        )

        right = helpers.AddLine(sketch,
            top_rad, top_y, 0,
            bottom_rad, bottom_y, 0,
            False
        )

        construction = helpers.AddLine(sketch,
            0, 0, 0,
            0, self.bolt_circle_radius * 1.3, 0,
            False
        )
        construction.isConstruction = True
        
        sketch.geometricConstraints.addVertical(construction)
        sketch.geometricConstraints.addCoincident(construction.startSketchPoint, sketch.originPoint)

        sketch.geometricConstraints.addCoincident(top.centerSketchPoint, construction)
        sketch.geometricConstraints.addCoincident(bottom.centerSketchPoint, construction)

        sketch.geometricConstraints.addTangent(left, top)
        sketch.geometricConstraints.addTangent(left, bottom)
        sketch.geometricConstraints.addTangent(right, top)
        sketch.geometricConstraints.addTangent(right, bottom)

        sketch.geometricConstraints.addCoincident(left.startSketchPoint, bottom)
        sketch.geometricConstraints.addCoincident(right.startSketchPoint, bottom)
        sketch.geometricConstraints.addCoincident(left.endSketchPoint, top)
        sketch.geometricConstraints.addCoincident(right.endSketchPoint, top)

        sketch.isComputeDeferred = False

        hole =  helpers.OneSideExtrude(
            self.compo,
            helpers.CreateCollection(
                sketch.profiles.item(0),
                sketch.profiles.item(1),
                sketch.profiles.item(2)
            ),
            0, 0.2,
            adsk.fusion.ExtentDirections.NegativeExtentDirection,
            adsk.fusion.FeatureOperations.CutFeatureOperation,
            [input_body]
        )

        inputEntites = adsk.core.ObjectCollection.create()
        inputEntites.add(hole)
        #for i in range(0, hole.linkedFeatures.count):
        #    inputEntites.add(hole.linkedFeatures.item(i))

        helpers.CircularPattern(self.compo,
            inputEntites,
            self.compo.zConstructionAxis,
            self.arm_count / 2
        )