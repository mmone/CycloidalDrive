# Copyright (C) 2018  Martin Muehlhaeuser <github@mmone.de>

class PrinterConfig:
    def __init__(self, nozzle_width_mm, layer_height_mm):
        self.nozzle_width = nozzle_width_mm
        self.layer_height = layer_height_mm

    def lToCm(self, layer_count):
        return layer_count * self.layer_height * 0.1

    def ewToCm(self, extrusion_count):
        return extrusion_count * self.nozzle_width * 0.1