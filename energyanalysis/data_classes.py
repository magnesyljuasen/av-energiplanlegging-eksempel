from dataclasses import dataclass, field
from typing import Union, List
from shapely.geometry import Polygon, Point

@dataclass
class Energy:
    spaceheating: List = field(default=None)
    dhw: List = field(default=None)
    elspecific: List = field(default=None)
    heating: List = field(default=None)
    cooling: List = field(default=None)
    geoenergy_compressor: List = field(default=None)
    geoenergy_extracted_from_wells: List = field(default=None)
    geoenergy_peak: List = field(default=None)
    geoenergy_electricity: List = field(default=None)
    air_water_heat_pump_compressor: List = field(default=None)
    air_water_heat_pump_extracted_from_air: List = field(default=None)
    air_water_heat_pump_peak: List = field(default=None)
    air_water_heat_pump_electricity: List = field(default=None)
    air_air_heat_pump_compressor: List = field(default=None)
    air_air_heat_pump_extracted_from_air: List = field(default=None)
    air_air_heat_pump_peak: List = field(default=None)
    air_air_heat_pump_electricity: List = field(default=None)
    district_heating: List = field(default=None)
    solar_production: List = field(default=None)
    electric_vehicle: List = field(default=None)
    cooling_covered: List = field(default=None)
    cooling_peak: List = field(default=None)
    cooling_compressor: List = field(default=None)
    woodburning : List = field(default=None)
    spaceheating_reduction : List = field(default=None)
    dhw_reduction : List = field(default=None)
    elspecific_reduction : List = field(default=None)
    electricity_for_heating : List = field(default=None)
    electricity_for_elspecific : List = field(default=None)
    electricity_from_grid : List = field(default=None)
    heating_demand : List = field(default=None)
    electric_demand : List = field(default=None)
    renewable : List = field(default=None)
    omgivelsesvarme_varmepumper : List = field(default=None)
    elforbruk_varmepumper : List = field(default=None)
    levert_fra_varmepumper : List = field(default=None)
    elkjel : List = field(default=None)

@dataclass
class Investment:
    geoenergy_heat_pump_size: int = field(default=None)
    geoenergy_borehole_meters: int = field(default=None)
    district_heating: int = field(default=None)
    solar_panels: int = field(default=None)
    air_water_heat_pump_size: int = field(default=None)
    air_air_heat_pump_size: int = field(default=None)
    cooling_pump_size: int = field(default=None)
    peakshaving: int = field(default=None)

@dataclass
class CostData(Investment):
    pass

@dataclass
class InvestmentCost(Investment):
    pass

@dataclass
class ReinvestmentCost(Investment):
    pass

@dataclass
class ServiceCost(Investment):
    pass

@dataclass
class InvestmentLifetime(Investment):
    pass

@dataclass
class InvestmentEmission(Investment):
    pass

@dataclass
class OperationData(Energy):
    pass
    
@dataclass
class OperationCost(Energy):
    pass

@dataclass
class OperationEmission(Energy):
    pass

#--

@dataclass
class Results:
    energy: Energy = field(default_factory=Energy)
    investment: Investment = field(default_factory=Investment)
    investment_cost: InvestmentCost = field(default_factory=InvestmentCost)
    reinvestment_cost: ReinvestmentCost = field(default_factory=ReinvestmentCost)
    investment_lifetime: InvestmentLifetime = field(default_factory=InvestmentLifetime)
    investment_emission: InvestmentEmission = field(default_factory=InvestmentEmission)
    service_cost: ServiceCost = field(default_factory=ServiceCost)
    operation_cost: OperationCost = field(default_factory=OperationCost)
    operation_emission: OperationEmission = field(default_factory=OperationEmission)

    def get_heating_balance(self):
        heating_balance = self.spaceheating + self.dhw - self.geoenergy_extracted_from_wells - self.geoenergy_compressor
        return heating_balance
    
    def get_electric_balance(self):
        electric_balance = self.elspecific + self.geoenergy_compressor
        return electric_balance
    
    def __setattr__(self, name, value):
        super().__setattr__(name, value)


@dataclass
class BuildingData:
    """Lagrer data om bygningen som areal, 
    type, standard, utetemperatur, grunnflate, 
    antall etasjer"""
    
    area : Union[List] = field(default=None)
    type : Union[List] = field(default=None)
    standard : Union[List] = field(default=None)
    outdoor_temperature: List = field(default=None)
    floor_area: int = field(default=None)
    stories: int = field(default=None)

#    def __post_init__(self):
#        valid_types = ['Hus', 'Leilighet', 'Kontor']
#        valid_standards = ['Lite energieffektiv', 'Middels energieffektiv', 'Veldig energieffektiv']
#        if self.type and self.type not in valid_types:
#            raise ValueError(f'Invalid building type: {self.type}')
#        elif self.standard and self.standard not in valid_standards:
#            raise ValueError(f'Invalid building standard: {self.standard}')


@dataclass
class HeatingSystem:
    """Lagrer data om varmesystemet"""

    type: str = field(default=None)
    flow_temperature: List = field(default=None)

    def __post_init__(self):
        valid_heating_systems = ['Gulvvarme', 'Radiator', 'Tappevann']
        if self.type and self.type not in valid_heating_systems:
            raise ValueError(f'Invalid heating system: {self.heating_system}')

@dataclass
class Address:
    """Lagrer addresse med navn, 
    koordinat og geometri"""

    name : str = field(default=None)
    lat : float = field(default=None)
    long : float = field(default=None)
    geometry : Union[Polygon, Point] = field(default=None)


@dataclass
class Building:
    """Samleklasse som representer data som 
    tilhører en bygning. Denne brukes som input-dataklasse 
    inn i videre metoder. Videre metoder returnerer så 
    resultater som legges tilbake i denne samleklassen. 
    På denne måten samles alle resultatene på et sted."""

    address: Address = field(default=None)
    data: BuildingData = field(default=None)
    heatingsystem: HeatingSystem = field(default=None)
    results: Results = field(default=None) 


if __name__ == '__main__':
    building = Building(
        data=BuildingData(500, 'Hus', 'Veldig energieffektiv'),
        heatingsystem=HeatingSystem('Gulvvarme'),
        address=Address('Jåttåvågen', 63, 10),
        results=Results(spaceheating=[30000, 20000, 10000]),
        )

    print(vars(building))

