import numpy as np
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import streamlit as st

def building_compilation(building):
    def get_time_series(building, name, mode):
        if mode == 'energy':
            series = vars(building.results.energy)[name]
        elif mode == 'operation_cost':
            series = vars(building.results.operation_cost)[name]
        if series is not None:
            return abs(series)
        else:
            return np.zeros(8760)
    
    # energy
    building.results.energy.heating_demand = get_time_series(building, 'spaceheating', 'energy') + get_time_series(building, 'dhw', 'energy')
    building.results.energy.electric_demand = get_time_series(building, 'elspecific', 'energy') + get_time_series(building, 'electric_vehicle', 'energy')
    
    #TODO: Sjekk opp i denne
    # varme som gjenstår (går til strøm). varmebehov minus (levert varme fra grunnvarme, luftluft, luftvann, fjernvarme og ved) 
    #rest_heating = get_time_series(building, 'spaceheating', 'energy') + get_time_series(building, 'dhw', 'energy') - get_time_series(building, 'geoenergy_extracted_from_wells', 'energy') - get_time_series(building, 'geoenergy_compressor', 'energy') - get_time_series(building, 'air_water_heat_pump_extracted_from_air', 'energy') - get_time_series(building, 'air_water_heat_pump_compressor', 'energy') - get_time_series(building, 'air_air_heat_pump_extracted_from_air', 'energy') - get_time_series(building, 'air_air_heat_pump_compressor', 'energy') - get_time_series(building, 'district_heating', 'energy') - get_time_series(building, 'woodburning', 'energy')
    # elektrisk som gjenstår. behov pluss strøm til varmeløsninger minus egenprodusert strøm
    #rest_electric = get_time_series(building, 'elspecific', 'energy') + get_time_series(building, 'electric_vehicle', 'energy') + get_time_series(building, 'geoenergy_compressor', 'energy') + get_time_series(building, 'air_water_heat_pump_compressor', 'energy') + get_time_series(building, 'air_air_heat_pump_compressor', 'energy') - get_time_series(building, 'solar_production', 'energy')

    rest_heating = get_time_series(building, 'spaceheating', 'energy') + get_time_series(building, 'dhw', 'energy') - get_time_series(building, 'geoenergy_extracted_from_wells', 'energy') - get_time_series(building, 'air_water_heat_pump_extracted_from_air', 'energy') - get_time_series(building, 'air_air_heat_pump_extracted_from_air', 'energy') - get_time_series(building, 'district_heating', 'energy') - get_time_series(building, 'woodburning', 'energy')
    # elektrisk som gjenstår. behov pluss strøm til varmeløsninger minus egenprodusert strøm
    rest_electric = get_time_series(building, 'elspecific', 'energy') + get_time_series(building, 'electric_vehicle', 'energy') - get_time_series(building, 'solar_production', 'energy')

    # omgivelsesvarme
    building.results.energy.omgivelsesvarme_varmepumper = get_time_series(building, 'geoenergy_extracted_from_wells', 'energy') + get_time_series(building, 'air_air_heat_pump_extracted_from_air', 'energy') + get_time_series(building, 'air_water_heat_pump_extracted_from_air', 'energy')
    building.results.energy.elforbruk_varmepumper = get_time_series(building, 'geoenergy_compressor', 'energy') + get_time_series(building, 'air_air_heat_pump_compressor', 'energy') + get_time_series(building, 'air_water_heat_pump_compressor', 'energy')
    building.results.energy.levert_fra_varmepumper = building.results.energy.omgivelsesvarme_varmepumper + building.results.energy.elforbruk_varmepumper
    
    # elkjel
    building.results.energy.elkjel = rest_heating - get_time_series(building, 'geoenergy_compressor', 'energy') + get_time_series(building, 'air_air_heat_pump_compressor', 'energy') + get_time_series(building, 'air_water_heat_pump_compressor', 'energy')
    
    # til bygningsklasse
    building.results.energy.electricity_for_heating = rest_heating
    building.results.energy.electricity_for_elspecific = rest_electric
    building.results.energy.electricity_from_grid = rest_heating + rest_electric

    building.results.energy.renewable = building.results.energy.heating_demand + building.results.energy.electric_demand - building.results.energy.electricity_from_grid


    # andre serier 
    #building.results.energy.electric_demand = get_time_series(building, 'elspecific', 'energy') + get_time_series(building, 'electric_vehicle', 'energy')
    #building.results.energy.electric_heating = rest_heating
    #building.results.energy.el_til_varmepumper = get_time_series(building, 'air_water_heat_pump_compressor', 'energy') + get_time_series(building, 'air_air_heat_pump_compressor', 'energy') + get_time_series(building, 'geoenergy_compressor', 'energy')
    #building.results.energy.el_til_oppvarming = building.results.energy.el_direkte_elektrisk_oppvarming + building.results.energy.el_til_varmepumper
    #building.results.energy.omgivelsesvarme_til_varmepumper = get_time_series(building, 'geoenergy_extracted_from_wells', 'energy') + get_time_series(building, 'air_water_heat_pump_extracted_from_air', 'energy') + get_time_series(building, 'air_air_heat_pump_extracted_from_air', 'energy')
    #building.results.energy.solproduksjon = get_time_series(building, 'solar_production', 'energy')
    
    #try:
    #    building.results.energy.effektforbruk_el = building.results.energy.elspesifikt_forbruk + building.results.energy.el_til_oppvarming - building.results.energy.solproduksjon
    #except Exception:
    #    building.results.energy.effektforbruk_el = np.zeros(8760)

    # operation cost
    # varme som gjenstår (går til strøm). varmebehov minus produsert varme 
    rest_heating = get_time_series(building, 'spaceheating', 'operation_cost') + get_time_series(building, 'dhw', 'operation_cost') - get_time_series(building, 'geoenergy_extracted_from_wells', 'operation_cost') - get_time_series(building, 'geoenergy_compressor', 'operation_cost') - get_time_series(building, 'air_water_heat_pump_extracted_from_air', 'operation_cost') - get_time_series(building, 'air_water_heat_pump_compressor', 'operation_cost') - get_time_series(building, 'air_air_heat_pump_extracted_from_air', 'operation_cost') - get_time_series(building, 'air_air_heat_pump_compressor', 'operation_cost') - get_time_series(building, 'district_heating', 'operation_cost') - get_time_series(building, 'woodburning', 'operation_cost')
    # elektrisk som gjenstår. behov pluss strøm til varmeløsninger minus egenprodusert strøm
    rest_electric = get_time_series(building, 'elspecific', 'operation_cost') + get_time_series(building, 'electric_vehicle', 'operation_cost') + get_time_series(building, 'geoenergy_compressor', 'operation_cost') + get_time_series(building, 'air_water_heat_pump_compressor', 'operation_cost') + get_time_series(building, 'air_air_heat_pump_compressor', 'operation_cost') - get_time_series(building, 'solar_production', 'operation_cost')

    building.results.operation_cost.heating_balance = rest_heating
    building.results.operation_cost.electric_balance = rest_electric
    building.results.operation_cost.total_balance = rest_heating + rest_electric

    # investment
    dict_investment_cost = vars(building.results.investment_cost)
    building.results.investment_cost.total = sum(value for value in dict_investment_cost.values() if value is not None)
    

