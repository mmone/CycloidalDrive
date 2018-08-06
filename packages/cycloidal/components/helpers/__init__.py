# Copyright (C) 2018  Martin Muehlhaeuser <github@mmone.de>

import adsk.core, adsk.fusion, math

def CreateCollection(*entities):
    collection = adsk.core.ObjectCollection.create()
    for entity in entities:
        collection.add(entity)
    return collection

def SymmetricExtrude(component, profiles, thickness, operation, offset = None, bodies = None):
    extrudeInput = component.features.extrudeFeatures.createInput(
        profiles,
        operation
    )
    extrudeInput.setSymmetricExtent(adsk.core.ValueInput.createByReal(thickness), True)
    if offset:
        extrudeInput.startExtent = adsk.fusion.OffsetStartDefinition.create( adsk.core.ValueInput.createByReal(offset))
    
    if bodies:
        extrudeInput.participantBodies = bodies

    feature = component.features.extrudeFeatures.add(extrudeInput)
    return feature


def OneSideExtrude(component, profiles, offset, extend, direction, operation, bodies = None):
    extrudeInput = component.features.extrudeFeatures.createInput(
        profiles,
        operation
    )
    
    extentDistance = adsk.fusion.DistanceExtentDefinition.create(
        adsk.core.ValueInput.createByReal(extend)
    )
    
    extrudeInput.setOneSideExtent(extentDistance, direction)
    extrudeInput.startExtent = adsk.fusion.OffsetStartDefinition.create(
        adsk.core.ValueInput.createByReal(offset)
    )

    if bodies:
        extrudeInput.participantBodies = bodies

    feature = component.features.extrudeFeatures.add(extrudeInput)

    #if bodies:
    #    feature.timelineObject.rollTo(True)
    #    feature.participantBodies = bodies
    #    feature.timelineObject.rollTo(False)
    return feature

def CircularPattern(component, entities, axis, quantity, compute_option = None):
    circular_input = component.features.circularPatternFeatures.createInput(entities, axis)
    circular_input.quantity = adsk.core.ValueInput.createByReal(quantity)
    if(compute_option):
        circular_input.patternComputeOption = compute_option
    return component.features.circularPatternFeatures.add(circular_input)

def Mirror(component, entities, plane):
    mirror_input = component.features.mirrorFeatures.createInput(
        entities,
        plane
    )
    return component.features.mirrorFeatures.add(mirror_input)

def Combine(
        component,
        operation,
        target_entity,
        *tool_entities
    ):

    collection = adsk.core.ObjectCollection.create()
    for entity in tool_entities:
        collection.add(entity)
    create_input = component.features.combineFeatures.createInput(
        target_entity,
        collection
    )
    return component.features.combineFeatures.add(create_input)

def Revolve(component, profile, axis, operation, bodies = None):
    feature_input = component.features.revolveFeatures.createInput(profile, axis, operation)
    feature_input.setAngleExtent(False,  adsk.core.ValueInput.createByReal(2.0 * math.pi))
    feature = component.features.revolveFeatures.add(feature_input)
    if bodies:
        feature.timelineObject.rollTo(True)
        feature.participantBodies = bodies
        feature.timelineObject.rollTo(False)
    return feature

def ChamferEdgesSimple(component, edges, chamfer_width):
    chamferInput = component.features.chamferFeatures.createInput(
        edges,
        True
    )
    chamferInput.setToEqualDistance(adsk.core.ValueInput.createByReal(chamfer_width))
    return component.features.chamferFeatures.add(chamferInput)

def FilletEdgesSimple(component, edges, radius):
    filletInput = component.features.filletFeatures.createInput()
    filletInput.addConstantRadiusEdgeSet(edges, adsk.core.ValueInput.createByReal(radius), False)
    return component.features.filletFeatures.add(filletInput)

def CreateSketch(component, name, deferred, visible, plane = None):
    if not plane:
        plane = component.xYConstructionPlane
        
    sketch = component.sketches.add(plane)
    sketch.name = name
    sketch.isComputeDeferred = deferred
    sketch.isLightBulbOn = visible
    return sketch

def CreateSketchOnPlane(component, name, deferred, visible, plane):
    sketch = component.sketches.add(plane)
    sketch.name = name
    sketch.isComputeDeferred = deferred
    sketch.isLightBulbOn = visible
    return sketch

def AddCircle(sketch, x, y, z, radius, fixed = True):
    circle = sketch.sketchCurves.sketchCircles.addByCenterRadius(
        adsk.core.Point3D.create(x, y, z),
        radius
    )
    circle.isFixed = fixed
    return circle

def AddLine(sketch, x1, y1, z1, x2, y2, z2, fixed = True):
    line = sketch.sketchCurves.sketchLines.addByTwoPoints(
        adsk.core.Point3D.create(x1, y1, z1),
        adsk.core.Point3D.create(x2, y2, z2)
    )
    line.isFixed = fixed
    return line
'''
def AddHex(sketch, width):
    inc = math.pi * 2.0 / 6.0
    r = w / ( 2 * math.cos(math.pi * 2.0 / 12.0))
    p0 = adsk.core.Point3D.create(math.sin(i * inc) * r, math.sin(i * inc) * r, 0)

    line = sketch.sketchCurves.sketchLines.addByTwoPoints(
        adsk.core.Point3D.create(math.sin(i * inc) * r, math.sin(i * inc) * r, 0),
        adsk.core.Point3D.create(math.sin((i+1) * inc) * r, math.sin((i+1) * inc) * r, 0)
    )
    for i in range(0, 6):
        line = sketch.sketchCurves.sketchLines.addByTwoPoints(
            adsk.core.Point3D.create(math.sin(i * inc) * r, math.sin(i * inc) * r, 0),
            adsk.core.Point3D.create(math.sin((i+1) * inc) * r, math.sin((i+1) * inc) * r, 0)
        )
            adsk.core.Point3D.create(x1, y1, z1)
            top_1.endSketchPoint, first_point_top)
        sketch.sketchCurves.sketchLines.addByTwoPoints(middle_1.endSketchPoint, first_point_middle)
    '''