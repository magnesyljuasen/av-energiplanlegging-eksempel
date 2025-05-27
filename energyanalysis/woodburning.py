from .utilities import coverage_calculation
import streamlit as st
import numpy as np
import pandas as pd
import holidays


class Woodburning:
    def __init__(self):
        self.set_simple_sizing_conditions()

    def set_simple_sizing_conditions(self):
        pass 
    
    def simple_sizing(self, building, percentage, mode='Flat'):
        percentage = 100 - percentage
        if mode == 'Flat':
            woodburning_not_covered = coverage_calculation(percentage, building.results.energy.spaceheating)
            woodburning_covered = building.results.energy.spaceheating - woodburning_not_covered
            building.results.energy.woodburning = woodburning_covered
    
    def advanced_sizing(self, building, power=5, efficiency=1, temperature_limit=-5, min_runtime_hours=4, coverage=50):
        # Create DataFrame
        df = pd.DataFrame()
        df["T_outdoor"] = building.data.outdoor_temperature
        df["Q_demand"] = building.results.energy.spaceheating * (coverage/100)

        # Create a timestamp column assuming hourly data from Jan 1, 2023
        norwegian_holidays = holidays.Norway(years=2023)
        df["timestamp"] = pd.date_range(start="2023-01-01 00:00:00", periods=len(df), freq="H")
        df["hour"] = df["timestamp"].dt.hour
        df["weekday"] = df["timestamp"].dt.weekday  # Monday = 0, Sunday = 6
        df["date"] = df["timestamp"].dt.date
        df["month"] = df["timestamp"].dt.month
        df["is_holiday"] = df["date"].astype(str).apply(lambda x: x in norwegian_holidays)

        df["fyringssesong"] = df["month"].between(10, 12) | df["month"].between(1, 4)

        # Define wood burning availability based on time rules
        df["time_allowed"] = np.where(
            (df["fyringssesong"]) & (
                ((df["weekday"] < 5) & (df["hour"].between(15, 23))) |  # Weekdays 15:00–24:00
                ((df["weekday"] >= 5) & (df["hour"].between(8, 23))) |   # Weekends 08:00–24:00
                ((df["is_holiday"]) & (df["hour"].between(8, 23))) # Public holidays 08:00–24:00
                ),
                1,
                0
                )

        # Initial stove state based on temperature & time availability
        df["stove_on_raw"] = np.where((df["T_outdoor"] <= temperature_limit) & (df["time_allowed"] == 1), 1, 0)

        # Apply minimum runtime constraint
        df["stove_on"] = 0
        stove_running = False
        hours_since_on = 0

        for i in range(len(df)):
            if df.loc[i, "stove_on_raw"] == 1:  # Should be on based on temperature & time
                if not stove_running:
                    stove_running = True
                    hours_since_on = 0
                df.loc[i, "stove_on"] = 1
            elif stove_running and hours_since_on < min_runtime_hours:
                df.loc[i, "stove_on"] = 1  # Keep it on for minimum runtime
                hours_since_on += 1
            else:
                stove_running = False

        # Calculate heat delivered by the wood stove
        df["Q_woodstove"] = df["stove_on"] * np.minimum(df["Q_demand"], power * efficiency)

        # Calculate remaining heating demand after wood stove
        df["Q_remaining"] = df["Q_demand"] - df["Q_woodstove"]

        # Store results in the building object
        building.results.energy.woodburning = np.array(df["Q_woodstove"])
