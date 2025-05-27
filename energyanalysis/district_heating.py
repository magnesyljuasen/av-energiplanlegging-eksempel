import numpy as np
import pandas as pd
from .utilities import coverage_calculation


class DistrictHeating:
    def __init__(self):
        self.set_simple_sizing_conditions()

    def set_simple_sizing_conditions(self):
        pass
    
    def simple_sizing(self, building, spaceheating_coverage = 100, dhw_coverage = 100):
        """Enkel beregning som beregner fjernvarme. """

        spaceheating = coverage_calculation(spaceheating_coverage, building.results.energy.spaceheating)
        dhw = coverage_calculation(dhw_coverage, building.results.energy.dhw)
        spaceheating_peak = building.results.energy.spaceheating - spaceheating
        dhw_peak = building.results.energy.dhw - dhw
        district_heating_covered = spaceheating + dhw
        building.results.energy.district_heating = district_heating_covered
