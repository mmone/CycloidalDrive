# Copyright (C) 2018  Martin Muehlhaeuser <github@mmone.de>

import pickle
import codecs

class DriveConfig:
    def __init__(self):
        self.roller_count = 13
        self.roller_diameter = 0.5
        self.roller_spacing = 1.0
        self.cam_bearing_outer_diameter = 1.5
        self.cam_bearing_inner_diameter = 1.0
        self.ring_bolt_count = 12
        self.ring_bolt_diameter = 0.21
        self.disc_bolt_count = 8
        self.disc_bolt_diameter = 0.21
        self.components = set(['Ring', 'Disc', 'Bearing Seat', 'Rollers', 'Cage', 'Cam', 'Brace', 'Output Disc'])

    def Load(self, pickle_string):
        self.__dict__ = pickle.loads(codecs.decode(pickle_string.encode(), "base64"))

    def ToString(self):
        return codecs.encode(pickle.dumps(self.__dict__), "base64").decode()