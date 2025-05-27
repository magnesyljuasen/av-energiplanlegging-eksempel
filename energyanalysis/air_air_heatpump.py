import numpy as np
import pandas as pd
from .utilities import coverage_calculation, linear_interpolation, linear_regression

class AirAirHeatPump:
    def __init__(self):
        self.set_simple_sizing_conditions()

    def set_simple_sizing_conditions(self):
        pass
    
    def simple_sizing(self, building, spaceheating_coverage = 80, spaceheating_cop = 2.5, dhw_coverage = 70, dhw_cop = 2.5):
        """Enkel beregning som bruker dekningsgrader på hhv. 
        romoppvarming og varmtvann samt flate COPer for å 
        returnere seriene som leveres fra luft-vann-varmepumpe. """

        spaceheating = coverage_calculation(spaceheating_coverage, building.results.energy.spaceheating)
        dhw = coverage_calculation(dhw_coverage, building.results.energy.dhw)
        spaceheating_compressor = spaceheating/spaceheating_cop
        spaceheating_extracted_from_air = spaceheating - spaceheating_compressor
        spaceheating_peak = building.results.energy.spaceheating - spaceheating
        dhw_compressor = dhw/dhw_cop
        dhw_extracted_from_air = dhw - dhw_compressor
        dhw_peak = building.results.energy.dhw - dhw
        compressor = spaceheating_compressor + dhw_compressor
        extracted_from_air = spaceheating_extracted_from_air + dhw_extracted_from_air
        peak = spaceheating_peak + dhw_peak
        building.results.energy.air_water_heat_pump_compressor = compressor
        building.results.energy.air_water_heat_pump_extracted_from_air = extracted_from_air
        building.results.energy.air_water_heat_pump_peak = peak
        building.results.energy.air_water_heat_pump_electricity = compressor + peak
        #--
        heat_pump_size = (extracted_from_air + compressor).max()
        building.results.investment.air_water_heat_pump_size = heat_pump_size
        return compressor, extracted_from_air, peak, heat_pump_size
    
    def set_simulation_parameters(self, COP_NOMINAL = 4.8, P_NOMINAL = 10):
        self.TECHNICAL_SHEET_FLUID_TEMPERATURE_MIN = np.array([-20, -15, -10, -7, 2, 7, 10, 18])
        self.TECHNICAL_SHEET_COP_MIN = np.array([2.16, 2.48, 2.83, 3.06, 3.79, 4.13, 4.6, 5.31])
        self.TECHNICAL_SHEET_FLUID_TEMPERATURE_MAX = np.array([-20, -15, -10, -7, 2, 7, 10, 18])
        self.TECHNICAL_SHEET_COP_MAX = np.array([1.8, 2.06, 2.36, 2.56, 3.04, 3.33, 3.66, 4.17]) 

        self.P_3031 = np.array([
            [0.48, 0.76, 1,], #1.25],
            [0.24, 0.38, 0.5,], #0.62],
            [0.12, 0.19, 0.25,]# 0.31]
            ])
        
        self.COP_3031 = np.array([
            [0.5, 0.69, 0.99,], #1.19],
            [0.51, 0.73, 1,], #1.24],
            [0.45, 0.65, 0.93,] #1.13]
            ])
        
        self.COP_NOMINAL = COP_NOMINAL
        self.P_NOMINAL = P_NOMINAL

    def _calculate_cop(self, source_temperature, SLOPE_FLOW_TEMPERATURE_MIN, SLOPE_FLOW_TEMPERATURE_MAX, INTERSECT_FLOW_TEMPERATURE_MIN, INTERSECT_FLOW_TEMPERATURE_MAX, flow_temperature_array, FLOW_TEMPERATURE_MAX, FLOW_TEMPERATURE_MIN):
        cop_array = np.zeros(8760)
        for i in range(0, len(cop_array)):
            if flow_temperature_array[i] == FLOW_TEMPERATURE_MAX:
                cop_array[i] = SLOPE_FLOW_TEMPERATURE_MAX * source_temperature[i] + INTERSECT_FLOW_TEMPERATURE_MAX
            elif flow_temperature_array[i] == FLOW_TEMPERATURE_MIN:
                cop_array[i] = SLOPE_FLOW_TEMPERATURE_MIN * source_temperature[i] + INTERSECT_FLOW_TEMPERATURE_MIN
            else:
                slope_interpolated = linear_interpolation(flow_temperature_array[i], FLOW_TEMPERATURE_MAX, FLOW_TEMPERATURE_MIN, SLOPE_FLOW_TEMPERATURE_MAX, SLOPE_FLOW_TEMPERATURE_MIN)
                intercept_interpolated = linear_interpolation(flow_temperature_array[i], FLOW_TEMPERATURE_MAX, FLOW_TEMPERATURE_MIN, INTERSECT_FLOW_TEMPERATURE_MAX, INTERSECT_FLOW_TEMPERATURE_MIN)
                cop_interpolated = slope_interpolated * source_temperature[i] + intercept_interpolated
                cop_array[i] = cop_interpolated
        return cop_array
    
    def nspek_heatpump_calculation(self, building, power_reduction = 0, cop_reduction = 0, defrosting_min = -5, defrosting_max = 5):
        outdoor_temperature_array = building.data.outdoor_temperature
        heating_demand_array = building.results.energy.spaceheating
        COP_NOMINAL = self.COP_NOMINAL  # Nominell COP
        temperature_datapoints = [-15, 2, 7,] #15] # SN- NSPEK 3031:2023 - tabell K.13
        P_3031_35 = self.P_3031
        COP_3031_35 = self.COP_3031
        
        P_3031_list, COP_3031_list = [], []
        for i in range(0, len(temperature_datapoints)):
            P_3031_list.append(np.polyfit(x = temperature_datapoints, y = P_3031_35[i], deg = 1))
            COP_3031_list.append(np.polyfit(x = temperature_datapoints, y = COP_3031_35[i], deg = 1))

        P_HP_DICT, COP_HP_DICT, INTERPOLATE_HP_DICT = [], [], []
        for index, outdoor_temperature in enumerate(outdoor_temperature_array):
            p_hp_list = np.array([np.polyval(P_3031_list[0], outdoor_temperature), np.polyval(P_3031_list[1], outdoor_temperature), np.polyval(P_3031_list[2], outdoor_temperature)])
            cop_hp_list = np.array([np.polyval(COP_3031_list[0], outdoor_temperature), np.polyval(COP_3031_list[1], outdoor_temperature), np.polyval(COP_3031_list[2], outdoor_temperature)]) * COP_NOMINAL
            interpolate_hp_list = np.polyfit(x = p_hp_list, y = cop_hp_list, deg = 0)[0]
            #--
            P_HP_DICT.append(p_hp_list)
            COP_HP_DICT.append(cop_hp_list)
            INTERPOLATE_HP_DICT.append(interpolate_hp_list)
        #--
        heatpump, cop = np.zeros(8760), np.zeros(8760)

        for i, outdoor_temperature in enumerate(outdoor_temperature_array):
            effekt = heating_demand_array[i]
            if outdoor_temperature < -20:
                cop[i] = 1
                heatpump[i] = 0
            else:
                varmepumpe_effekt_verdi = effekt
                p_hp_list = P_HP_DICT[i] * self.P_NOMINAL
                cop_hp_list = COP_HP_DICT[i]
                if effekt >= p_hp_list[0]:
                    varmepumpe_effekt_verdi = p_hp_list[0] - (p_hp_list[0]*power_reduction/100)
                    if outdoor_temperature > defrosting_min and outdoor_temperature < defrosting_max:
                        cop_verdi = cop_hp_list[0] - (cop_hp_list[0]*cop_reduction/100)
                    else:
                        cop_verdi = cop_hp_list[0]
                elif effekt <= p_hp_list[2]:
                    if outdoor_temperature > defrosting_min and outdoor_temperature < defrosting_max:
                        cop_verdi = cop_hp_list[2] - (cop_hp_list[2]*cop_reduction/100)
                    else:
                        cop_verdi = cop_hp_list[2]
                else:
                    if outdoor_temperature > defrosting_min and outdoor_temperature < defrosting_max:
                        cop_verdi = INTERPOLATE_HP_DICT[i] - (INTERPOLATE_HP_DICT[i] * cop_reduction/100)
                    else:
                        cop_verdi = INTERPOLATE_HP_DICT[i]
                heatpump[i] = varmepumpe_effekt_verdi
                cop[i] = cop_verdi

        self.heatpump_array = heatpump
        self.from_air_array = self.heatpump_array - self.heatpump_array / np.array(cop_verdi)
        self.compressor_array = self.heatpump_array - self.from_air_array
        self.peak_array = heating_demand_array - self.heatpump_array
        self.cop_array = cop

        building.results.energy.air_air_heat_pump_compressor = self.compressor_array
        building.results.energy.air_air_heat_pump_extracted_from_air = self.from_air_array
        building.results.energy.air_air_heat_pump_peak = self.peak_array
        building.results.energy.air_air_heat_pump_electricity = self.compressor_array + self.peak_array
        #--
        building.results.investment.air_air_heat_pump_size = self.P_NOMINAL
        building.results.investment_lifetime.air_air_heat_pump_size = 12
        building.results.reinvestment_cost.air_air_heat_pump_size = 300000
        building.results.investment_cost.air_air_heat_pump_size = 300000
 
    
    def advanced_sizing_of_heat_pump(self, building, spaceheating_coverage = 80, dhw_coverage = 70):
        spaceheating_heatpump = coverage_calculation(percentage=spaceheating_coverage, array=building.results.energy.spaceheating)
        dhw_heatpump = coverage_calculation(percentage=dhw_coverage, array=building.results.energy.dhw)
        self.heatpump_array = spaceheating_heatpump + dhw_heatpump
        self.peak_array = building.results.energy.spaceheating + building.results.energy.dhw - self.heatpump_array

        slope_flow_temperature_min, intersect_flow_temperature_min = linear_regression(self.TECHNICAL_SHEET_FLUID_TEMPERATURE_MIN, self.TECHNICAL_SHEET_COP_MIN)
        slope_flow_temperature_max, intersect_flow_temperature_max = linear_regression(self.TECHNICAL_SHEET_FLUID_TEMPERATURE_MAX, self.TECHNICAL_SHEET_COP_MAX)

        source_temperature = building.data.outdoor_temperature     
        self.cop_array = self._calculate_cop(
            source_temperature=source_temperature,
            SLOPE_FLOW_TEMPERATURE_MIN=slope_flow_temperature_min,
            SLOPE_FLOW_TEMPERATURE_MAX=slope_flow_temperature_max,
            INTERSECT_FLOW_TEMPERATURE_MIN=intersect_flow_temperature_min,
            INTERSECT_FLOW_TEMPERATURE_MAX=intersect_flow_temperature_max,
            flow_temperature_array=building.flow_temperature_array,
            FLOW_TEMPERATURE_MAX=self.building_instance.FLOW_TEMPERATURE_MAX,
            FLOW_TEMPERATURE_MIN=self.building_instance.FLOW_TEMPERATURE_MIN,
            )
        self.from_air_array = self.heatpump_array - self.heatpump_array/self.cop_array
        self.compressor_array = self.heatpump_array - self.from_air_array

        self.building.results.energy['heatpump_production_array'] = -self.heatpump_array
        self.building.results.energy['heatpump_consumption_compressor_array'] = self.compressor_array
        self.building.results.energy['heatpump_consumption_peak_array'] = self.peak_array  