# data_ingestion_agent.py

import pandas as pd
import numpy as np
import os
import re
import json
from fuzzywuzzy import process
import pdfplumber
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Define standard columns and assumptions ---
STANDARD_COLUMNS = [
    'Material', 'Mass_kg', 'EI_process', 'EI_recycled', 'EF_direct', 'EF_direct_recycled',
    'Coal_pct', 'Gas_pct', 'Oil_pct', 'Nuclear_pct', 'Hydro_pct', 'Wind_pct', 'Solar_pct', 'Other_pct',
    'Transport_mode', 'Transport_distance_km', 'Transport_weight_t', 'Transport_EF',
    'Virgin_EF', 'Secondary_EF', 'Collection_rate', 'Recycling_efficiency', 'Secondary_content_existing'
]

PARAMETER_ASSUMPTIONS = {
    "EI_process": {"simulation": {"type": "triangular", "mode": 14.2, "min": 12.78, "max": 15.62, "unit": "kWh/kg"}},
    "EI_recycled": {"simulation": {"type": "triangular", "mode": 0.7, "min": 0.63, "max": 0.77, "unit": "kWh/kg"}},
    "EF_direct": {"simulation": {"type": "triangular", "mode": 1.5, "min": 1.35, "max": 1.65, "unit": "kgCO2e/kg"}},
    "EF_direct_recycled": {"simulation": {"type": "triangular", "mode": 0.05, "min": 0.045, "max": 0.055, "unit": "kgCO2e/kg"}},
    # Electricity
    "Coal_pct": {"simulation": {"type": "triangular", "mode": 70, "min": 63, "max": 77, "unit": "%"}},
    "Gas_pct": {"simulation": {"type": "triangular", "mode": 4, "min": 3.6, "max": 4.4, "unit": "%"}},
    "Oil_pct": {"simulation": {"type": "triangular", "mode": 0.5, "min": 0.45, "max": 0.55, "unit": "%"}},
    "Nuclear_pct": {"simulation": {"type": "triangular", "mode": 3, "min": 2.7, "max": 3.3, "unit": "%"}},
    "Hydro_pct": {"simulation": {"type": "triangular", "mode": 11, "min": 9.9, "max": 12.1, "unit": "%"}},
    "Wind_pct": {"simulation": {"type": "triangular", "mode": 5.5, "min": 4.95, "max": 6.05, "unit": "%"}},
    "Solar_pct": {"simulation": {"type": "triangular", "mode": 6, "min": 5.4, "max": 6.6, "unit": "%"}},
    # Transport
    "Transport_distance_km": {"simulation": {"type": "triangular", "mode": 500, "min": 450, "max": 550, "unit": "km"}},
    "Transport_EF": {"simulation": {"type": "triangular", "mode": 0.1, "min": 0.09, "max": 0.11, "unit": "kgCO2e/tkm"}},
    # Recycling
    "Collection_rate": {"simulation": {"type": "triangular", "mode": 90, "min": 81, "max": 99, "unit": "%"}},
    "Recycling_efficiency": {"simulation": {"type": "triangular", "mode": 92, "min": 82.8, "max": 100, "unit": "%"}},
    "Secondary_content_existing": {"simulation": {"type": "triangular", "mode": 35, "min": 31.5, "max": 38.5, "unit": "%"}}
}


class DataIngestionAgent:
    def __init__(self):
        self.standard_cols = STANDARD_COLUMNS
        self.assumptions = PARAMETER_ASSUMPTIONS

    def estimate_value_mc(self, param, trials=10000):
        sim = param.get('simulation', {})
        if sim.get('type') != 'triangular':
            return None, None
        values = np.random.triangular(left=sim['min'], mode=sim['mode'], right=sim['max'], size=trials)
        mean_val = round(np.mean(values), 3)
        ci_95 = [round(np.percentile(values, 2.5), 3), round(np.percentile(values, 97.5), 3)]
        return mean_val, ci_95

    def read_file(self, file_path: str):
        if file_path.lower().endswith('.csv'):
            return pd.read_csv(file_path)
        elif file_path.lower().endswith('.xlsx'):
            return pd.read_excel(file_path)
        elif file_path.lower().endswith('.pdf'):
            return self.read_pdf(file_path)
        else:
            raise ValueError("Unsupported file type")

    def read_pdf(self, file_path: str):
        with pdfplumber.open(file_path) as pdf:
            text = pdf.pages[0].extract_text()
        lines = text.split('\n')
        header_found = False
        table_data = []
        header = []
        for line in lines:
            row_cells = re.split(r'\s{2,}', line.strip())
            if len(row_cells) > 2 and not header_found:
                header = row_cells
                header_found = True
            elif header_found and len(row_cells) == len(header):
                table_data.append(row_cells)
        return pd.DataFrame(table_data, columns=header)

    def standardize_and_fill(self, df: pd.DataFrame, scope: str = "cradle_to_gate"):
        standardized = pd.DataFrame()
        missing_cols = []

        for col in self.standard_cols:
            if col in df.columns:
                standardized[col] = pd.to_numeric(df[col], errors='coerce')
            else:
                standardized[col] = np.nan
                missing_cols.append(col)

        # Handle scope: ignore recycling if cradle_to_gate
        if scope.lower() == 'cradle_to_gate':
            recycling_cols = ['EI_recycled', 'EF_direct_recycled', 'Secondary_EF',
                              'Collection_rate', 'Recycling_efficiency', 'Secondary_content_existing']
            for rc in recycling_cols:
                if rc in standardized.columns:
                    standardized[rc] = np.nan

        # Fill missing values using Monte Carlo
        simulation_tracker = {}
        for col in standardized.columns:
            if standardized[col].isnull().any() and col in self.assumptions:
                mean, ci = self.estimate_value_mc(self.assumptions[col])
                standardized[col].fillna(mean, inplace=True)
                simulation_tracker[col] = {"confidence_interval_95": ci}

        return standardized, simulation_tracker

    def ingest_data(self, file_path: str, goal: str, scope: str, functional_unit: str):
        try:
            df = self.read_file(file_path)
            df_std, sim_tracker = self.standardize_and_fill(df, scope=scope)

            # Prepare dictionary output
            output = []
            for i, row in df_std.iterrows():
                record = {}
                for col, val in row.items():
                    if col in sim_tracker:
                        record[col] = {"value": round(val, 3), "source": "simulated", "confidence_interval_95": sim_tracker[col]["confidence_interval_95"]}
                    else:
                        record[col] = {"value": round(val, 3) if pd.notna(val) else None, "source": "original", "confidence_interval_95": None}
                output.append(record)

            return {"success": True, "processed_data": output, "goal": goal, "scope": scope, "functional_unit": functional_unit}
        except Exception as e:
            logger.error(f"Data ingestion failed: {e}")
            return {"success": False, "error": str(e)}

# --- Example usage ---
if __name__ == "__main__":
    agent = DataIngestionAgent()
    result = agent.ingest_data("LCI_sample.xlsx", goal="CO2 footprint of aluminum", scope="cradle_to_gate", functional_unit="1 kg")
    print(json.dumps(result, indent=2))
