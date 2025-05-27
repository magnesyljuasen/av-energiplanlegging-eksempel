import numpy as np
import pandas as pd
from .data_classes import Building, Address, BuildingData, Results
from pvgispy import Hourly
import streamlit as st 


class SolarPanels:
    def __init__(self):
        self.set_simple_sizing_conditions()

    def set_simple_sizing_conditions(self):
        self.df_solar_sheet = pd.read_excel('src/data/solar_sheet.xlsx')
        self.SOLARPANEL_BUILDINGS = {
            'Hus' : 'Småhus', 
            'Leilighet' : 'Boligblokk',
            'Kontor' : 'Næringsbygg_mindre',
            'Butikk' : 'Næringsbygg_større',
            'Hotell' : 'Småhus', 
            'Barnehage' : 'Boligblokk',
            'Skole' : 'Næringsbygg_mindre',
            'Universitet' : 'Næringsbygg_mindre',
            'Kultur' : 'Næringsbygg_større',
            'Sykehjem' : 'Småhus', 
            'Sykehus' : 'Boligblokk',
            'Andre' : 'Næringsbygg_mindre',
        }

        self.ROOF_COSTS = {
            'Skråtak takstein' : 0.4,
            'Skråtak metallplater' : -0.6,
            'Skråtak asfalt' : 0,
            'Flatt tak øst/vest' : -0.6,
            'Flatt sør' : 0.4,
            'Fasade over offentlig område' : 7,
            'Fasade over sperret område' : 3.4
            }
        
        self.ROOF_MAP = {
            "Hus": ["Skråtak takstein"],
            "Leilighet": ["Skråtak takstein", "Flatt tak øst/vest"],
            "Kontor": ["Flatt tak øst/vest"],
            "Butikk": ["Flatt tak øst/vest"],
            "Hotell": ["Flatt tak øst/vest"],
            "Barnehage": ["Skråtak takstein", "Flatt tak øst/vest"],
            "Skole": ["Flatt tak øst/vest"],
            "Universitet": ["Flatt tak øst/vest"],
            "Kultur": ["Flatt tak øst/vest"],
            "Sykehjem": ["Skråtak takstein", "Flatt tak øst/vest"],
            "Sykehus": ["Skråtak takstein", "Flatt tak øst/vest"],
            "Andre": ["Flatt tak øst/vest"]
        }

        building_roof_costs = {building: [self.ROOF_COSTS[roof] for roof in roofs if roof in self.ROOF_COSTS] for building, roofs in self.ROOF_MAP.items()}
        self.ROOF_COSTS = {building: sum(costs) / len(costs) for building, costs in building_roof_costs.items()}
    
    def simple_sizing(self, building):
        """Enkel beregning som beregner solceller. """
        if len(building.data.type) > 1:
            solar_type = 'Næringsbygg_større'
        else:
            solar_type = self.SOLARPANEL_BUILDINGS[building.data.type[0]]
        solar_production = np.array(self.df_solar_sheet[solar_type])
        building.results.energy.solar_production = solar_production * building.data.floor_area

    def preprocess_solar_production(self, building, year=2016, kwp=1, kwp_m2=0.22, loss_inp=20, slopes=[25, 25, 25, 25, 10, 10], angles=[-90, 0, 90, 180, 90, -90]):    
        slopes, angles = np.array(slopes), np.array(angles)
        kwh_kwp = np.zeros(len(slopes))
        p_list = []
        for i in range(len(slopes)):
            hourly = Hourly(
                lat=building.address.lat, 
                lon=building.address.long, 
                raddatabase='PVGIS-ERA5',
                pvcalculation=True,
                loss=loss_inp, 
                peakpower=kwp,
                pvtech="crystSi",
                angle=slopes[i], 
                aspect=angles[i], 
                startyear=year, 
                endyear=year
                )
            hourly_data = hourly.hourly()[0:8760] 
            p = np.zeros(8760)
            for j in range(len(hourly_data)):
                p[j] = hourly_data[j]['P']
            kwh_kwp[i] = int(np.sum(p)/1000)
            p = p / np.sum(p)
            p_list.append(p)

        df = pd.DataFrame()
        df.index = ['Småhus', 'Boligblokk', 'Næringsbygg_mindre', 'Næringsbygg_større']
        df['Taktype'] = ['100% skrått', '50% skrått / 50% flatt', '100% flatt', '100% flatt']
        df['Helling'] = [25, 12.5, 10, 10]
        df['Orientering'] = ['Blanding av sør, vest og øst', '', '90 / -90', '90 / -90']
        df['Tilgjenglig andel tak (bortfall av takflater (skrått))'] = [0.75, 0.88, 1, 1]
        df['Bortfall på grunn av ting'] = [0.3, 0.275, 0.25, 0.10]
        df['Andel av takareal som er tilgjengelig'] = df['Tilgjenglig andel tak (bortfall av takflater (skrått))'] * (1 - df['Bortfall på grunn av ting'])
        df['Faktor for bebygd areal til takareal'] = 1/np.cos(np.radians(df['Helling']))
        df['Total faktor for bebygd areal'] = df['Andel av takareal som er tilgjengelig'] * df['Faktor for bebygd areal til takareal']
        df['kWp/m2'] = [kwp_m2, kwp_m2, kwp_m2, kwp_m2]
        df['kWh/kWp'] = [np.mean(kwh_kwp[0:2]), np.mean([np.mean(kwh_kwp[0:2]), np.mean(kwh_kwp[4:5])]), np.mean(kwh_kwp[4:5]), np.mean(kwh_kwp[4:5])]
        df['kWh/m2'] = df['kWp/m2'] * df['kWh/kWp']
        df['kWh/tilgjengelig m2'] = df['Total faktor for bebygd areal'] * df['kWh/m2']
        df['Produksjon'] = [(p_list[0] + p_list[1] + p_list[2]) / 3, (p_list[0] + p_list[1] + p_list[2] + p_list[4] + p_list[5]) / 5, (p_list[4] + p_list[5]) / 2, (p_list[4] + p_list[5]) / 2]
        df['Produksjon'] = df['Produksjon'] * df['kWh/tilgjengelig m2']
        self.df_solar = df

    def advanced_sizing(self, building, kWp_limit = 0):
        """Avansert beregning som beregner solceller inkl. kostnader. """
        if len(building.data.type) > 1:
            solar_type = 'Næringsbygg_større'
        else:
            solar_type = self.SOLARPANEL_BUILDINGS[building.data.type[0]]
        self.df_solar_building = self.df_solar.loc[solar_type]
        if isinstance(building.data.floor_area, list):
            floor_area = building.data.floor_area[0]
        else:
            floor_area = building.data.floor_area

        self.df_solar_building['kWp'] = int(self.df_solar_building['Total faktor for bebygd areal'] * self.df_solar_building['kWp/m2'] * floor_area)
        
        ## ENDRE til riktig kWp
        self.kWp = self.df_solar_building['kWp']
        self.specific_price = 20.323 * (self.kWp)**(-0.149) + self.ROOF_COSTS[building.data.type[0]]
        investment_cost = int(self.specific_price * self.kWp * 1000)
        
        if self.kWp >= kWp_limit:
            building.results.energy.solar_production = self.df_solar_building.loc['Produksjon'] * building.data.floor_area
            building.results.investment.solar_panels = self.kWp
            building.results.investment_cost.solar_panels = investment_cost
            building.results.reinvestment_cost.solar_panels = int(investment_cost * 0.1)
            building.results.investment_lifetime.solar_panels = 15

        
