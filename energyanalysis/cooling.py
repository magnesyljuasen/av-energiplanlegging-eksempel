import numpy as np
import pandas as pd
from .utilities import coverage_calculation

class Cooling:
    def __init__(self):
        self.set_simple_sizing_conditions()

    def set_simple_sizing_conditions(self):
        pass
    
    def simple_sizing(self, building, cooling_coverage = 100, cooling_cop = None):
        """Enkel beregning for frikjøling / fjernkjøling / maskinkjøling """
        cooling_covered, cooling_peak, cooling_compressor, cooling_pump_size = 0, 0, 0, 0
        try:
            if cooling_coverage != 100:
                cooling = coverage_calculation(cooling_coverage, building.results.energy.cooling)
                cooling_peak = building.results.energy.cooling - cooling
            else:
                cooling = building.results.energy.cooling
            if cooling_cop == None:
                # Frikjøling / fjernkjøling
                cooling_covered = cooling
            else:
                # Maskinkjøling
                cooling_compressor = cooling/cooling_cop
                cooling_extracted_from_air = cooling - cooling_compressor
                cooling_covered = cooling_compressor + cooling_extracted_from_air
                cooling_pump_size = (cooling_extracted_from_air + cooling_compressor).max() 
        except:
            pass

        building.results.energy.cooling_covered = cooling_covered
        building.results.energy.cooling_peak = cooling_peak
        building.results.energy.cooling_compressor = cooling_compressor
        building.results.investment.cooling_pump_size = cooling_pump_size
        
        return cooling_covered, cooling_peak, cooling_compressor, cooling_pump_size
