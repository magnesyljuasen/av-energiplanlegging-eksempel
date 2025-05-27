import numpy as np
import streamlit as st
import pandas as pd
from .utilities import coverage_calculation, linear_interpolation, linear_regression
import scipy.constants as spc
import math

class Peakshaving:
    def __init__(self):
        self.set_simple_sizing_conditions()

    def set_simple_sizing_conditions(self):
        self.RHO = 0.96
        self.HEAT_CAPACITY = 4.2
        self.TO_TEMP = 60
        self.FROM_TEMP = 40

    def estimate_tank_size(self, building):
        K = 0.5/100 
        building_area = building.data.area[0] # area
        available_area = building_area * K
        tank_area = math.pi*(((595-160)/1000)/2)**2
        tank_volume = tank_area * (1775/1000) * 1000
        total_tank_volume = tank_volume * available_area
        return total_tank_volume
    
    def simple_sizing(self, building, energy_array, selected_tank_size=200, mode='dhw'):
        REDUCTION = 0
        tank_size_liters = 0
        coarse_step = 0.1  
        fine_step = 0.001   
        overshot = False   
        
        count = 0
        while True:
            if not overshot:
                REDUCTION += coarse_step
            else:
                REDUCTION += fine_step  # Reverse with finer resolution

            NEW_MAX_EFFECT = np.max(energy_array - REDUCTION)

            peakshaving_arr = np.copy(energy_array)
            max_effect_arr = np.maximum(0, energy_array - NEW_MAX_EFFECT)

            day = 12
            peakshave_accumulated = 0
            accumulated_arr = []
            shave_days = 24

            for i in range(0, len(energy_array) - day):
                peakshave = max_effect_arr[i + day]
                peakshave_accumulated += peakshave
                accumulated_arr.append(peakshave)
                    
                if peakshave > 0:
                    peakshaving_arr[i + day] -= peakshave # tar bort peak
                    for j in range(shave_days):  # shave bort i de x timene før
                        peakshaving_arr[(i+day-shave_days) + j] += peakshave / shave_days
                else:
                    accumulated_arr.append(peakshave_accumulated)
                    peakshave_accumulated = 0
            max_accumulated_energy = max(accumulated_arr) if accumulated_arr else 0

            tank_size = (max_accumulated_energy * 3600) / (self.RHO * self.HEAT_CAPACITY * (self.TO_TEMP - self.FROM_TEMP)) / 1000  # in m³
            tank_size_liters = round(tank_size * 1000, 1)

            if abs(tank_size_liters - selected_tank_size) <= ((selected_tank_size/100) * 1):  # Allow small tolerance
                break

            if tank_size_liters > selected_tank_size and not overshot:
                overshot = True
                REDUCTION -= coarse_step  # Backtrack by the coarse step to refine
            
            if count > 100:
                break
            count = count + 1
        building.results.investment.peakshaving = tank_size_liters

        if mode == 'dhw':
            building.results.energy.dhw_reduction = building.results.energy.dhw - peakshaving_arr
            building.results.energy.dhw = peakshaving_arr

            discharging_arr = np.where(building.results.energy.dhw_reduction > 0, building.results.energy.dhw_reduction, 0)
            charging_arr = -np.where(building.results.energy.dhw_reduction < 0, building.results.energy.dhw_reduction, 0)

        elif mode == 'spaceheating':
            building.results.energy.spaceheating_reduction = building.results.energy.spaceheating - peakshaving_arr
            building.results.energy.spaceheating = peakshaving_arr

            discharging_arr = np.where(building.results.energy.spaceheating_reduction > 0, building.results.energy.spaceheating_reduction, 0)
            charging_arr = -np.where(building.results.energy.spaceheating_reduction < 0, building.results.energy.spaceheating_reduction, 0)

        return peakshaving_arr, accumulated_arr, charging_arr, discharging_arr