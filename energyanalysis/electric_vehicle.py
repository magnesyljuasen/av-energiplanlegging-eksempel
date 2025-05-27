import numpy as np
import pandas as pd
from .data_classes import Building, Address, BuildingData, Results


class ElectricVehicle:
    def __init__(self):
        self.set_simple_sizing_conditions()

    def set_simple_sizing_conditions(self):
        self.df_electric_vehicle_sheet = pd.read_excel('src/data/electric_vehicle_sheet.xlsx')
        self.ELECTIC_VEHICLES_CHARGERS = {
            'Hus' : 'Hjemmelader', 
            'Leilighet' : 'Hjemmelader',
            'Kontor' : 'Offentlig',
            'Butikk' : 'Offentlig',
            'Hotell' : 'Offentlig', 
            'Barnehage' : 'Offentlig',
            'Skole' : 'Offentlig',
            'Universitet' : 'Offentlig',
            'Kultur' : 'Offentlig',
            'Sykehjem' : 'Offentlig', 
            'Sykehus' : 'Offentlig',
            'Andre' : 'Offentlig',
        }
    
    def simple_sizing(self, building):
        """Enkel beregning som beregner elbil. """
        if len(building.data.type) > 1:
            charging_type = 'Offentlig'
        else:
            charging_type = self.ELECTIC_VEHICLES_CHARGERS[building.data.type[0]]
        
        if building.data.type[0] == 'Hus':
            users = 2
        elif building.data.type[0] == 'Leilighet':
            users = int((building.data.area[0] / 70) * 0.3 * 2)

        if charging_type == 'Hjemmelader':
            electric_vehicle = np.array(self.df_electric_vehicle_sheet[charging_type] * users)
            building.results.energy.electric_vehicle = electric_vehicle
        

if __name__ == "__main__":
    building = Building(
        address = Address(),
        data = BuildingData([600], ['Hus'], ['Lite energieffektiv'], floor_area=100),
        results = Results()
    )
    ElectricVehicle().simple_sizing(building)