def hour_to_month(hourly_array, aggregation='sum'):
    result_array = []
    temp_value = 0 if aggregation in ['sum', 'max'] else []
    count = 0 if aggregation == 'average' else None
    if len(hourly_array) == 8760:
        timestep_list = [744, 1416, 2160, 2880, 3624, 4344, 5088, 5832, 6552, 7296, 8016, 8759]
    else:
        timestep_list = [744, 1416, 2160, 2880, 3624, 4344, 5088, 5832, 6552, 7296, 8016, 8735]
    for index, value in enumerate(hourly_array):
        if np.isnan(value):
            value = 0
        if aggregation == 'sum':
            temp_value += value
        elif aggregation == 'average':
            temp_value.append(value)
            count += 1
        elif aggregation == 'max' and value > temp_value:
            temp_value = value
        if index in timestep_list:
            if aggregation == 'average':
                if count != 0:
                    result_array.append(sum(temp_value) / count)
                else:
                    result_array.append(0)
                temp_value = []
                count = 0
            else:
                result_array.append(temp_value)
                temp_value = 0 if aggregation in ['sum', 'max'] else []
    return result_array
 

def linear_interpolation(x, x1, x2, y1, y2):
    y = y1 + (x - x1) * (y2 - y1) / (x2 - x1)
    return y

