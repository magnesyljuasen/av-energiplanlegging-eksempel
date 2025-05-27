import numpy as np
import math
import pandas as pd
import pygfunction as gt
from GHEtool import Borefield, GroundConstantTemperature, HourlyGeothermalLoad
from .utilities import coverage_calculation, calculate_flow_temperature


class GeoEnergy:
    def __init__(self):
        self.set_simple_sizing_conditions()
        self.set_advanced_sizing_conditions()

    def set_simple_sizing_conditions(self):
        self.kwh_per_meter = 80
    
    def simple_sizing(self, building, spaceheating_coverage = 90, spaceheating_cop = 3.5, dhw_coverage = 80, dhw_cop = 2.5, kWh_limit = 0):
        """Enkel beregning som bruker dekningsgrader på hhv. 
        romoppvarming og varmtvann samt flate COPer for å 
        returnere seriene som leveres fra bergvarmeanlegget. """

        spaceheating = coverage_calculation(spaceheating_coverage, building.results.energy.spaceheating)
        dhw = coverage_calculation(dhw_coverage, building.results.energy.dhw)
        spaceheating_compressor = spaceheating/spaceheating_cop
        spaceheating_extracted_from_wells = spaceheating - spaceheating_compressor
        spaceheating_peak = building.results.energy.spaceheating - spaceheating
        dhw_compressor = dhw/dhw_cop
        dhw_extracted_from_wells = dhw - dhw_compressor
        dhw_peak = building.results.energy.dhw - dhw
        compressor = spaceheating_compressor + dhw_compressor
        extracted_from_wells = spaceheating_extracted_from_wells + dhw_extracted_from_wells
        peak = spaceheating_peak + dhw_peak

        borehole_meters = round(extracted_from_wells.sum() / self.kwh_per_meter)
        heatpump_size = round((extracted_from_wells + compressor).max(),1)

        if np.sum(spaceheating + dhw) >= kWh_limit:
            building.results.energy.geoenergy_compressor = compressor
            building.results.energy.geoenergy_extracted_from_wells = extracted_from_wells
            building.results.energy.geoenergy_peak = peak
            building.results.energy.geoenergy_electricity = compressor + peak      
            
            building.results.investment.geoenergy_borehole_meters = int(borehole_meters)
            building.results.investment.geoenergy_heat_pump_size = int(heatpump_size)
            building.results.investment_cost.geoenergy_heat_pump_size = int(214000 + heatpump_size * 2200)
            building.results.investment_cost.geoenergy_borehole_meters = int(20000 + borehole_meters * 437.5)
            building.results.reinvestment_cost.geoenergy_heat_pump_size = int((214000 + heatpump_size * 2200) * 0.6)
            building.results.reinvestment_cost.geoenergy_borehole_meters = int((20000 + borehole_meters * 437.5) * 0)
            building.results.investment_lifetime.geoenergy_heat_pump_size = 20
            building.results.investment_lifetime.geoenergy_borehole_meters = 60
        
        return compressor, extracted_from_wells, peak, borehole_meters, heatpump_size
    
    def set_intermediate_sizing_conditions(self, simulation_period=25, thermal_conductivity=3.5, undisturbed_temperature=8, volumetric_heat_capacity=2.6e6, borehole_thermal_resistance=0.12, allowed_fluid_temperatures=[0,16], fluid_density=968.4, fluid_specific_heat=4.3, flow_rate=0.6):
        self.simulation_period = simulation_period                     # years
        self.thermal_conductivity = thermal_conductivity                 # W/(mK)
        self.undisturbed_temperature = undisturbed_temperature              # C
        self.volumetric_heat_capacity = volumetric_heat_capacity           # J/(m3K)
        self.borehole_thermal_resistance = borehole_thermal_resistance         # (mK)/W
        self.max_allowed_fluid_temperature = allowed_fluid_temperatures[1]         # C
        self.min_allowed_fluid_temperature = allowed_fluid_temperatures[0]         # C
    
        self.field = gt.boreholes.rectangle_field(
            N_1=1,                                      # stk (Number of boreholes x)
            N_2=2,                                      # stk (Number of boreholes y)
            B_1=15,                                     # m (distance between boreholes)
            B_2=15,                                     # m (distance between boreholes)
            H=200,                      # m
            D=10,                                       # m (Borehole buried depth)
            r_b=0.114/2,                                # m (Borehole radius)
            tilt=0                                      # deg (Tilt)
            )
        self.fluid_density = fluid_density                      # kg/m3
        self.fluid_specific_heat = fluid_specific_heat                  # kJ/(kgK)
        self.flow_rate = flow_rate                            # l/s
    
    def intermediate_sizing(self, building, spaceheating_coverage = 90, spaceheating_cop = 3.5, dhw_coverage = 80, dhw_cop = 2.5):
        spaceheating = coverage_calculation(spaceheating_coverage, building.results.energy.spaceheating)
        dhw = coverage_calculation(dhw_coverage, building.results.energy.dhw)
        spaceheating_compressor = spaceheating/spaceheating_cop
        spaceheating_extracted_from_wells = spaceheating - spaceheating_compressor
        spaceheating_peak = building.results.energy.spaceheating - spaceheating
        dhw_compressor = dhw/dhw_cop
        dhw_extracted_from_wells = dhw - dhw_compressor
        dhw_peak = building.results.energy.dhw - dhw
        compressor = spaceheating_compressor + dhw_compressor
        extracted_from_wells = spaceheating_extracted_from_wells + dhw_extracted_from_wells
        peak = spaceheating_peak + dhw_peak
        building.results.energy.geoenergy_compressor = compressor
        building.results.energy.geoenergy_extracted_from_wells = extracted_from_wells
        building.results.energy.geoenergy_peak = peak
        building.results.energy.geoenergy_electricity = compressor + peak

        borefield = Borefield()

        load = HourlyGeothermalLoad(heating_load=building.results.energy.geoenergy_extracted_from_wells, cooling_load=building.results.energy.cooling, simulation_period=self.simulation_period)
        borefield.set_load(load=load)
        
        ground_data = GroundConstantTemperature(k_s=self.thermal_conductivity, T_g=self.undisturbed_temperature, volumetric_heat_capacity=self.volumetric_heat_capacity)
        borefield.set_ground_parameters(data=ground_data)
        borefield.set_Rb(Rb=self.borehole_thermal_resistance)
        borefield.calculation_setup(use_constant_Rb=True)
        borefield.set_max_avg_fluid_temperature(self.max_allowed_fluid_temperature) 
        borefield.set_min_avg_fluid_temperature(self.min_allowed_fluid_temperature)

        borefield.set_borefield(borefield = self.field)
        
        borefield.calculate_temperatures(hourly=True)
        
        load = np.array(list(building.results.energy.geoenergy_extracted_from_wells)*25)
        deltaT = ((load) / (self.fluid_density*self.flow_rate*self.fluid_specific_heat)) * 1000

        heatpump_size = np.max(compressor+extracted_from_wells)/1.25

        borehole_meters = len(borefield.borefield)*borefield.H

        building.results.investment.geoenergy_borehole_meters = int(borehole_meters)
        building.results.investment.geoenergy_heat_pump_size = int(heatpump_size)
        building.results.investment_cost.geoenergy_heat_pump_size = int(214000 + heatpump_size * 2200)
        building.results.investment_cost.geoenergy_borehole_meters = int(20000 + borehole_meters * 437.5)
        building.results.reinvestment_cost.geoenergy_heat_pump_size = int((214000 + heatpump_size * 2200) * 0.6)
        building.results.reinvestment_cost.geoenergy_borehole_meters = int((20000 + borehole_meters * 437.5) * 0)
        building.results.investment_lifetime.geoenergy_heat_pump_size = 20
        building.results.investment_lifetime.geoenergy_borehole_meters = 60

        self.borehole_temperature = borefield.results.peak_heating
        self.borehole_wall_temperature = borefield.results.Tb
        self.borehole_temperature_to_HP = self.borehole_temperature + deltaT/2
        self.borehole_temperature_from_HP = self.borehole_temperature - deltaT/2
        
    def set_advanced_sizing_conditions(self):
        self.simulation_period = 25                     # years
        self.thermal_conductivity = 3.5                 # W/(mK)
        self.undisturbed_temperature = 8.0              # C
        self.volumetric_heat_capacity = 2.6e6           # J/(m3K)
        self.borehole_thermal_resistance = 0.12         # (mK)/W
        self.max_allowed_fluid_temperature = 16         # C
        self.min_allowed_fluid_temperature = 0          # C
    
        self.borehole_depth = 200                       # m
        self.field = gt.boreholes.rectangle_field(
            N_1=1,                                      # stk (Number of boreholes x)
            N_2=1 ,                                      # stk (Number of boreholes y)
            B_1=15,                                     # m (distance between boreholes)
            B_2=15,                                     # m (distance between boreholes)
            H=self.borehole_depth,                      # m
            D=10,                                       # m (Borehole buried depth)
            r_b=0.114/2,                                # m (Borehole radius)
            tilt=0                                      # deg (Tilt)
            )
        
        self.fluid_density = 968.4                      # kg/m3
        self.fluid_specific_heat = 4.3                  # kJ/(kgK)
        self.flow_rate = 0.6                            # l/s
        self.df_heatpump_sheet = pd.read_excel('src/data/heatpump_sheet.xlsx')

    def _interpolate_datasheet(self, df, target_power, target_temperature):
        df_sorted = df.sort_values(by='Power')
        
        lower_idx = df_sorted['Power'].searchsorted(target_power) - 1
        higher_idx = lower_idx + 1

        lower_power = df_sorted.iloc[lower_idx]
        higher_power = df_sorted.iloc[higher_idx]

        F = (target_power - lower_power['Power']) / (higher_power['Power'] - lower_power['Power']) # interpolation factor

        interpolated_temperature = {}
        for column in df.columns[2:]: # interpolate temperature for each outlet hot water temperature
            if higher_power[column] == 0:
                interpolated_value = 0
            else:
                interpolated_value = lower_power[column] + F * (higher_power[column] - lower_power[column])
            interpolated_temperature[column] = interpolated_value
        
        df = pd.DataFrame(list(interpolated_temperature.items()), columns=['Outlet temperature', 'COP'])
        lower_idx = df['Outlet temperature'].searchsorted(target_temperature) - 1
        higher_idx = lower_idx + 1
        
        if higher_idx == len(df):
            higher_idx = lower_idx

        lower_power = df.iloc[lower_idx]
        higher_power = df.iloc[higher_idx]
        
        if higher_power['COP'] == 0:
            cop = 0
        elif lower_power['COP'] == 0:
            cop = higher_power['COP']
        else:
            slope = (higher_power['COP'] - lower_power['COP']) / (higher_power['Outlet temperature'] - lower_power['Outlet temperature'])
            cop = slope * (target_temperature - lower_power['Outlet temperature']) + lower_power['COP']
        
        return cop
    
    def get_cop(self, desired_power, target_temperature, source_temperature):
        df = self.df_heatpump_sheet
        source_temperatures = [-5, -2, 0, 2, 5, 10, 15, 20, 25, 27]
        lower_power, higher_power = None, None
        for temp in source_temperatures:
            if temp <= source_temperature:
                lower_power = temp
            elif temp >= source_temperature:
                higher_power = temp
                break

        if lower_power == None:
            df_0 = df[df['Inlet heat source temp'] == higher_power]
            cop = self._interpolate_datasheet(df=df_0, target_power=desired_power, target_temperature=target_temperature)
        elif higher_power == None:
            df_0 = df[df['Inlet heat source temp'] == lower_power]
            cop = self._interpolate_datasheet(df=df_0, target_power=desired_power, target_temperature=target_temperature)
        else:
            df_1 = df[df['Inlet heat source temp'] == lower_power]
            cop_1 = self._interpolate_datasheet(df=df_1, target_power=desired_power, target_temperature=target_temperature)

            df_2 = df[df['Inlet heat source temp'] == higher_power]
            cop_2 = self._interpolate_datasheet(df=df_2, target_power=desired_power, target_temperature=target_temperature)

            slope = (cop_2 - cop_1) / (higher_power - lower_power)
            cop = slope * (source_temperature - lower_power) + cop_1
        
        if cop < 1:
            cop = 1
            
        return cop

    def advanced_sizing(self, building):
        def _borefield_sizing(load_array, borefield):
            # function that calculates the temperature of the load and borefield - could be wrapped in a for loop for optimizing the borefield
            load = HourlyGeothermalLoad(heating_load=load_array, simulation_period=self.simulation_period)
            borefield.set_load(load=load)
            borefield.calculate_temperatures(hourly=True)
            borehole_temperature = borefield.results.peak_heating
            return borehole_temperature

        def _heatpump_technical_sheet(source_temperature, demand, flow_temperature, heatpump_size):
            if demand > heatpump_size:
                power_percentage = 1
            else:
                power_percentage = demand/heatpump_size
            COP = 1
            while COP == 1:
                COP = self.get_cop(desired_power=power_percentage, target_temperature=flow_temperature, source_temperature=source_temperature)
                if COP == 1:
                    power_percentage = power_percentage - 0.1

            P = power_percentage * heatpump_size
            return COP, P

        spaceheating_array = building.results.energy.spaceheating
        dhw_array = building.results.energy.dhw
        dhw_heatpump = dhw_array.max() * 1
        spaceheating_heatpump = spaceheating_array.max() * 1
        borehole_temperature = np.zeros(8760 * self.simulation_period)
        dhw_flow_temperature = calculate_flow_temperature(building.data.outdoor_temperature, flow_temperature_max=50, flow_temperature_min=40)
        spaceheating_flow_temperature = calculate_flow_temperature(building.data.outdoor_temperature, flow_temperature_max=55, flow_temperature_min=45)

        compressor_array, load_array, peak_array = np.zeros(8760), np.zeros(8760), np.zeros(8760)

        borefield = Borefield()
        ground_data = GroundConstantTemperature(k_s=self.thermal_conductivity, T_g=self.undisturbed_temperature, volumetric_heat_capacity=self.volumetric_heat_capacity)
        borefield.set_ground_parameters(data=ground_data)
        borefield.set_Rb(Rb=self.borehole_thermal_resistance)
        borefield.calculation_setup(use_constant_Rb=True)
        borefield.set_max_avg_fluid_temperature(self.max_allowed_fluid_temperature) 
        borefield.set_min_avg_fluid_temperature(self.min_allowed_fluid_temperature)
        borefield.set_borefield(borefield=self.field)

        YEAR = int(self.simulation_period/2)
        for i in range(0, 2):
            for j in range(0, 8760):
                dhw_COP, dhw_P = _heatpump_technical_sheet(borehole_temperature[(8760*YEAR) + j], dhw_array[j], dhw_flow_temperature[j], heatpump_size=dhw_heatpump)
                spaceheating_COP, spaceheating_P = _heatpump_technical_sheet(borehole_temperature[(8760*YEAR) + j], spaceheating_array[j], spaceheating_flow_temperature[j], heatpump_size=spaceheating_heatpump)

                compressor = dhw_P/dhw_COP + spaceheating_P/spaceheating_COP
                load = (dhw_P - dhw_P/dhw_COP) + (spaceheating_P - spaceheating_P/spaceheating_COP)
                peak = spaceheating_array[j] + dhw_array[j] - compressor - load

                compressor_array[j] = compressor
                load_array[j] = load
                peak_array[j] = peak

            borehole_temperature = _borefield_sizing(load_array, borefield)
        
        building.results.energy.geoenergy_compressor = compressor_array
        building.results.energy.geoenergy_extracted_from_wells = load_array
        building.results.energy.geoenergy_peak = peak_array
        building.results.energy.geoenergy_electricity = compressor_array + peak_array
        #--
        heatpump_size = round(spaceheating_heatpump + dhw_heatpump,1)
        borehole_meters = borefield.number_of_boreholes * borefield.H
        building.results.investment.geoenergy_borehole_meters = round(borehole_meters)
        building.results.investment.geoenergy_heatpump_size = heatpump_size
        building.results.investment_cost.geoenergy_heat_pump_size = int(214000 + heatpump_size * 2200)
        building.results.investment_cost.geoenergy_borehole_meters = int(20000 + borehole_meters * 437.5)
        building.results.reinvestment_cost.geoenergy_heat_pump_size = int((214000 + heatpump_size * 2200) * 0.6)
        building.results.reinvestment_cost.geoenergy_borehole_meters = int((20000 + borehole_meters * 437.5) * 0)
        building.results.investment_lifetime.geoenergy_heat_pump_size = 20
        building.results.investment_lifetime.geoenergy_borehole_meters = 60

        load = np.array(list(building.results.energy.geoenergy_extracted_from_wells)*25)
        deltaT = ((load) / (self.fluid_density*self.flow_rate*self.fluid_specific_heat)) * 1000
        self.borehole_temperature = borehole_temperature
        self.borehole_wall_temperature = borefield.results.Tb
        self.borehole_temperature_to_HP = self.borehole_temperature + deltaT/2
        self.borehole_temperature_from_HP = self.borehole_temperature - deltaT/2



