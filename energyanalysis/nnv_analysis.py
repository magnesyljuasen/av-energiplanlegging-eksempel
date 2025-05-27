import streamlit as st
import numpy as np
import numpy_financial as npf
import pandas as pd

class NetPresentValue:
    def __init__(self):
        self.set_simple_conditions()

    def set_simple_conditions(self, rate=4, calculation_time=30):
        self.rate = rate/100
        self.calculation_time = calculation_time

    def calculate_npv(self, rate, cash_flows):
        return int(npf.npv(rate, cash_flows))

    def calculation(self, cost_map):
        incomes, expenses, cash_flows = np.zeros(self.calculation_time), np.zeros(self.calculation_time), np.zeros(self.calculation_time)
        for i in range(0, self.calculation_time):
            if i == 0:
                expenses[i] = cost_map['investment_year_zero']
            else:
                incomes[i] = cost_map['yearly_savings']
            if (i != 0) and (i % cost_map['investment_lifetime'] == 0):
                expenses[i] = cost_map['reinvestment']

        cash_flows = -expenses + incomes
        npv = self.calculate_npv(self.rate, cash_flows)
        rates = np.linspace(0.01, 0.20, 100)  # Discount rates from 1% to 20%
        npvs = [self.calculate_npv(rate, cash_flows) for rate in rates]
        df_npvs = pd.DataFrame({'rate' : rates*100, 'npv' : npvs})
        df_npvs['rate'] = df_npvs['rate'].round(1)
        df_npvs = df_npvs.set_index('rate')
        df_cash_flows = pd.DataFrame({'incomes' : incomes, 'expenses' : -expenses})

        return npv, cash_flows, df_npvs, df_cash_flows

    



    



    