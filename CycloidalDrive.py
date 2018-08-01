# Creates a pure rolling cycloidal drive with
# variable effective diameter rollers
#
# Copyright (C) 2018  Martin Muehlhaeuser <github@mmone.de>

from .packages.cycloidal import CycloidalComponent
from .packages.cycloidal.components import PrinterConfig
from .packages.cycloidal.components import DriveConfig
import adsk.core, adsk.fusion, adsk.cam, traceback

# Globals
_app = None
_ui = None
_units = ''

_handlers = []

def run(context):
    try:
        global _app, _ui
        _app = adsk.core.Application.get()
        _ui  = _app.userInterface

        cmd_def = _ui.commandDefinitions.itemById('adskCycloidalDrive')
        if not cmd_def:
            cmd_def = _ui.commandDefinitions.addButtonDefinition(
                'mmoneCycloidalDrive',
                'Cycloidal Drive',
                'Creates a cycloidal drive component',
                'resources/CycloidalDrive') 
        
        # Connect to the command created event.
        on_command_created = CommandCreatedHandler()
        cmd_def.commandCreated.add(on_command_created)
        _handlers.append(on_command_created)
        
        # Execute the command.
        #cmd_def.execute()

        panel = _ui.allToolbarPanels.itemById('SolidScriptsAddinsPanel')
        cntrl = panel.controls.itemById('mmoneCycloidalDrive')
        if not cntrl:
            panel.controls.addCommand(cmd_def)

        # prevent this module from being terminate when the script returns, because we are waiting for event handlers to fire
        adsk.autoTerminate(False)
    except:
        if _ui:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def stop(context):
    try:        
        # Delete controls and associated command definitions created by this add-ins
        panel = _ui.allToolbarPanels.itemById('SolidScriptsAddinsPanel')
        cmd = panel.controls.itemById('mmoneCycloidalDrive')
        if cmd:
            cmd.deleteMe()
        cmdDef = _ui.commandDefinitions.itemById('mmoneCycloidalDrive')
        if cmdDef:
            cmdDef.deleteMe() 
    except:
        if _ui:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

# Event handler for the commandCreated event.
class CommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            event_args = adsk.core.CommandCreatedEventArgs.cast(args)
            
            # Verify that a Fusion design is active.
            des = adsk.fusion.Design.cast(_app.activeProduct)
            if not des:
                _ui.messageBox('A Fusion design must be active when invoking this command.')
                return()
                
            # Determine whether to use inches or millimeters as the intial default.
            global _units
            if des.unitsManager.defaultLengthUnits == 'in' or des.unitsManager.defaultLengthUnits == 'ft':
                _units = 'in'
            else:
                _units = 'mm'
            
            cmd = event_args.command
            cmd.isExecutedWhenPreEmpted = False
            inputs = cmd.commandInputs
            
            global _roller_count, _roller_diameter, _roller_spacing, _create_select, _cam_bearing_outer_dia, \
            _cam_bearing_inner_dia, _ring_bolt_count, _ring_bolt_dia, _disc_bolt_count, _disc_bolt_dia, \
            _output_pin_diameter, \
            _err_message, _drive_config, _info_message
            
            # Load existing parameter values
            _drive_config = DriveConfig.DriveConfig()
            drive_config_json = des.attributes.itemByName('CycloidalDrive', 'drive_config')
            if drive_config_json:
                _drive_config.Load(drive_config_json.value)

            # Define the command dialog.
            _roller_diameter = inputs.addValueInput(
                'roller_diameter',
                'Roller Diameter',
                _units,
                adsk.core.ValueInput.createByReal(_drive_config.roller_diameter)
            )
            _roller_count = inputs.addIntegerSpinnerCommandInput(
                'roller_count',
                'Number of Rollers',
                5, 100, 1,
                _drive_config.roller_count
            )
            _roller_spacing = inputs.addValueInput(
                'roller_spacing',
                'Roller Spacing',
                '',
                adsk.core.ValueInput.createByReal(_drive_config.roller_spacing)
            )
            _output_pin_diameter = inputs.addValueInput(
                'output_pin_diameter',
                'Output Pin Diameter',
                _units,
                adsk.core.ValueInput.createByReal(_drive_config.output_pin_diameter)
            )

            inputs.addTextBoxCommandInput('textbox_1', '', "<br><b>Cam Bearing Settings</b>", 2, True)

            _cam_bearing_outer_dia = inputs.addValueInput(
                'bearing_outer_dia',
                'Outer Diameter',
                _units,
                adsk.core.ValueInput.createByReal(_drive_config.cam_bearing_outer_diameter)
            )

            _cam_bearing_inner_dia = inputs.addValueInput(
                'bearing_inner_dia',
                'Inner Diameter',
                _units,
                adsk.core.ValueInput.createByReal(_drive_config.cam_bearing_inner_diameter)
            )

            inputs.addTextBoxCommandInput('textbox_2', '', "<br><b>Flange Settings</b>", 2, True) 

            _ring_bolt_count = inputs.addIntegerSpinnerCommandInput(
                'ring_bolt_count',
                'Number of Ring Bolts',
                3, 16, 1,
                _drive_config.ring_bolt_count
            )

            _ring_bolt_dia = inputs.addValueInput(
                'ring_bolt_dia',
                'Ring Bolt Diameter',
                _units,
                adsk.core.ValueInput.createByReal(_drive_config.ring_bolt_diameter)
            )

            _disc_bolt_count = inputs.addIntegerSpinnerCommandInput(
                'disc_bolt_count',
                'Number of Disc Bolts',
                3, 16, 1,
                _drive_config.disc_bolt_count
            )

            _disc_bolt_dia = inputs.addValueInput(
                'disc_bolt_dia',
                'Disc Bolt Diameter',
                _units,
                adsk.core.ValueInput.createByReal(_drive_config.disc_bolt_diameter)
            )

            inputs.addTextBoxCommandInput('textbox_3', '', "", 1, True)

            _create_select = inputs.addDropDownCommandInput('create_select', 'Components', adsk.core.DropDownStyles.CheckBoxDropDownStyle)
            _create_select_items = _create_select.listItems
            _create_select_items.add('Ring',         ('Ring' in _drive_config.components))
            _create_select_items.add('Disc',         ('Disc' in _drive_config.components))
            _create_select_items.add('Bearing Seat', ('Bearing Seat' in _drive_config.components))
            _create_select_items.add('Cam',          ('Cam' in _drive_config.components))
            _create_select_items.add('Cage',         ('Cage' in _drive_config.components))
            _create_select_items.add('Output',       ('Output' in _drive_config.components))
            _create_select_items.add('Brace',        ('Brace' in _drive_config.components))
            _create_select_items.add('Rollers',      ('Rollers' in _drive_config.components))

            _err_message = inputs.addTextBoxCommandInput('err_message', '', '', 2, True)
            _err_message.isFullWidth = True
            
            _info_message = inputs.addTextBoxCommandInput('info_message', '', '', 2, True)
            _info_message.isFullWidth = True

            inputs.addTextBoxCommandInput(
                'textbox_4', '',
                "<a href=\"http://blog.mmone.de/cycloidal-drive/\"><b>Parameter Documentation</b></a>",
                1, True
            )

            # Connect the neccesary event handlers.
            onExecute = CommandExecuteHandler()
            cmd.execute.add(onExecute)
            _handlers.append(onExecute)        
            
            onInputChanged = CommandInputChangedHandler()
            cmd.inputChanged.add(onInputChanged)
            _handlers.append(onInputChanged)     
            
            onValidateInputs = CommandValidateInputsHandler()
            cmd.validateInputs.add(onValidateInputs)
            _handlers.append(onValidateInputs)

            #onDestroy = CommandDestroyHandler()
            #cmd.destroy.add(onDestroy)
            #_handlers.append(onDestroy)
        except:
            if _ui:
                _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


class CommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            eventArgs = adsk.core.CommandEventArgs.cast(args)

            # Save the current values as attributes.
            design = adsk.fusion.Design.cast(_app.activeProduct)
            attributes = design.attributes

            _drive_config.roller_count = _roller_count.value
            _drive_config.roller_diameter = _roller_diameter.value
            _drive_config.roller_spacing = _roller_spacing.value
            _drive_config.output_pin_diameter = _output_pin_diameter.value

            _drive_config.cam_bearing_outer_diameter = _cam_bearing_outer_dia.value
            _drive_config.cam_bearing_inner_diameter = _cam_bearing_inner_dia.value

            _drive_config.ring_bolt_count = _ring_bolt_count.value
            _drive_config.ring_bolt_diameter = _ring_bolt_dia.value
            _drive_config.disc_bolt_count = _disc_bolt_count.value
            _drive_config.disc_bolt_diameter = _disc_bolt_dia.value

            _drive_config.components.clear()
            for item in _create_select.listItems:
                if(item.isSelected):
                    _drive_config.components.add(item.name)

            attributes.add('CycloidalDrive', 'drive_config', _drive_config.ToString())

            # Create the gear.
            printer_config = PrinterConfig.PrinterConfig(0.4, 0.2)
            c = CycloidalComponent.CycloidalComponent(
                    design,
                    _ui,
                    _drive_config,
                    printer_config
                )
            compo = c.GetComponent()
            
            if compo:
                desc = 'Cycloadial Drive;  '
                desc += str(_roller_count.value) + 'D: ' + str(_roller_diameter.value) + 'S: ' + str(_roller_spacing.value) + ';'
                compo.description = desc
        except:
            if _ui:
                _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
        
        
class CommandInputChangedHandler(adsk.core.InputChangedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            eventArgs = adsk.core.InputChangedEventArgs.cast(args)
            changedInput = eventArgs.input
            
            global _units
            
            median = CycloidalComponent.CycloidalComponent.CalculateMedianDiameter(_roller_diameter.value, _roller_count.value, _roller_spacing.value)
            rad = CycloidalComponent.CycloidalComponent.CalculateOuterRadius(median * 0.5, _roller_diameter.value, _ring_bolt_dia.value)

            _info_message.text = 'Outer Diameter: {}mm'.format(round((rad * 2.0) * 10.0, 2))
            #if changedInput.id == 'pressureAngle':
            #    if _pressureAngle.selectedItem.name == 'Custom':
            #        _pressureAngleCustom.isVisible = True
            #    else:
             #       _pressureAngleCustom.isVisible = False                    
        except:
            if _ui:
                _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
        
        
class CommandValidateInputsHandler(adsk.core.ValidateInputsEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            event_args = adsk.core.ValidateInputsEventArgs.cast(args)
            
            _err_message.text = ''

            if _roller_count.value < 6:
                _err_message.text = 'The number of rollers must be 6 or more.'
                event_args.areInputsValid = False
                return
            return
        except:
            if _ui:
                _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class CommandDestroyHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            eventArgs = adsk.core.CommandEventArgs.cast(args)

            # when the command is done, terminate the script
            # this will release all globals which will remove all event handlers
            adsk.terminate()
        except:
            if _ui:
                _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))