"""
Data Ingestion Agent - Enhanced for comprehensive LCA input data
Handles material, energy, emissions, transport, and recycling parameters
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import json

logger = logging.getLogger(__name__)

class DataIngestionAgent:
    """Enhanced Data Ingestion Agent for comprehensive LCA parameters"""
    
    def __init__(self):
        # Define expected columns and their data types
        self.expected_columns = {
            # Material properties
            'Material': str,
            'Mass_kg': float,
            
            # Energy intensity
            'EI_process': float,
            'EI_recycled': float,
            
            # Direct emissions
            'EF_direct': float,
            'EF_direct_recycled': float,
            
            # Grid composition (%)
            'Coal_pct': float,
            'Gas_pct': float,
            'Oil_pct': float,
            'Nuclear_pct': float,
            'Hydro_pct': float,
            'Wind_pct': float,
            'Solar_pct': float,
            'Other_pct': float,
            
            # Transport parameters
            'Transport_mode': str,
            'Transport_distance_km': float,
            'Transport_weight_t': float,
            'Transport_EF': float,
            
            # Material emission factors
            'Virgin_EF': float,
            'Secondary_EF': float,
            
            # Recycling parameters
            'Collection_rate': float,
            'Recycling_efficiency': float,
            'Secondary_content_existing': float
        }
        
        # Define valid values for categorical columns
        self.valid_materials = [
            'steel', 'aluminum', 'copper', 'zinc', 'lead', 
            'nickel', 'tin', 'magnesium', 'titanium'
        ]
        
        self.valid_transport_modes = [
            'truck', 'ship', 'rail', 'air'
        ]
    
    def ingest_data(self, file_path: str, file_type: str = "csv") -> Dict[str, Any]:
        """Ingest and validate LCA input data"""
        try:
            logger.info(f"Starting data ingestion from {file_path}")
            
            # Read file based on type
            if file_type.lower() == "csv":
                df = pd.read_csv(file_path)
            elif file_type.lower() in ["excel", "xlsx", "xls"]:
                df = pd.read_excel(file_path)
            else:
                return {"error": f"Unsupported file type: {file_type}", "success": False}
            
            # Basic validation
            if df.empty:
                return {"error": "File is empty", "success": False}
            
            logger.info(f"Raw data loaded: {len(df)} rows, {len(df.columns)} columns")
            
            # Validate and clean data
            validation_results = self._validate_data(df)
            if not validation_results["valid"]:
                return {
                    "error": "Data validation failed",
                    "validation_errors": validation_results["errors"],
                    "success": False
                }
            
            # Process and structure the data
            processed_data = self._process_data(df)
            
            # Calculate data quality metrics
            quality_metrics = self._assess_data_quality(df, processed_data)
            
            return {
                "success": True,
                "records_count": len(df),
                "processed_data": processed_data,
                "data_quality": quality_metrics,
                "validation_results": validation_results,
                "column_summary": self._get_column_summary(df)
            }
            
        except Exception as e:
            logger.error(f"Data ingestion error: {e}")
            return {"error": str(e), "success": False}
    
    def _validate_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate the input data structure and values"""
        errors = []
        warnings = []
        
        # Check for required columns
        missing_columns = []
        for col in self.expected_columns.keys():
            if col not in df.columns:
                missing_columns.append(col)
        
        if missing_columns:
            errors.append(f"Missing required columns: {missing_columns}")
        
        # Validate data types and ranges
        for col, expected_type in self.expected_columns.items():
            if col in df.columns:
                # Check for missing values
                null_count = df[col].isnull().sum()
                if null_count > 0:
                    warnings.append(f"Column '{col}' has {null_count} missing values")
                
                # Validate specific columns
                if col == 'Material':
                    invalid_materials = df[~df[col].str.lower().isin(self.valid_materials)][col].unique()
                    if len(invalid_materials) > 0:
                        warnings.append(f"Unknown materials found: {list(invalid_materials)}")
                
                elif col == 'Transport_mode':
                    invalid_modes = df[~df[col].str.lower().isin(self.valid_transport_modes)][col].unique()
                    if len(invalid_modes) > 0:
                        warnings.append(f"Unknown transport modes: {list(invalid_modes)}")
                
                # Validate percentage columns (should be 0-100)
                elif col.endswith('_pct') or col in ['Collection_rate', 'Recycling_efficiency', 'Secondary_content_existing']:
                    invalid_pct = df[(df[col] < 0) | (df[col] > 100)][col]
                    if len(invalid_pct) > 0:
                        errors.append(f"Column '{col}' has values outside 0-100% range")
                
                # Validate positive values for mass and distances
                elif col in ['Mass_kg', 'Transport_distance_km', 'Transport_weight_t']:
                    negative_values = df[df[col] < 0][col]
                    if len(negative_values) > 0:
                        errors.append(f"Column '{col}' has negative values")
        
        # Validate grid composition sums to 100%
        grid_columns = ['Coal_pct', 'Gas_pct', 'Oil_pct', 'Nuclear_pct', 'Hydro_pct', 'Wind_pct', 'Solar_pct', 'Other_pct']
        available_grid_cols = [col for col in grid_columns if col in df.columns]
        
        if len(available_grid_cols) > 1:
            grid_sums = df[available_grid_cols].sum(axis=1)
            invalid_sums = grid_sums[(grid_sums < 95) | (grid_sums > 105)]  # Allow 5% tolerance
            if len(invalid_sums) > 0:
                warnings.append(f"Grid composition doesn't sum to 100% for {len(invalid_sums)} rows")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def _process_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Process and structure the data for LCA analysis"""
        
        # Handle multiple rows (scenarios)
        scenarios = []
        
        for idx, row in df.iterrows():
            scenario = {
                # Material properties
                "material_type": row.get('Material', '').lower(),
                "mass_kg": float(row.get('Mass_kg', 0)),
                
                # Energy parameters
                "energy_intensity": {
                    "virgin_process_kwh_per_kg": float(row.get('EI_process', 0)),
                    "recycled_process_kwh_per_kg": float(row.get('EI_recycled', 0))
                },
                
                # Direct emissions
                "direct_emissions": {
                    "virgin_kg_co2e_per_kg": float(row.get('EF_direct', 0)),
                    "recycled_kg_co2e_per_kg": float(row.get('EF_direct_recycled', 0))
                },
                
                # Grid composition
                "grid_composition": {
                    "coal_pct": float(row.get('Coal_pct', 0)),
                    "gas_pct": float(row.get('Gas_pct', 0)),
                    "oil_pct": float(row.get('Oil_pct', 0)),
                    "nuclear_pct": float(row.get('Nuclear_pct', 0)),
                    "hydro_pct": float(row.get('Hydro_pct', 0)),
                    "wind_pct": float(row.get('Wind_pct', 0)),
                    "solar_pct": float(row.get('Solar_pct', 0)),
                    "other_pct": float(row.get('Other_pct', 0))
                },
                
                # Transport parameters
                "transport": {
                    "mode": row.get('Transport_mode', '').lower(),
                    "distance_km": float(row.get('Transport_distance_km', 0)),
                    "weight_t": float(row.get('Transport_weight_t', 0)),
                    "emission_factor_kg_co2e_per_tkm": float(row.get('Transport_EF', 0))
                },
                
                # Material emission factors
                "material_emission_factors": {
                    "virgin_kg_co2e_per_kg": float(row.get('Virgin_EF', 0)),
                    "secondary_kg_co2e_per_kg": float(row.get('Secondary_EF', 0))
                },
                
                # Recycling parameters
                "recycling": {
                    "collection_rate_pct": float(row.get('Collection_rate', 0)),
                    "recycling_efficiency_pct": float(row.get('Recycling_efficiency', 0)),
                    "secondary_content_existing_pct": float(row.get('Secondary_content_existing', 0))
                },
                
                # Calculated fields
                "functional_unit": f"1 kg of {row.get('Material', 'material')}",
                "scenario_id": f"scenario_{idx + 1}"
            }
            
            scenarios.append(scenario)
        
        return {
            "scenarios": scenarios,
            "total_scenarios": len(scenarios),
            "summary": self._generate_data_summary(scenarios)
        }
    
    def _assess_data_quality(self, df: pd.DataFrame, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the quality of the input data"""
        
        total_cells = df.size
        missing_cells = df.isnull().sum().sum()
        completeness = (total_cells - missing_cells) / total_cells
        
        # Check for data consistency
        consistency_issues = 0
        
        # Check if grid composition is reasonable
        grid_columns = ['Coal_pct', 'Gas_pct', 'Oil_pct', 'Nuclear_pct', 'Hydro_pct', 'Wind_pct', 'Solar_pct', 'Other_pct']
        available_grid_cols = [col for col in grid_columns if col in df.columns]
        
        if len(available_grid_cols) > 1:
            grid_sums = df[available_grid_cols].sum(axis=1)
            consistency_issues += len(grid_sums[(grid_sums < 90) | (grid_sums > 110)])
        
        consistency_score = max(0, 1 - (consistency_issues / len(df)))
        
        return {
            "completeness": completeness,
            "consistency": consistency_score,
            "overall_score": (completeness + consistency_score) / 2,
            "missing_values_count": int(missing_cells),
            "total_data_points": int(total_cells),
            "consistency_issues": consistency_issues
        }
    
    def _generate_data_summary(self, scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics for the processed data"""
        
        if not scenarios:
            return {}
        
        materials = [s["material_type"] for s in scenarios]
        masses = [s["mass_kg"] for s in scenarios]
        
        return {
            "unique_materials": list(set(materials)),
            "total_mass_kg": sum(masses),
            "avg_mass_kg": np.mean(masses),
            "mass_range_kg": {"min": min(masses), "max": max(masses)},
            "transport_modes": list(set([s["transport"]["mode"] for s in scenarios])),
            "avg_recycled_content_pct": np.mean([s["recycling"]["secondary_content_existing_pct"] for s in scenarios])
        }
    
    def _get_column_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get summary information about columns"""
        
        summary = {}
        for col in df.columns:
            if col in self.expected_columns:
                summary[col] = {
                    "data_type": str(df[col].dtype),
                    "missing_count": int(df[col].isnull().sum()),
                    "unique_values": int(df[col].nunique()) if df[col].dtype == 'object' else None,
                    "min_value": float(df[col].min()) if pd.api.types.is_numeric_dtype(df[col]) else None,
                    "max_value": float(df[col].max()) if pd.api.types.is_numeric_dtype(df[col]) else None,
                    "mean_value": float(df[col].mean()) if pd.api.types.is_numeric_dtype(df[col]) else None
                }
        
        return summary

    def preprocess_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Preprocess data for LCA analysis"""
        try:
            # This method can be used for additional preprocessing if needed
            scenarios = raw_data.get("scenarios", [])
            
            # Add any additional preprocessing logic here
            for scenario in scenarios:
                # Calculate derived metrics
                scenario["derived_metrics"] = {
                    "recycled_fraction": scenario["recycling"]["secondary_content_existing_pct"] / 100,
                    "transport_emissions_kg_co2e": (
                        scenario["transport"]["distance_km"] * 
                        scenario["transport"]["weight_t"] * 
                        scenario["transport"]["emission_factor_kg_co2e_per_tkm"]
                    )
                }
            
            return {
                "success": True,
                "preprocessed_data": raw_data
            }
            
        except Exception as e:
            logger.error(f"Preprocessing error: {e}")
            return {"error": str(e), "success": False}