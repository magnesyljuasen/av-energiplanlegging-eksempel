import numpy as np
import pandas as pd
import streamlit as st 
from .utilities import coverage_calculation, linear_interpolation, linear_regression

class EnergyEfficiency:
    def __init__(self):
        self.set_simple_sizing_conditions()

    def set_simple_sizing_conditions(self):
        self.df_house = pd.read_excel('src/data/energieffektivisering.xlsx', sheet_name='Bolig')
        self.df_other = pd.read_excel('src/data/energieffektivisering.xlsx', sheet_name='Andre')

        self.MEASURES = [
            "Insulation of walls",
            "Insulation of roof",
            "Insulation of floor",
            "New windows and doors",
            "Red. indoor temp. nights/weekends",
            "Heat recovery in ventilation",
            "Energy Monitoring System",
            "Energy efficient lighting",
            "Improved specific fan power (SFP)",
            "Energy management system",
            "Demand controlled ventilation",
            "System for lightning control",
            "Tiltakspakke 1 - Bygningskropp",
            "Tiltakspakke 2 - Smartstyring",
            "Tiltakspakke 3 - Ventilasjon"
        ]
    
    def simple_sizing(self, building, selected_measure, spot_area, building_year = 1970):
        building_type = building.data.type[0]

        if (building_type == 'Hus') or (building_type == 'Leilighet'):
            df = self.df_house
        else:
            df = self.df_other

        df['TEK'] = df['TEK'].astype(int)
        
        if building_year <= 1968:
            target_year = 1968
        elif building_year >= 1968 and building_year <= 1986:
            target_year = 1986
        elif building_year >= 1987 and building_year <= 1996:
            target_year = 1996
        elif building_year >= 1997 and building_year <= 2006:
            target_year = 2006
        else:
            target_year = 0
        
        df = df[df['TEK'] == target_year]
        df = df[df['Measure'] == selected_measure].reset_index(drop=True)
        
        building.results.energy.spaceheating_reduction = np.zeros(8760)
        building.results.energy.dhw_reduction = np.zeros(8760)
        building.results.energy.elspecific_reduction = np.zeros(8760)
        for index, row in df.iterrows():
            end_use = row['End-use']
            percentage = row[f'{spot_area}_{building_type}']
            if percentage != 0:
                if end_use == 'Romoppvarming':
                    building.results.energy.spaceheating_reduction = np.copy(building.results.energy.spaceheating*(percentage))
                elif end_use == 'Tappevann':
                    building.results.energy.dhw_reduction = np.copy(building.results.energy.dhw*(percentage))
                elif end_use == 'Elspesifikt':
                    building.results.energy.elspecific_reduction = np.copy(building.results.energy.elspecific*(percentage))
                elif end_use == 'Alle':
                    building.results.energy.spaceheating_reduction = np.copy(building.results.energy.spaceheating*(percentage))
                    building.results.energy.dhw_reduction = np.copy(building.results.energy.dhw*(percentage))
                    building.results.energy.elspecific_reduction = np.copy(building.results.energy.elspecific*(percentage))
        
        building.results.energy.spaceheating = building.results.energy.spaceheating - building.results.energy.spaceheating_reduction
        building.results.energy.dhw = building.results.energy.dhw - building.results.energy.dhw_reduction
        building.results.energy.elspecific = building.results.energy.elspecific - building.results.energy.elspecific_reduction
        