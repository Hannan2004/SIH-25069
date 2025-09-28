# DataIngestionAgent.py

import pandas as pd
import numpy as np
import os
import re
import json
from fuzzywuzzy import process
import pdfplumber

class DataIngestionAgent:
    """
    Handles LCA data ingestion:
    - Reads CSV/XLSX/PDF files
    - Performs column standardization
    - Fills missing values using Monte Carlo (uniform) simulation
    - Includes Goal, Scope, Functional Unit from frontend
    """

    def __init__(self):
        # Define standard columns for LCA dataset
        self.STANDARD_COLUMNS = [
            'Material', 'Mass_kg', 'EI_process', 'EI_recycled', 'EF_direct', 'EF_direct_recycled',
            'Coal_pct', 'Gas_pct', 'Oil_pct', 'Nuclear_pct', 'Hydro_pct', 'Wind_pct', 'Solar_pct', 'Other_pct',
            'Transport_mode', 'Transport_distance_km', 'Transport_weight_t', 'Transport_EF',
            'Virgin_EF', 'Secondary_EF', 'Collection_rate', 'Recycling_efficiency', 'Secondary_content_existing'
        ]

        # Assumptions for Monte Carlo simulation
        self.PARAMETER_ASSUMPTIONS = {
            "EI_process": {"simulation": {"min": 14.2*0.9, "max": 14.2*1.1, "unit": "kWh/kg"}},
            "EI_recycled": {"simulation": {"min": 0.7*0.9, "max": 0.7*1.1, "unit": "kWh/kg"}},
            "EF_direct": {"simulation": {"min": 1.5*0.9, "max": 1.5*1.1, "unit": "kgCO2e/kg"}},
            "EF_direct_recycled": {"simulation": {"min": 0.05*0.9, "max": 0.05*1.1, "unit": "kgCO2e/kg"}},
            "Coal_pct": {"simulation": {"min": 70*0.9, "max": 70*1.1, "unit": "%"}},
            "Gas_pct": {"simulation": {"min": 4*0.9, "max": 4*1.1, "unit": "%"}},
            "Oil_pct": {"simulation": {"min": 0.5*0.9, "max": 0.5*1.1, "unit": "%"}},
            "Nuclear_pct": {"simulation": {"min": 3*0.9, "max": 3*1.1, "unit": "%"}},
            "Hydro_pct": {"simulation": {"min": 11*0.9, "max": 11*1.1, "unit": "%"}},
            "Wind_pct": {"simulation": {"min": 5.5*0.9, "max": 5.5*1.1, "unit": "%"}},
            "Solar_pct": {"simulation": {"min": 6*0.9, "max": 6*1.1, "unit": "%"}},
            "Transport_distance_km": {"simulation": {"min": 500*0.9, "max": 500*1.1, "unit": "km"}},
            "Transport_EF": {"simulation": {"min": 0.1*0.9, "max": 0.1*1.1, "unit": "kgCO2e/tkm"}},
            "Collection_rate": {"simulation": {"min": 90*0.9, "max": min(90*1.1,100), "unit": "%"}},
            "Recycling_efficiency": {"simulation": {"min": 92*0.9, "max": min(92*1.1,100), "unit": "%"}},
            "Secondary_content_existing": {"simulation": {"min": 35*0.9, "max": 35*1.1, "unit": "%"}}
        }

    def read_file(self, file_path: str) -> pd.DataFrame:
        """Reads CSV, XLSX, or PDF file into a DataFrame"""
        if file_path.lower().endswith(".csv"):
            return pd.read_csv(file_path)
        elif file_path.lower().endswith((".xlsx", ".xls")):
            return pd.read_excel(file_path)
        elif file_path.lower().endswith(".pdf"):
            return self._read_pdf(file_path)
        else:
            raise ValueError("Unsupported file format. Only CSV, XLSX, XLS, PDF are supported.")

    def _read_pdf(self, file_path: str) -> pd.DataFrame:
        """Extract table from first page of PDF"""
        try:
            with pdfplumber.open(file_path) as pdf:
                page = pdf.pages[0]
                table = page.extract_table()
                if not table:
                    raise ValueError("No table detected in PDF.")
                df = pd.DataFrame(table[1:], columns=table[0])
                return df
        except Exception as e:
            raise ValueError(f"PDF extraction error: {e}")

    def _simulate_missing_value(self, col_name: str, num_trials: int = 10000):
        """Monte Carlo simulation using uniform distribution"""
        if col_name not in self.PARAMETER_ASSUMPTIONS:
            return None, None
        sim = self.PARAMETER_ASSUMPTIONS[col_name]["simulation"]
        values = np.random.uniform(low=sim["min"], high=sim["max"], size=num_trials)
        mean = float(np.round(np.mean(values), 3))
        ci = [float(np.round(values.min(),3)), float(np.round(values.max(),3))]
        return mean, ci

    def standardize_and_fill(self, df: pd.DataFrame) -> dict:
        """Standardize columns, fill missing values, return JSON-ready dict"""
        result = {}
        sim_tracker = {}

        for col in self.STANDARD_COLUMNS:
            if col in df.columns:
                col_data = pd.to_numeric(df[col], errors='coerce')
                if col_data.isnull().any():
                    mean, ci = self._simulate_missing_value(col)
                    col_data.fillna(mean, inplace=True)
                    sim_tracker[col] = ci
                result[col] = col_data.round(3).tolist()
            else:
                mean, ci = self._simulate_missing_value(col)
                result[col] = [mean]
                sim_tracker[col] = ci

        return {"data": result, "confidence_intervals": sim_tracker}

    def ingest_data(self, file_path: str, goal: str, scope: str, functional_unit: str) -> dict:
        """
        Main method to ingest data
        Includes Goal, Scope, and Functional Unit in final output
        """
        try:
            df = self.read_file(file_path)
            output = self.standardize_and_fill(df)
            output["goal"] = goal
            output["scope"] = scope
            output["functional_unit"] = functional_unit
            output["success"] = True
            return output
        except Exception as e:
            return {"success": False, "error": str(e)}

# Example usage
#if __name__ == "__main__":
#    agent = DataIngestionAgent()
#    file_path = "LCA_SHEET.xlsx"  # Replace with your file
#    goal = "CO2 footprint of aluminum production"
#    scope = "cradle_to_gate"
#    functional_unit = "1 kg aluminum"
#    result = agent.ingest_data(file_path, goal, scope, functional_unit)
#    print(json.dumps(result, indent=2))
