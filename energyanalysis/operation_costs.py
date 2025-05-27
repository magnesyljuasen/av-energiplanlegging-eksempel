import numpy as np
import pandas as pd
import streamlit as st

class OperationCosts:
    def __init__(self):
        self.set_simple_conditions()

    def set_simple_conditions(self, electric_price=1, district_heating_price=1):
        self.electric_price = electric_price
        self.district_heating_price = district_heating_price
        self.mode = 'Simple'

    def set_advanced_conditions(self, year, region, tarrifs):
        df = pd.read_excel('src/data/spotprices.xlsx', sheet_name=str(year))
        self.spotprice_array = df[region].to_numpy()
        self.tarriffs = tarrifs
        self.get_tarriffs()
        self.set_network_energy_component()
        self.mode = 'Advanced'

    def get_tarriffs(self):
        if self.tarriffs == "Elvia":
            self.energy_component_night_jan_mar = 32.09
            self.energy_component_night_apr_dec = 40.75
            self.energy_component_day_jan_mar = 39.59
            self.energy_component_day_apr_dec = 48.25
            self.capacity_component_0_2 = 120
            self.capacity_component_2_5 = 190
            self.capacity_component_5_10 = 305
            self.capacity_component_10_15 = 420
            self.capacity_component_15_20 = 535
            self.capacity_component_20_25 = 650
            self.capacity_component_25_50 = 1225
            self.capacity_component_50_75 = 1800
            self.capacity_component_75_100 = 2375
            self.capacity_component_100 = 4750
        elif self.tarriffs == 'Arva':
            self.energy_component_night_jan_mar = 11.6
            self.energy_component_night_apr_dec = 11.6
            self.energy_component_day_jan_mar = 23.1
            self.energy_component_day_apr_dec = 23.1
            self.capacity_component_0_2 = 85
            self.capacity_component_2_5 = 201
            self.capacity_component_5_10 = 398
            self.capacity_component_10_15 = 595
            self.capacity_component_15_20 = 792
            self.capacity_component_20_25 = 989
            self.capacity_component_25_50 = 1972
            self.capacity_component_50_75 = 2955
            self.capacity_component_75_100 = 3939
            self.capacity_component_100 = 5945

    def set_network_energy_component(self):
        hours_in_year = pd.date_range(start='2023-01-01 00:00:00', end='2023-12-31 23:00:00', freq='h')
        network_energy_array = np.zeros(8760)
        for i in range(0, len(network_energy_array)):
            element = hours_in_year[i]
            hour = element.hour
            month = element.month
            weekday = element.dayofweek
            if (0 <= hour < 6) or (22 <= hour <= 23) or (weekday in [5,6]): # night
                if (month in [1, 2, 3]): # jan - mar
                    energy_component = self.energy_component_night_jan_mar
                else: # apr - dec
                    energy_component = self.energy_component_night_apr_dec
            else: # day
                if (month in [1, 2, 3]): # jan - mar
                    energy_component = self.energy_component_day_jan_mar
                else:
                    energy_component = self.energy_component_day_apr_dec # apr - dec
            energy_component = energy_component/100
            network_energy_array[i] = energy_component
        self.network_energy_array = network_energy_array
    
    def _network_capacity_component(self, demand_array):
        previous_index = 0
        daymax = 0
        daymax_list = []
        series_list = []
        cost_per_hour = 0
        for index, value in enumerate(demand_array):
            if value > daymax:
                daymax = value
            if index % 24 == 23:
                daymax_list.append(daymax)
                daymax = 0
            if index in [744, 1416, 2160, 2880, 3624, 4344, 5088, 5832, 6552, 7296, 8016, 8759]:
                daymax_list = np.sort(daymax_list)[::-1]
                average_max_value = np.mean(daymax_list[0:3])
                if 0 < average_max_value <= 2:
                    cost = self.capacity_component_0_2
                elif 2 < average_max_value <= 5:
                    cost = self.capacity_component_2_5
                elif 5 < average_max_value <= 10:
                    cost = self.capacity_component_5_10
                elif 10 < average_max_value <= 15:
                    cost = self.capacity_component_10_15
                elif 15 < average_max_value <= 20:
                    cost = self.capacity_component_15_20
                elif 20 < average_max_value <= 25:
                    cost = self.capacity_component_20_25
                elif 25 < average_max_value <= 50:
                    cost = self.capacity_component_25_50
                elif 50 < average_max_value <= 75:
                    cost = self.capacity_component_50_75 
                elif 75 < average_max_value <= 100:
                    cost = self.capacity_component_75_100
                elif average_max_value > 100:
                    cost = self.capacity_component_100
                else:
                    cost = 0
                cost_per_hour = cost/(index-previous_index)
                daymax_list = []
                previous_index = index
            series_list.append(cost_per_hour)
        return series_list
    
    def calculation(self, building):
        """Enkel beregning som beregner driftskostnader for tiltak ut ifra flat strømpris. """
        dict_results = vars(building.results.energy)
        keys_to_iterate = list(dict_results.keys())
        for key in keys_to_iterate:
            value = dict_results[key]            
            
            if isinstance(value, np.ndarray) and "cost" not in key.lower() and "co2" not in key.lower():
                if len(value) == 8760:
                    if self.mode == 'Advanced':
                        below_zero = np.where(value < 0, value, 0)
                        above_zero = np.where(value > 0, value, 0)
                        if below_zero.sum() < 0: # Kun spotpris under 0
                            costs_below_zero = self.spotprice_array * below_zero
                            costs_above_zero = self.spotprice_array * above_zero + self.network_energy_array*above_zero + self._network_capacity_component(above_zero)
                            variable_cost = costs_below_zero + costs_above_zero
                        else:
                            spotcosts_array = self.spotprice_array * value # spotpris
                            network_energycosts_array = self.network_energy_array * value # energiledd
                            network_capacitycosts_array = self._network_capacity_component(value) # kapasitetsledd
                            variable_cost = spotcosts_array + network_energycosts_array + network_capacitycosts_array
                    else:
                        variable_cost = value * self.electric_price
                    setattr(building.results.operation_cost, key, variable_cost)
        #--
        return 0
    
    def get_spotprices_in_region(self, region):
        df_spot = pd.DataFrame()
        for year in [2020, 2021, 2022, 2023]:
            df = pd.read_excel('src/data/spotprices.xlsx', sheet_name=str(year))
            array = df[region].to_numpy()
            df_spot[year] = array
        return df_spot
    
    def get_spotprices_in_year(self, year):
        df_spot = pd.DataFrame()
        df = pd.read_excel('src/data/spotprices.xlsx', sheet_name=str(year))
        for region in ['NO1', 'NO2', 'NO3', 'NO4', 'NO5']:
            array = df[region].to_numpy()
            df_spot[region] = array
        return df_spot
    