def linear_regression(x, y):
    x = x.reshape((-1, 1))
    model = LinearRegression()
    model.fit(x, y)
    model = LinearRegression().fit(x, y)
    r_sq = model.score(x, y)
    y_pred = model.predict(x)
    y_pred = model.intercept_ + np.sum(model.coef_ * x, axis=1)
    linear_y = model.predict(x)
    slope = (linear_y[-1]-linear_y[0])/(x[-1]-x[0])
    intersect = linear_y[-1]-slope*x[-1]
    return slope, intersect

def get_secret(filename):
    with open(filename) as file:
        secret = file.readline()
    return secret

def update_df(df: pd.DataFrame, new_df: pd.DataFrame) -> pd.DataFrame:
    cols_to_update = new_df.columns.intersection(df.columns)
    cols_to_add = new_df.columns.difference(df.columns)
    df[cols_to_update] = new_df[cols_to_update]
    return pd.concat([df, new_df[cols_to_add]], axis=1)

def coverage_calculation(percentage, array):
    if percentage == 100:
        return array
    elif percentage == 0 or np.sum(array) == 0:
        return np.zeros(8760)
    array_sorted = np.sort(array)
    timeserie_sum = np.sum(array)
    timeserie_N = len(array)
    startpunkt = timeserie_N // 2
    i = 0
    avvik = 0.0001
    pm = 2 + avvik
    while abs(pm - 1) > avvik:
        cutoff = array_sorted[startpunkt]
        array_tmp = np.where(array > cutoff, cutoff, array)
        beregnet_dekningsgrad = (np.sum(array_tmp) / timeserie_sum) * 100
        pm = beregnet_dekningsgrad / percentage
        gammelt_startpunkt = startpunkt
        if pm < 1:
            startpunkt = startpunkt + timeserie_N // 2 ** (i + 2) - 1
        else:
            startpunkt = startpunkt - timeserie_N // 2 ** (i + 2) - 1
        if startpunkt == gammelt_startpunkt:
            break
        i += 1
        if i > 13:
            break
    return array_tmp

def calculate_flow_temperature(outdoor_temperature_array, outdoor_temperature_min = -15, outdoor_temperature_max = 15, flow_temperature_min = 35, flow_temperature_max = 45):
    flow_temperature = np.zeros(8760)
    for i in range(0, len(flow_temperature)):
        if outdoor_temperature_array[i] < outdoor_temperature_min:
            flow_temperature[i] = flow_temperature_max
        elif outdoor_temperature_array[i] > outdoor_temperature_max:
            flow_temperature[i] = flow_temperature_min
        else:
            flow_temperature[i] = linear_interpolation(outdoor_temperature_array[i], outdoor_temperature_min, outdoor_temperature_max, flow_temperature_max, flow_temperature_min)
    return flow_temperature

def hex_to_rgba(hex_color):
    hex_color = hex_color.lstrip('#')
    
    if len(hex_color) == 6:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
    elif len(hex_color) == 3:
        r = int(hex_color[0]*2, 16)
        g = int(hex_color[1]*2, 16)
        b = int(hex_color[2]*2, 16)
    else:
        raise ValueError("Invalid hex color format")

    return pd.Series([r, g, b], index=['r', 'g', 'b'])