code = """
def read_datasheet():
    df = pd.read_excel('src/data/heatpump_sheet.xlsx')
    return df

def _interpolate_datasheet(df, target_power, target_temperature):
    df_sorted = df.sort_values(by='Power')
    
    lower_idx = df_sorted['Power'].searchsorted(target_power) - 1
    higher_idx = lower_idx + 1

    lower_power = df_sorted.iloc[lower_idx]
    higher_power = df_sorted.iloc[higher_idx]

    F = (target_power - lower_power['Power']) / (higher_power['Power'] - lower_power['Power']) # interpolation factor

    interpolated_temperature = {}
    for column in df.columns[2:]: # interpolate temperature for each outlet hot water temperature
        if higher_power[column] == 0:
            interpolated_value = 0
        else:
            interpolated_value = lower_power[column] + F * (higher_power[column] - lower_power[column])
        interpolated_temperature[column] = interpolated_value
    
    df = pd.DataFrame(list(interpolated_temperature.items()), columns=['Outlet temperature', 'COP'])
    lower_idx = df['Outlet temperature'].searchsorted(target_temperature) - 1
    higher_idx = lower_idx + 1
    
    if higher_idx == len(df):
        higher_idx = lower_idx

    lower_power = df.iloc[lower_idx]
    higher_power = df.iloc[higher_idx]
    
    if higher_power['COP'] == 0:
        cop = 0
    elif lower_power['COP'] == 0:
        cop = higher_power['COP']
    else:
        slope = (higher_power['COP'] - lower_power['COP']) / (higher_power['Outlet temperature'] - lower_power['Outlet temperature'])
        cop = slope * (target_temperature - lower_power['Outlet temperature']) + lower_power['COP']
    
    return cop

def get_cop(df, desired_power, target_temperature, source_temperature):
    source_temperatures = [-5, -2, 0, 2, 5, 10, 15, 20, 25, 27]
    lower_power, higher_power = None, None
    for temp in source_temperatures:
        if temp <= source_temperature:
            lower_power = temp
        elif temp >= source_temperature:
            higher_power = temp
            break

    if lower_power == None:
        df_0 = df[df['Inlet heat source temp'] == higher_power]
        cop = _interpolate_datasheet(df=df_0, target_power=desired_power, target_temperature=target_temperature)
    elif higher_power == None:
        df_0 = df[df['Inlet heat source temp'] == lower_power]
        cop = _interpolate_datasheet(df=df_0, target_power=desired_power, target_temperature=target_temperature)
    else:
        df_1 = df[df['Inlet heat source temp'] == lower_power]
        cop_1 = _interpolate_datasheet(df=df_1, target_power=desired_power, target_temperature=target_temperature)

        df_2 = df[df['Inlet heat source temp'] == higher_power]
        cop_2 = _interpolate_datasheet(df=df_2, target_power=desired_power, target_temperature=target_temperature)

        slope = (cop_2 - cop_1) / (higher_power - lower_power)
        cop = slope * (source_temperature - lower_power) + cop_1
    
    if cop < 1:
        cop = 1
        
    return cop

    
df = read_datasheet()
st.dataframe(df, height=200)
st.markdown("---")
P_NOMINAL = 100
desired_power = st.number_input('Effekt', value=0.8)
target_temperature = st.number_input('target temp', value=42)
source_temperature = st.number_input('Brønntemperatur', value = -5.00)

cop = get_cop(df = df, desired_power=desired_power, target_temperature=target_temperature, source_temperature=source_temperature)
st.write(f'Power : {round(P_NOMINAL * desired_power)} kW | COP: {round(cop,2)}')




















def plot(df, power, inlet_temperature = -5):
    df = df[df['Inlet heat source temp'] == inlet_temperature]

    interpolated_temperature = _interpolate_datasheet(power, df)
    st.write(interpolated_temperature)

    temps = list(interpolated_temperature.keys())
    values = list(interpolated_temperature.values())
    # Plot the interpolated temperature values
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=temps, y=values, mode='lines+markers', name='Interpolated Temperature'))
    fig.update_layout(
        title=f'Temperatur {inlet_temperature} grader',
        xaxis_title='Outlet hot water temp',
        yaxis_title='COP',
        yaxis_range=[0,9],
        height=400)
    st.plotly_chart(fig, use_container_width=True)


#c1, c2 = st.columns(2)
#with c1:
#    plot(df, power=desired_power, inlet_temperature=-5)
#    plot(df, power=desired_power, inlet_temperature=-2)
#    plot(df, power=desired_power, inlet_temperature=0)
#    plot(df, power=desired_power, inlet_temperature=2)
#    plot(df, power=desired_power, inlet_temperature=5)
#with c2:
#    plot(df, power=desired_power, inlet_temperature=10)
#    plot(df, power=desired_power, inlet_temperature=15)
#    plot(df, power=desired_power, inlet_temperature=20)
#    plot(df, power=desired_power, inlet_temperature=25)
#    plot(df, power=desired_power, inlet_temperature=27)




"""