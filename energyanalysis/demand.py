import numpy as np
import pandas as pd
import streamlit as st

from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient
from .utilities import get_secret, update_df


class Demand:
    BUILDING_STANDARDS = {
        "Lite energieffektiv": "Reg", 
        "Middels energieffektiv": "Eff-E", 
        "Veldig energieffektiv": "Vef"
        }
    BUILDING_TYPES = {
        "Hus": "Hou",
        "Leilighet": "Apt",
        "Kontor": "Off",
        "Butikk": "Shp",
        "Hotell": "Htl",
        "Barnehage": "Kdg",
        "Skole": "Sch",
        "Universitet": "Uni",
        "Kultur": "CuS",
        "Sykehjem": "Nsh",
        "Sykehus": "Other",
        "Andre": "Other"
        }
    PROFET_FILEPATH = 'src/data/profet_data.csv'
    
    def __init__(self):
        self.COOLING_PER_SQUARE_METER = {
            "Hus": 15,
            "Leilighet": 20,
            "Kontor": 13,
            "Butikk": 10,
            "Hotell": 20,
            "Barnehage": 10,
            "Skole": 30,
            "Universitet": 10,
            "Kultur": 10,
            "Sykehjem": 20,
            "Sykehus": 30,
            "Andre": 20
            }

    def cooling_calculation(self, building, cooling_target_sum = None):
        """Beregning som estimerer 
        kjølebehovet basert på building."""
        
        cooling = 0
        for i in range(0, len(building.data.standard)):
            building_standard = building.data.standard[i]
            building_type = building.data.type[i]
            building_area = building.data.area[i]

            calculated_cooling = self.COOLING_PER_SQUARE_METER[building_type] * building_area

            cooling = cooling + calculated_cooling
            #TODO: convert this to a numpy array 
        
        if cooling_target_sum != None:
            cooling_factor = cooling_target_sum/np.sum(cooling)
            cooling = cooling * cooling_factor
            
        building.results.energy.cooling = np.array(cooling)
        return cooling

    def profet_api(self, building, spaceheating_target_sum = None, dhw_target_sum = None, electric_target_sum = None):
        """Beregning som estimerer romoppvarming, 
        tappevann og elspesifikt behov basert på 
        building med et kall til PROFet API'et."""

        spaceheating, dhw, elspecific = np.zeros(8760), np.zeros(8760), np.zeros(8760)
        for i in range(0, len(building.data.standard)):
            building_standard = building.data.standard[i]
            building_type = building.data.type[i]
            building_area = building.data.area[i]
            if building_area != 0:
                oauth = OAuth2Session(client=BackendApplicationClient(client_id="profet_2024"))
                predict = OAuth2Session(token=oauth.fetch_token(token_url="https://identity.byggforsk.no/connect/token", client_id="profet_2024", client_secret=get_secret("src/config/profet_secret.txt")))
                selected_standard = self.BUILDING_STANDARDS[building_standard]
                if selected_standard == "Reg":
                    regular_area, efficient_area, veryefficient_area = building_area, 0, 0
                if selected_standard == "Eff-E":
                    regular_area, efficient_area, veryefficient_area = 0, building_area, 0
                if selected_standard == "Vef":
                    regular_area, efficient_area, veryefficient_area = 0, 0, building_area
                # --
                if isinstance(building.data.outdoor_temperature, list):
                    temperature_request_data = {"Tout": building.data.outdoor_temperature}
                else:
                    if building.data.outdoor_temperature is None:
                        temperature_request_data = None
                
                request_data = {
                    "StartDate": "2023-01-01", 
                    "Areas": {f"{self.BUILDING_TYPES[building_type]}": {"Reg": regular_area, "Eff-E": efficient_area, "Eff-N": 0, "Vef": veryefficient_area}},
                    #"EV_charging" : {"Hou" : {"Units":0.006667, 'Utilization' : 1}},
                    "RetInd": False,
                    "Country": "Norway",
                    "TimeSeries" : temperature_request_data
                    }   
                r = predict.post("https://flexibilitysuite.byggforsk.no/api/Profet", json=request_data)
                if r.status_code == 200:
                    df = pd.DataFrame.from_dict(r.json())
                    dhw = dhw + df['DHW'].to_numpy()
                    spaceheating = spaceheating + df['SpaceHeating'].to_numpy()
                    elspecific = elspecific + df['Electric'].to_numpy()
                else:
                    raise ValueError(f'Invalid status code - PROFet API: {r}.')
        
        if spaceheating_target_sum != None:
            spaceheating_factor = spaceheating_target_sum/np.sum(spaceheating)
            spaceheating = spaceheating * spaceheating_factor
        if dhw_target_sum != None:
            dhw_factor = dhw_target_sum/np.sum(dhw)
            dhw = dhw * dhw_factor
        if electric_target_sum != None:
            electric_factor = electric_target_sum/np.sum(elspecific)
            elspecific = elspecific * electric_factor

        building.results.energy.spaceheating = spaceheating
        building.results.energy.dhw = dhw
        building.results.energy.heating = spaceheating + dhw
        building.results.energy.elspecific = elspecific
        return spaceheating, dhw, elspecific
    
    def preprocess_profet_df(self, building):
        """Beregning som preprosserer 
        PROFet-data (.csv) ved å kjøre PROFet API
        for alle ulike kombinasjoner."""

        df_profet = pd.DataFrame()
        for building_type in self.BUILDING_TYPES:
            for building_standard in self.BUILDING_STANDARDS:
                building.data.standard = [building_standard]
                building.data.type = [building_type]
                building.data.area = [1]
                spaceheating_demand, dhw_demand, electric_demand = self.profet_api(building)
                dhw_column_name = f"{building_type}_{building_standard}_DHW"
                spaceheating_column_name = f"{building_type}_{building_standard}_SPACEHEATING"
                electric_column_name = f"{building_type}_{building_standard}_ELSPECIFIC"
                new_df = pd.DataFrame({
                    dhw_column_name : dhw_demand.flatten(),
                    spaceheating_column_name: spaceheating_demand.flatten(),
                    electric_column_name: electric_demand.flatten()
                    })
                df_profet = update_df(df_profet, new_df)
        self.df_profet = df_profet
        df_profet.to_csv(self.PROFET_FILEPATH, sep=';')

    def read_profet_df(self):
        self.df_profet = pd.read_csv(self.PROFET_FILEPATH, sep=';', index_col=0)

    def profet_calculation_preprocessed(self, building, spaceheating_target_sum = None, dhw_target_sum = None, electric_target_sum = None):
        """Beregning som estimerer romoppvarming, 
        tappevann og elspesifikt behov basert på 
        building fra preprossert PROFet-data (.csv)."""

        spaceheating, dhw, elspecific = np.zeros(8760), np.zeros(8760), np.zeros(8760)
        for i in range(0, len(building.data.standard)):
            building_standard = building.data.standard[i]
            building_type = building.data.type[i]
            building_area = building.data.area[i]
            if building_area != 0:
                dhw = dhw + (self.df_profet[f'{building_type}_{building_standard}_DHW'] * building_area)
                spaceheating = spaceheating + (self.df_profet[f'{building_type}_{building_standard}_SPACEHEATING'] * building_area)
                elspecific = elspecific + (self.df_profet[f'{building_type}_{building_standard}_ELSPECIFIC'] * building_area)
        
        if spaceheating_target_sum != None:
            spaceheating_factor = spaceheating_target_sum/np.sum(spaceheating)
            spaceheating = spaceheating * spaceheating_factor
        if dhw_target_sum != None:
            dhw_factor = dhw_target_sum/np.sum(dhw)
            dhw = dhw * dhw_factor
        if electric_target_sum != None:
            electric_factor = electric_target_sum/np.sum(elspecific)
            elspecific = elspecific * electric_factor

        building.results.energy.spaceheating = np.array(spaceheating)
        building.results.energy.dhw = np.array(dhw)
        building.results.energy.elspecific = np.array(elspecific)
        return spaceheating, dhw, elspecific