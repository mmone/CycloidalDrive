# Copyright (C) 2018  Martin Muehlhaeuser <github@mmone.de>

import adsk.core, adsk.fusion, traceback
import math
from . import helpers

class WheelAssembly:
    def __init__(self,
        parentCompo,
        ui,
        width,
        inner_diameter,
        pin_circle_diameter,
        pin_diameter,
        pin_count,
        bearing_diameter):

        self.ui = ui
        self.width = width
        self.inner_dia = inner_diameter
        self.pin_circle_dia = pin_circle_diameter
        self.pin_dia = pin_diameter
        self.pin_count = pin_count
        self.bearing_dia = bearing_diameter

        self.innner_thickness = 0.5
        self.rim_thickness = 0.4
        self.gap = self.bearing_dia / 3.0
        self.bearing_center_radius = self.inner_dia * 0.5 + self.innner_thickness + self.gap * 0.5

        occs = parentCompo.occurrences
        mat = adsk.core.Matrix3D.create()
        newOcc = occs.addNewComponent(mat)

        self.compo = adsk.fusion.Component.cast(newOcc.component)
        self.compo.name = "Wheel"

        self.CreateRaceways()
        self.CreateRollerCage()

    def CreateRaceways(self):
        ringSketch = helpers.CreateSketch(self.compo, "Inner Raceway", False, False)

        # inner race - inner
        helpers.AddCircle( ringSketch,
            0,0,0,
            self.inner_dia * 0.5
        )

        # inner race - outer
        helpers.AddCircle( ringSketch,
            0,0,0,
           self.inner_dia * 0.5 + self.innner_thickness
        )

        # outer race - inner
        helpers.AddCircle( ringSketch,
            0,0,0,
            self.inner_dia * 0.5 + self.innner_thickness + self.gap 
        )

        # outer race - outer
        helpers.AddCircle( ringSketch,
            0,0,0,
           self.inner_dia * 0.5 + self.innner_thickness + self.gap + self.rim_thickness
        )

        rollerSketch = helpers.CreateSketchOnPlane(self.compo,
            "Roller Profile", False, False, self.compo.yZConstructionPlane)

        # bearing profile
        helpers.AddCircle( rollerSketch,
            -(self.width - self.bearing_dia * 1.5) * 0.5 , self.bearing_center_radius, 0,
            self.bearing_dia * 0.5
        )

        helpers.AddCircle( rollerSketch,
            (self.width - self.bearing_dia * 1.5) * 0.5, self.bearing_center_radius, 0,
            self.bearing_dia * 0.5
        )

        # inner ring
        profiles = adsk.core.ObjectCollection.create()
        profiles.add(ringSketch.profiles.item(1))

        inner_ring_extrude = helpers.SymmetricExtrude(
            self.compo,
            profiles,
            self.width,
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        )

        profiles = adsk.core.ObjectCollection.create()
        profiles.add(ringSketch.profiles.item(3))

        helpers.SymmetricExtrude(
            self.compo,
            profiles,
            self.width * 1.5,
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        )

        profiles = adsk.core.ObjectCollection.create()
        profiles.add(ringSketch.profiles.item(0))
        profiles.add(ringSketch.profiles.item(1))
        profiles.add(ringSketch.profiles.item(2))

        outer_ring_extrude = helpers.OneSideExtrude(
            self.compo,
            profiles,
            self.width * 1.5 * 0.5,
            - self.width * 0.1,
            adsk.fusion.ExtentDirections.PositiveExtentDirection,
            adsk.fusion.FeatureOperations.JoinFeatureOperation
        )

        inner_ring_extrude.bodies.item(0).name = "Inner Race"
        outer_ring_extrude.bodies.item(0).name = "Outer Race"

        profiles = adsk.core.ObjectCollection.create()
        profiles.add(rollerSketch.profiles.item(0))
        profiles.add(rollerSketch.profiles.item(1))

        revolveInput = self.compo.features.revolveFeatures.createInput(
            profiles,
            self.compo.zConstructionAxis,
            adsk.fusion.FeatureOperations.CutFeatureOperation
        )
        angle = adsk.core.ValueInput.createByReal(2*math.pi)
        revolveInput.setAngleExtent(False, angle)
        revolve = self.compo.features.revolveFeatures.add(revolveInput)

        self.compo.parentDesign.timeline.moveToPreviousStep()
        revolve.participantBodies = [inner_ring_extrude.bodies.item(0), outer_ring_extrude.bodies.item(0)]
        self.compo.parentDesign.timeline.movetoNextStep()

        # pin holes 
        sketch = helpers.CreateSketch(self.compo, "Pin Holes", False, False)

        helpers.AddCircle( sketch,
            0, self.pin_circle_dia * 0.5, 0,
            self.pin_dia * 0.5
        )

        profiles = adsk.core.ObjectCollection.create()
        profiles.add(sketch.profiles.item(0))

        pin_hole_extrude = helpers.OneSideExtrude(
            self.compo,
            profiles,
            0,
            self.width,
            adsk.fusion.ExtentDirections.PositiveExtentDirection,
            adsk.fusion.FeatureOperations.CutFeatureOperation
        )

        self.compo.parentDesign.timeline.moveToPreviousStep()
        pin_hole_extrude.participantBodies = [outer_ring_extrude.bodies.item(0)]
        self.compo.parentDesign.timeline.movetoNextStep()

        input_entities = adsk.core.ObjectCollection.create()
        input_entities.add(pin_hole_extrude)
        for i in range(0, pin_hole_extrude.linkedFeatures.count):
            input_entities.add(pin_hole_extrude.linkedFeatures.item(i))

        out = helpers.CircularPattern(
            self.compo,
            input_entities, 
            self.compo.zConstructionAxis,
            self.pin_count
        )
    
    def CreateRollerCage(self):
        sketch = helpers.CreateSketch(self.compo, "Roller Cage", False, False)

        helpers.AddCircle( sketch,
            0,0,0,
            self.bearing_center_radius - 0.06
        )

        helpers.AddCircle( sketch,
            0,0,0,
            self.bearing_center_radius + 0.06
        )

        roller_sketch = helpers.CreateSketchOnPlane(self.compo,
            "Roller Cage Profile", False, False, self.compo.yZConstructionPlane)

        # bearing profile
        helpers.AddCircle( roller_sketch,
            0,0,0,
            self.bearing_dia * 0.55
        )

        profiles = adsk.core.ObjectCollection.create()
        profiles.add(sketch.profiles.item(1))

        ring = helpers.SymmetricExtrude(
            self.compo,
            profiles,
            self.bearing_dia + 0.12,
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        )

        profiles = adsk.core.ObjectCollection.create()
        profiles.add(roller_sketch.profiles.item(0))

        pin_hole_extrude = helpers.OneSideExtrude(
            self.compo,
            profiles,
            0,
            self.bearing_center_radius + 1,
            adsk.fusion.ExtentDirections.PositiveExtentDirection,
            adsk.fusion.FeatureOperations.CutFeatureOperation
        )

        self.compo.parentDesign.timeline.moveToPreviousStep()
        pin_hole_extrude.participantBodies = [ring.bodies.item(0)]
        self.compo.parentDesign.timeline.movetoNextStep()

        input_entities = adsk.core.ObjectCollection.create()
        input_entities.add(pin_hole_extrude)
        for i in range(0, pin_hole_extrude.linkedFeatures.count):
            input_entities.add(pin_hole_extrude.linkedFeatures.item(i))

        out = helpers.CircularPattern(
            self.compo,
            input_entities, 
            self.compo.zConstructionAxis,
            12
        )

        out.bodies.item(0).name = "Ball Cage"