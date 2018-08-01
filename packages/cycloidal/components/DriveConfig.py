# Copyright (C) 2018  Martin Muehlhaeuser <github@mmone.de>

import pickle
import codecs

class DriveConfig:
    def __init__(self):
        # cycloidal
        self.roller_count = 13
        self.roller_diameter = 0.5
        self.roller_spacing = 1.0
        self.cam_bearing_outer_diameter = 1.5
        self.cam_bearing_inner_diameter = 1.0
        self.shaft_bearing_diameter = 0.3
        self.shaft_diameter = 0.31

        # flange
        self.ring_bolt_count = 12
        self.ring_bolt_diameter = 0.21
        self.disc_bolt_count = 8
        self.disc_bolt_diameter = 0.21
        self.chamfer_ring_bolt_holes = False
        self.chamfer_disc_bolt_holes = False

        #output
        self.output_pin_diameter = 0.36
        self.output_bearing_ball_diameter = 0.5

        # components
        self.components = set(['Ring', 'Disc', 'Bearing Seat', 'Rollers', 'Cage', 'Cam', 'Brace', 'Output'])

    def Load(self, pickle_string):
        self.__dict__ = pickle.loads(codecs.decode(pickle_string.encode(), "base64"))

    def ToString(self):
        return codecs.encode(pickle.dumps(self.__dict__), "base64").decode()