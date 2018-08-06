# Copyright (C) 2018  Martin Muehlhaeuser <github@mmone.de>

import adsk.core, adsk.fusion, traceback
import math
from .components import Brace, OutputDisc, WheelAssembly
from .components import helpers
from .components import DriveConfig
from .components import PrinterConfig

class CycloidalComponent:
   
    def __init__(self, design, ui, drive_config, printer_config ):
        self.design = design
        self.ui = ui
        self.config = drive_config
        self.printer_config = printer_config

        self.RACE_HEIGHT_RAD_PLUS = 0.01
        self.CURVE_SUBSAMPLING = 32
        self.CAGE_SLOT_HEIGHT = self.printer_config.lToCm(5)

        occs = design.rootComponent.occurrences
        mat = adsk.core.Matrix3D.create()
        newOcc = occs.addNewComponent(mat)
        
        self.compo = adsk.fusion.Component.cast(newOcc.component)
        self.compo.name = 'Drive (' + str(self.config.roller_count) + ' rollers @' + str(self.config.roller_spacing) +')'
        
        self.sketches = self.compo.sketches
        # calculates the diameter from the length of the circle segment intersected with the main planet orbit
        self.median_dia  = self.CalculateMedianDiameter(
            self.config.roller_diameter,
            self.config.roller_count,
            self.config.roller_spacing
        )
        self.median_radius = self.median_dia  * 0.5
        self.roller_rad = self.config.roller_diameter * 0.5
        self.thickness = self.config.roller_diameter + 2 * self.printer_config.lToCm(5) + 2 * self.RACE_HEIGHT_RAD_PLUS

        self.ring_outer_radius = self.CalculateOuterRadius(
            self.median_radius,
            self.config.roller_diameter,
            self.config.ring_bolt_diameter
        )
        self.ring_bolt_circle_radius = self.ring_outer_radius - self.config.ring_bolt_diameter * 0.25
        self.disc_bolt_circle_radius = self.median_radius - (self.roller_rad * 3.0) - self.config.disc_bolt_diameter * 0.5
        self.slot_radius = self.median_radius + (self.roller_rad * 2.25)

        self.cycloid_cut_plane = None
        self.output_cut_plane = None

        self.DrawConstructionSketch()
        self.CreateSplitPlanes()
        self.CreateRollerSketch()
        if('Ring' in self.config.components):
            self.BuildRing()
        if('Disc' in self.config.components):
            self.BuildDisc()
        if('Bearing Seat' in self.config.components):
            self.CreateBearingSeat()
        if('Rollers' in self.config.components):
            self.BuildRollers()
        if('Cage' in self.config.components):
            self.BuildRollerCage()
        if('Cam' in self.config.components):
            self.BuildCam()
        # deactivate temporarily to avoid conflicts when cutting
        self.compo.isBodiesFolderLightBulbOn = False
        if('Brace' in self.config.components):
            self.BuildBrace()
        self.compo.isBodiesFolderLightBulbOn = True 
        if('Output' in self.config.components):
            self.BuildOutputDisc()
        #self.CreateWheelAssembly()

    @staticmethod
    def CalculateMedianDiameter(roller_diameter, roller_count, roller_gap_factor):
        return roller_diameter / (2 * math.sin(math.pi / ((1 + roller_gap_factor) * roller_count * 2.0)))

    @staticmethod
    def CalculateOuterRadius(median_radius, roller_diameter, ring_bolt_diameter):
        return median_radius + roller_diameter + ring_bolt_diameter * 1.5

    def GetComponent(self):
        return self.compo

    def DrawConstructionSketch(self):
        try:
            baseSketch = helpers.CreateSketch(self.compo, "Construction", True, False)
        
            yOffset =  self.config.roller_diameter / 12.0
            circle = helpers.AddCircle(baseSketch,
                0, yOffset, 0,
                self.median_radius
            )
            circle.isFixed = True

            self.circle_center = baseSketch.sketchCurves.sketchLines.addByTwoPoints(
                adsk.core.Point3D.create(0, yOffset, 1),
                adsk.core.Point3D.create(0, yOffset, -1)
            )
            self.circle_center.isConstruction = True
            self.circle_center.isFixed = True

            radOffset = math.pi * 2.0 / self.config.roller_count

            for i in range(0, self.config.roller_count):
              circle = baseSketch.sketchCurves.sketchCircles.addByCenterRadius(
                  adsk.core.Point3D.create(math.sin(radOffset * i) * self.median_radius , (math.cos( radOffset * i) * self.median_radius) + yOffset, 0),
                  self.roller_rad)
              circle.isConstruction = True
              circle.isFixed = True

            #######
            groveRootRadius = (self.median_dia  + self.GrooveRootToBallCenter(self.config.roller_diameter) + self.roller_rad) * 0.5
            topRailPoints = adsk.core.ObjectCollection.create()
            radOffset = 2.0 * math.pi * 0.25 / (self.config.roller_count + 1)
            rad = 0.0

            div =  (self.config.roller_count+1) * 10
            for i in range(0, div):
                rad = 2.0 * math.pi * (i / div * 1.0)
                amp = math.sin(rad * (self.config.roller_count+1))

                o = self.median_radius + self.config.roller_diameter * amp * 0.125# (1 - (0.25 * ((amp + 1) * 0.5) ))

                topRailPoints.add( adsk.core.Point3D.create(
                    math.sin(rad + radOffset) * o,
                    math.cos(rad + radOffset) * o + yOffset,
                    0)
                )

            top_1    = baseSketch.sketchCurves.sketchLines.addByTwoPoints(topRailPoints.item(0), topRailPoints.item(1))

            first_point_top = top_1.startSketchPoint

            for i in range(2, topRailPoints.count):
                top_1 = baseSketch.sketchCurves.sketchLines.addByTwoPoints(top_1.endSketchPoint, topRailPoints.item(i))
                top_1.isFixed = True

            baseSketch.sketchCurves.sketchLines.addByTwoPoints(top_1.endSketchPoint, first_point_top)
            
            baseSketch.isComputeDeferred = False

        except Exception as error:
            if self.ui:
                self.ui.messageBox("drawConstructionSketch Failed : " + str(error))
            return None

    def CreateSplitPlanes(self):
        try:
            planes = self.compo.constructionPlanes
            planeInput = planes.createInput()
            planeInput.setByOffset(
                self.compo.xYConstructionPlane,
                adsk.core.ValueInput.createByReal(self.CAGE_SLOT_HEIGHT * 0.5)
            )
            self.cycloid_cut_plane = planes.add(planeInput)
            self.cycloid_cut_plane.name = "cycloid-cut"
            self.cycloid_cut_plane.isLightBulbOn = False
            
            if 'Output' in self.config.components:
                planeInput2 = planes.createInput()
                planeInput2.setByOffset(
                    self.compo.xYConstructionPlane,
                    adsk.core.ValueInput.createByReal(
                        self.thickness * 0.5 + self.printer_config.lToCm(5) + self.config.output_bearing_ball_diameter * 0.5
                    )
                )
                self.output_cut_plane = planes.add(planeInput2)
                self.output_cut_plane.name = "output-cut"
                self.output_cut_plane.isLightBulbOn = False

        except Exception as error:
            if self.ui:
                self.ui.messageBox("createSpPlane Failed : " + str(error)) 
            return None
    
    def CreateRollerSketch(self):
        try:
            profileCenter = adsk.core.Point3D.create(0, self.median_radius + self.config.roller_diameter / 12.0, 0)

            self.roller_sketch = helpers.CreateSketch(self.compo, "Roller", True, False, self.compo.yZConstructionPlane)
            helpers.AddCircle(self.roller_sketch,
                0, self.median_radius + self.config.roller_diameter / 12.0, 0,
                self.roller_rad
            )

            self.roller_mirror_line = self.roller_sketch.sketchCurves.sketchLines.addByTwoPoints(
                adsk.core.Point3D.create(self.config.roller_diameter, profileCenter.y, 0),
                adsk.core.Point3D.create(-self.config.roller_diameter, profileCenter.y, 0)
            )

            self.roller_sketch.isComputeDeferred = False
        except Exception as error:
            if self.ui:
                self.ui.messageBox("Create Roller Sketch Failed : " + str(error)) 
            return None

    def BuildRollers(self):
        try:
            revolves = self.compo.features.revolveFeatures
            revolveInput = revolves.createInput(
                self.roller_sketch.profiles.item(0),
                self.roller_mirror_line,
                adsk.fusion.FeatureOperations.NewBodyFeatureOperation   
            )
            
            revolveInput.setAngleExtent(False, adsk.core.ValueInput.createByReal(math.pi * 2.0))
            revolve = revolves.add(revolveInput)
            revolve.bodies.item(0).name = "Roller"

            inputEntites = adsk.core.ObjectCollection.create()
            inputEntites.add(revolve.bodies.item(0))

            helpers.CircularPattern(self.compo,
                inputEntites,
                self.circle_center,
                self.config.roller_count
            )
        except Exception as error:
            if self.ui:
                self.ui.messageBox("buildRoller Failed : " + str(error)) 
            return None

    def GrooveRootToBallCenter(self, planet_diameter):
        return (planet_diameter * planet_diameter) / (2.0 * (planet_diameter * 3/4.0))

    def TangentFunction(self, planet_diameter, contact_diameter, x):
        return contact_diameter / math.sqrt(planet_diameter * planet_diameter - contact_diameter * contact_diameter) * x

    def TangentFunctionInverse(self, planet_diameter, contact_diameter, y):
        if( contact_diameter == planet_diameter):
            return 0
        elif ( contact_diameter == 0):
            return planet_diameter * 0.5
        else:
            return y / (contact_diameter / math.sqrt(planet_diameter * planet_diameter - contact_diameter * contact_diameter))

    def BuildRing(self):
        try:
            half_race_height = self.roller_rad + self.RACE_HEIGHT_RAD_PLUS

            groveRootRadius = (self.median_dia  + self.GrooveRootToBallCenter(self.config.roller_diameter) + self.roller_rad) * 0.5

            housingSketch = helpers.CreateSketch(self.compo, "Ring", True, False)
            raceSketch = helpers.CreateSketch(self.compo, "Ring Race", True, False)

            # inner ring
            helpers.AddCircle(housingSketch, 0,0,0, self.median_radius + self.roller_rad * 0.42)

            # slot
            helpers.AddCircle(housingSketch, 0,0,0, self.slot_radius)

            # outer ring
            helpers.AddCircle(housingSketch, 0,0,0, self.ring_outer_radius)
            
            topRailPoints = adsk.core.ObjectCollection.create()

            radOffset = 2.0 * math.pi * 0.25 / (self.config.roller_count + 1)
            rad = 0.0

            div =  (self.config.roller_count+1) * self.CURVE_SUBSAMPLING
            for i in range(0, div):
                rad = 2.0 * math.pi * (i / div * 1.0)
                amp = math.sin(rad * (self.config.roller_count+1))

                o = groveRootRadius - self.TangentFunctionInverse(
                    self.config.roller_diameter,
                    self.config.roller_diameter * (1 - (0.25 * ((amp + 1) * 0.5) )),
                    half_race_height
                )
                topRailPoints.add( adsk.core.Point3D.create(
                    math.sin(rad + radOffset) * o,
                    math.cos(rad + radOffset) * o,
                    half_race_height)
                )

            top_1    = raceSketch.sketchCurves.sketchLines.addByTwoPoints(topRailPoints.item(0), topRailPoints.item(1))

            first_point_top = top_1.startSketchPoint

            for i in range(2, topRailPoints.count):
                top_1 = raceSketch.sketchCurves.sketchLines.addByTwoPoints(top_1.endSketchPoint, topRailPoints.item(i))
                top_1.isFixed = True

            raceSketch.sketchCurves.sketchLines.addByTwoPoints(top_1.endSketchPoint, first_point_top)
            
            helpers.AddCircle(raceSketch, 0,0,0, groveRootRadius, True)

            raceSketch.isComputeDeferred = False
            housingSketch.isComputeDeferred = False

            # ring
            if 'Output' in self.config.components:
               extend = self.thickness + self.config.output_bearing_ball_diameter + 2 * self.printer_config.lToCm(5)
            else:
               extend = self.thickness

            extrudeOut = helpers.OneSideExtrude(self.compo,
                helpers.CreateCollection(
                    housingSketch.profiles.item(1),
                    housingSketch.profiles.item(2)
                ),
                -self.thickness * 0.5,
                extend,
                adsk.fusion.ExtentDirections.PositiveExtentDirection,
                adsk.fusion.FeatureOperations.JoinFeatureOperation
            )
            
            self.CreateRingHoles(-self.thickness * 0.5, extend)

            loft = self.compo.features.loftFeatures
            loftInput = loft.createInput(
                adsk.fusion.FeatureOperations.CutFeatureOperation
            )

            loftSections = loftInput.loftSections
            s1 = loftSections.add(raceSketch.profiles.item(0))
            s1.setFreeEndCondition()
            s2 = loftSections.add(raceSketch.profiles.item(1))
            s2.setFreeEndCondition()
            loft_out = loft.add(loftInput)
       
            helpers.Mirror(self.compo,
                helpers.CreateCollection(loft_out),
                self.compo.xYConstructionPlane
            )

            # cut slot
            extrudeOut = helpers.SymmetricExtrude(
                self.compo,
                helpers.CreateCollection(
                    housingSketch.profiles.item(0),
                    housingSketch.profiles.item(1),
                ),
                self.CAGE_SLOT_HEIGHT,
                adsk.fusion.FeatureOperations.CutFeatureOperation
            )
            
            splits = self.compo.features.splitBodyFeatures
            splitInput = splits.createInput(extrudeOut.bodies.item(0), self.cycloid_cut_plane, True)
            split = splits.add(splitInput)
            split.bodies.item(0).name = "Ring-bottom"
            split.bodies.item(1).name = "Ring-top"

            self.CreateRingKeyFeatures(split.bodies.item(1), split.bodies.item(0))
            
            if 'Output' in self.config.components:
                splits = self.compo.features.splitBodyFeatures
                splitInput = splits.createInput(split.bodies.item(1), self.output_cut_plane, True)
                split = splits.add(splitInput)
                split.bodies.item(0).name = "Ring-top"
                split.bodies.item(1).name = "Output-top"

        except Exception as error:
            if self.ui:
                self.ui.messageBox("buildRing Failed : " + str(error)) 
            return None

    def CreateRingHoles(self, start, extend):
        try:
            holeSketch = helpers.CreateSketch(self.compo, "Ring Holes", True, False)
            
            helpers.AddCircle(holeSketch,
                0, self.ring_bolt_circle_radius, 0,
                self.config.ring_bolt_diameter * 0.5
            )

            helpers.AddCircle(holeSketch,
                0, self.ring_bolt_circle_radius, 0,
                self.config.ring_bolt_diameter * 0.5 + self.printer_config.ewToCm(3)
            )

            holeSketch.isComputeDeferred = False

            extrudeOut1 = helpers.OneSideExtrude(
                self.compo,
                helpers.CreateCollection(
                    holeSketch.profiles.item(1)
                ),
                start,
                extend,
                adsk.fusion.ExtentDirections.PositiveExtentDirection,
                adsk.fusion.FeatureOperations.JoinFeatureOperation
            )

            extrudeOut2 = helpers.OneSideExtrude(
                self.compo,
                helpers.CreateCollection(
                    holeSketch.profiles.item(0)
                ),                
                start,
                extend,
                adsk.fusion.ExtentDirections.PositiveExtentDirection,
                adsk.fusion.FeatureOperations.CutFeatureOperation
            )

            inputEntites = adsk.core.ObjectCollection.create()
            inputEntites.add(extrudeOut1)
            inputEntites.add(extrudeOut2)
            
            if(self.config.chamfer_ring_bolt_holes):
                chamferEdges = adsk.core.ObjectCollection.create()
                chamferEdges.add(extrudeOut2.faces.item(0).edges.item(0))
                chamferEdges.add(extrudeOut2.faces.item(0).edges.item(1))
               
                chamferOut = helpers.ChamferEdgesSimple(self.compo,
                    chamferEdges,
                    self.config.ring_bolt_diameter / 3.0
                )
                inputEntites.add(chamferOut)

            out = helpers.CircularPattern(self.compo,
                inputEntites,
                self.compo.zConstructionAxis,
                self.config.ring_bolt_count
            )

            filletEdges = adsk.core.ObjectCollection.create()

            for e in range(0, out.bodies.item(0).convexEdges.count):
                filletEdges.add(out.bodies.item(0).convexEdges.item(e))
            
            filletInput = self.compo.features.filletFeatures.createInput()
            filletInput.addConstantRadiusEdgeSet(filletEdges, adsk.core.ValueInput.createByReal(0.1), False)
            return self.compo.features.filletFeatures.add(filletInput)
        except Exception as error:
            if self.ui:
                self.ui.messageBox("Ring Holes Failed : " + str(error)) 
            return None

    def CreateRingKeyFeatures(self, top_ring_body, bottom_ring_body):
        try:
            sketch = helpers.CreateSketchOnPlane(self.compo,
                "Ring Keys",
                True, False,
                self.cycloid_cut_plane
            )
            
            # inner circle
            helpers.AddCircle(
                sketch,
                0,0,0,
                self.ring_outer_radius - self.config.ring_bolt_diameter * 0.5
            )

            # outer circle
            helpers.AddCircle(sketch, 0,0,0, self.ring_outer_radius)

            rad = 2 * math.pi / self.config.ring_bolt_count
            sketch.sketchCurves.sketchLines.addByTwoPoints(
                adsk.core.Point3D.create(0,0,0),
                adsk.core.Point3D.create(
                    math.sin(rad - rad / 4.0) * self.ring_outer_radius,
                    math.cos(rad - rad / 4.0) * self.ring_outer_radius,
                    0
                )
            )

            sketch.sketchCurves.sketchLines.addByTwoPoints(
                adsk.core.Point3D.create(0,0,0),
                adsk.core.Point3D.create(
                    math.sin(rad / 4.0) * self.ring_outer_radius,
                    math.cos(rad / 4.0) * self.ring_outer_radius,
                    0
                )
            )

            sketch.isComputeDeferred = False

            profile = helpers.CreateCollection(sketch.profiles.item(3))
            slot = helpers.OneSideExtrude(self.compo,
                profile,
                0, self.printer_config.lToCm(6),
                adsk.fusion.ExtentDirections.NegativeExtentDirection,
                adsk.fusion.FeatureOperations.CutFeatureOperation,
                [bottom_ring_body]
            )

            helpers.CircularPattern(self.compo,
                helpers.CreateCollection(slot),
                self.compo.zConstructionAxis,
                self.config.ring_bolt_count
            )

            key = helpers.OneSideExtrude(self.compo,
                profile,
                0, self.printer_config.lToCm(5),
                adsk.fusion.ExtentDirections.NegativeExtentDirection,
                adsk.fusion.FeatureOperations.JoinFeatureOperation,
                [top_ring_body]
            )

            edges = adsk.core.ObjectCollection.create()
            for i in range(0, key.bodies.item(0).edges.count):
                if key.bodies.item(0).edges.item(i).length == self.printer_config.lToCm(5):
                    edges.add(key.bodies.item(0).edges.item(i))

            key_fillet = helpers.FilletEdgesSimple(self.compo,
                edges,
                0.05
            )

            helpers.CircularPattern(self.compo,
                helpers.CreateCollection(key, key_fillet),
                self.compo.zConstructionAxis,
                self.config.ring_bolt_count
            )
        except Exception as error:
            if self.ui:
                self.ui.messageBox("Ring Key Features Failed : " + str(error)) 
            return None

    def BuildDisc(self):
        try:
            half_race_height = self.roller_rad + self.RACE_HEIGHT_RAD_PLUS

            groveRootRadius = (self.median_dia  - self.GrooveRootToBallCenter(self.config.roller_diameter) - self.roller_rad) * 0.5

            discSketch = helpers.CreateSketch(self.compo, "Disc", True, False)
            raceSketch = helpers.CreateSketch(self.compo, "Disc Race", True, False)

            # slot
            helpers.AddCircle(discSketch, 0,0,0, self.median_radius - self.roller_rad * 2.25)

            # outer ring
            helpers.AddCircle(discSketch, 0,0,0,
                groveRootRadius + self.TangentFunctionInverse(
                    self.config.roller_diameter,
                    self.config.roller_diameter * 3/4.0,
                    half_race_height
                )
            )

            topRailPoints = adsk.core.ObjectCollection.create()

            radOffset = 2.0 * math.pi * 0.25 / (self.config.roller_count -1)# math.pi * 3/2.0 # 1/4 phase
            rad = 0.0

            div =  (self.config.roller_count-1) * self.CURVE_SUBSAMPLING
            for i in range(0, div):
                rad = 2.0 * math.pi * (i / div * 1.0)
                amp = math.sin(rad * (self.config.roller_count-1))

                o = groveRootRadius + self.TangentFunctionInverse(
                    self.config.roller_diameter,
                    self.config.roller_diameter * (1 - (0.25 * ((amp + 1) * 0.5) )),
                    half_race_height
                )
                topRailPoints.add( adsk.core.Point3D.create(
                    math.sin(rad - radOffset) * o,
                    math.cos(rad - radOffset) * o,
                    half_race_height)
                )

            top_1    = raceSketch.sketchCurves.sketchLines.addByTwoPoints(topRailPoints.item(0), topRailPoints.item(1))

            first_point_top = top_1.startSketchPoint

            for i in range(2, topRailPoints.count):
                top_1 = raceSketch.sketchCurves.sketchLines.addByTwoPoints(top_1.endSketchPoint, topRailPoints.item(i))
                top_1.isFixed = True

            raceSketch.sketchCurves.sketchLines.addByTwoPoints(top_1.endSketchPoint, first_point_top)

            helpers.AddCircle(raceSketch, 0,0,0, groveRootRadius, True)

            raceSketch.isComputeDeferred = False
            discSketch.isComputeDeferred = False

            # main body
            loft = self.compo.features.loftFeatures
            loftInput = loft.createInput(
                adsk.fusion.FeatureOperations.NewBodyFeatureOperation
            )

            loftSections = loftInput.loftSections
            s1 = loftSections.add(raceSketch.profiles.item(0))
            s1.setFreeEndCondition()
            s2 = loftSections.add(raceSketch.profiles.item(1))
            s2.setFreeEndCondition()
            loft_out = loft.add(loftInput)

            mirror_out = helpers.Mirror(self.compo,
                helpers.CreateCollection(loft_out),
                self.compo.xYConstructionPlane
            )

            helpers.Combine(self.compo,
                adsk.fusion.FeatureOperations.JoinFeatureOperation,
                loft_out.bodies.item(0),
                mirror_out.bodies.item(0)
            )

            # top plate
            profiles = helpers.CreateCollection(
                discSketch.profiles.item(0),
                discSketch.profiles.item(1)
            )

            helpers.OneSideExtrude(
                self.compo,
                profiles,
                half_race_height,
                self.printer_config.lToCm(4),
                adsk.fusion.ExtentDirections.PositiveExtentDirection,
                adsk.fusion.FeatureOperations.JoinFeatureOperation
            )

            #bottom plate
            helpers.OneSideExtrude(
                self.compo,
                profiles,
                -half_race_height,
                self.printer_config.lToCm(4),
                adsk.fusion.ExtentDirections.NegativeExtentDirection,
                adsk.fusion.FeatureOperations.JoinFeatureOperation
            )

            self.CreateDiscHoles()

            # cut slot
            extrudeOut = helpers.SymmetricExtrude(
                self.compo,
                helpers.CreateCollection(discSketch.profiles.item(1)),
                self.CAGE_SLOT_HEIGHT,
                adsk.fusion.FeatureOperations.CutFeatureOperation
            )
            
            splits = self.compo.features.splitBodyFeatures
            splitInput = splits.createInput(extrudeOut.bodies.item(0), self.cycloid_cut_plane, True)
            split = splits.add(splitInput)
            split.bodies.item(0).name = "Disc-bottom"
            split.bodies.item(1).name = "Disc-top"
            
        except Exception as error:
            if self.ui:
                self.ui.messageBox("BuildDisc Failed : " + str(error)) 
            return None

    def CreateBearingSeat(self):
        try:
            sketch = helpers.CreateSketch(self.compo, "Bearing Seat", False, False)

            helpers.AddCircle(sketch, 0, 0, 0, (self.config.cam_bearing_outer_diameter - 0.16) * 0.5)

            helpers.AddCircle(sketch, 0, 0, 0, self.config.cam_bearing_outer_diameter * 0.5)

            profiles = adsk.core.ObjectCollection.create()
            profiles.add(sketch.profiles.item(0))

            helpers.SymmetricExtrude(
                self.compo,
                profiles,
                self.thickness,
                adsk.fusion.FeatureOperations.CutFeatureOperation
            )

            profiles = adsk.core.ObjectCollection.create()
            profiles.add(sketch.profiles.item(1))
            
            helpers.SymmetricExtrude(
                self.compo,
                profiles,
                0.42,
                adsk.fusion.FeatureOperations.CutFeatureOperation
            )
        except Exception as error:
            if self.ui:
                self.ui.messageBox("Bearing Seat Failed : " + str(error)) 
            return None

    def CreateDiscHoles(self):
        try:
            holeSketch = helpers.CreateSketch(self.compo, "Disc Holes", True, False)
            
            helpers.AddCircle(holeSketch,
                0, self.disc_bolt_circle_radius, 0,
                self.config.disc_bolt_diameter * 0.5
            )

            holeSketch.isComputeDeferred = False

            profiles = adsk.core.ObjectCollection.create()
            profiles.add(holeSketch.profiles.item(0))

            extrudeOut = helpers.SymmetricExtrude(
                self.compo,
                profiles,
                self.thickness,
                adsk.fusion.FeatureOperations.CutFeatureOperation
            )

            inputEntites = adsk.core.ObjectCollection.create()
            inputEntites.add(extrudeOut)

            if(self.config.chamfer_ring_bolt_holes):
                chamferEdges = adsk.core.ObjectCollection.create()
                chamferEdges.add(extrudeOut.faces.item(0).edges.item(0))
                chamferEdges.add(extrudeOut.faces.item(0).edges.item(1))

                chamferOut = helpers.ChamferEdgesSimple(self.compo,
                    chamferEdges,
                    self.config.ring_bolt_diameter / 3.0
                )
                inputEntites.add(chamferOut)

            helpers.CircularPattern(self.compo,
                inputEntites,
                self.compo.zConstructionAxis,
                self.config.disc_bolt_count
            )
        except Exception as error:
            if self.ui:
                self.ui.messageBox("Disc Holes Failed : " + str(error)) 
            return None

    def BuildRollerCage(self):
        try:
            carrierSketch = helpers.CreateSketch(self.compo, "Cage", True, False)

            radOffset = math.pi * 2 / self.config.roller_count
            yOffset = self.config.roller_diameter / 12.0

            helpers.AddCircle(carrierSketch,
                0, yOffset, 0,
                self.median_radius + (self.roller_rad * 1.7)
            )    

            helpers.AddCircle(carrierSketch,
                0, yOffset, 0,
                self.median_radius - (self.roller_rad * 1.7)
            )    
        
            for i in range(0, self.config.roller_count):
                helpers.AddCircle(carrierSketch,
                    math.sin(radOffset * i) * self.median_radius , (math.cos( radOffset * i) * self.median_radius) + yOffset, 0,
                    self.roller_rad * 1.1
                )
            
            carrierSketch.isComputeDeferred = False

            # extrusion
            profiles = adsk.core.ObjectCollection.create()
            profiles.add(carrierSketch.profiles.item(0))
            extrude = helpers.SymmetricExtrude(self.compo,
                profiles, self.CAGE_SLOT_HEIGHT - self.printer_config.lToCm(1),
                adsk.fusion.FeatureOperations.NewBodyFeatureOperation
            )
            extrude.bodies.item(0).name = "Cage"
        
        except Exception as error:
            if self.ui:
                self.ui.messageBox("Build Cage Failed : " + str(error)) 
            return None

    def BuildCam(self):
        try:
            sketch = helpers.CreateSketch(self.compo, "Cam", True, False)
            helpers.AddCircle( sketch,
                0, self.config.roller_diameter * 1/4.0, 0,
                0.155
            )

            helpers.AddCircle( sketch, 0,0,0, self.config.cam_bearing_inner_diameter * 0.5 )

            helpers.AddCircle( sketch, 0,0,0, (self.config.cam_bearing_inner_diameter  + 0.08) * 0.5 )

            sketch.isComputeDeferred = False

            helpers.SymmetricExtrude(self.compo,
                helpers.CreateCollection(
                    sketch.profiles.item(1)
                ),
                0.44,
                adsk.fusion.FeatureOperations.NewBodyFeatureOperation
            )

            out = helpers.OneSideExtrude(self.compo,
                helpers.CreateCollection(
                    sketch.profiles.item(1),
                    sketch.profiles.item(2)
                ),
                0.22,
                0.04,
                adsk.fusion.ExtentDirections.PositiveExtentDirection,
                adsk.fusion.FeatureOperations.JoinFeatureOperation
            )

            out.bodies.item(0).name = "Cam"
        except Exception as error:
            if self.ui:
                self.ui.messageBox("Cam Failed : " + str(error)) 
            return None

    def BuildBrace(self):
        try:
            Brace.Brace(
                self.compo,
                self.ui,
                self.ring_bolt_circle_radius,
                self.config.ring_bolt_diameter,
                self.config.shaft_diameter,
                self.config.ring_bolt_count
            )
        except Exception as error:
            if self.ui:
                self.ui.messageBox("Brace Failed : " + str(error)) 
            return None

    def BuildOutputDisc(self):
        try:
            OutputDisc.OutputDisc(
                self.compo,
                self.ui,
                self.median_radius + self.roller_rad * 0.42,
                self.disc_bolt_circle_radius,
                self.output_cut_plane,
                self.config,
                self.printer_config
            )
        except Exception as error:
            if self.ui:
                self.ui.messageBox("OutputDisc Failed : " + str(error))
            return None

    def CreateWheelAssembly(self):
        WheelAssembly.WheelAssembly(self.compo,
            self.ui,
            1.5,
            (self.median_radius + self.config.roller_diameter * 1.8) * 2,
            (self.median_radius - (self.roller_rad * 3.3)) * 2,
            0.36 + self.config.roller_diameter * 0.5,
            self.config.disc_bolt_count,
            0.4
        )