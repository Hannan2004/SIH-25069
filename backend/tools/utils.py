"""
Utility Functions for LCA Tools
Common helper functions, data validation, unit conversions, and statistical operations
"""

from typing import Dict, List, Optional, Tuple, Any, Union
import logging
import math
import statistics
from datetime import datetime
import json
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Unit conversion factors
UNIT_CONVERSIONS = {
    # Mass conversions (to kg)
    "mass": {
        "kg": 1.0,
        "g": 0.001,
        "t": 1000.0,
        "tonnes": 1000.0,
        "lb": 0.453592,
        "oz": 0.0283495
    },
    
    # Energy conversions (to kWh)
    "energy": {
        "kwh": 1.0,
        "mj": 0.277778,
        "gj": 277.778,
        "btu": 0.000293071,
        "cal": 1.163e-6,
        "kcal": 0.001163,
        "j": 2.77778e-7
    },
    
    # Distance conversions (to km)
    "distance": {
        "km": 1.0,
        "m": 0.001,
        "cm": 1e-5,
        "miles": 1.60934,
        "ft": 0.0003048,
        "yards": 0.0009144
    },
    
    # Emission factor conversions (to kg CO2e)
    "emissions": {
        "kg_co2e": 1.0,
        "g_co2e": 0.001,
        "t_co2e": 1000.0,
        "lb_co2e": 0.453592
    }
}

# Data validation patterns
VALIDATION_PATTERNS = {
    "metal_type": ["aluminum", "aluminium", "copper", "cu", "al"],
    "region": ["national_average", "northern", "western", "southern", "eastern", "northeastern", 
               "urban_tier1", "urban_tier2", "urban_tier3", "rural", "industrial_zones", "coastal_areas"],
    "scenario": ["current_2024", "renewable_target_2030", "ambitious_2030"],
    "transport_mode": ["truck_heavy", "truck_medium", "truck_light", "truck_electric", 
                      "rail_freight", "rail_electric", "rail_diesel", "coastal_shipping", 
                      "river_barge", "multimodal", "container_truck", "bulk_truck", "pipeline"]
}

def validate_input_data(data: Dict[str, Any], required_fields: List[str], 
                       validation_rules: Optional[Dict[str, Any]] = None) -> Tuple[bool, List[str]]:
    """
    Validate input data against required fields and rules
    
    Args:
        data (Dict): Input data to validate
        required_fields (List[str]): List of required field names
        validation_rules (Dict, optional): Custom validation rules
        
    Returns:
        Tuple[bool, List[str]]: (is_valid, list_of_errors)
    """
    
    errors = []
    
    # Check required fields
    for field in required_fields:
        if field not in data or data[field] is None:
            errors.append(f"Missing required field: {field}")
    
    # Apply validation rules
    if validation_rules:
        for field, rules in validation_rules.items():
            if field in data and data[field] is not None:
                value = data[field]
                
                # Type validation
                if "type" in rules and not isinstance(value, rules["type"]):
                    errors.append(f"Field '{field}' must be of type {rules['type'].__name__}")
                
                # Range validation for numeric values
                if "range" in rules and isinstance(value, (int, float)):
                    min_val, max_val = rules["range"]
                    if not (min_val <= value <= max_val):
                        errors.append(f"Field '{field}' must be between {min_val} and {max_val}")
                
                # Allowed values validation
                if "allowed_values" in rules and value not in rules["allowed_values"]:
                    errors.append(f"Field '{field}' must be one of: {rules['allowed_values']}")
                
                # Custom validation function
                if "custom_validator" in rules:
                    is_valid, error_msg = rules["custom_validator"](value)
                    if not is_valid:
                        errors.append(f"Field '{field}': {error_msg}")
    
    return len(errors) == 0, errors

def convert_units(value: float, from_unit: str, to_unit: str, unit_type: str) -> float:
    """
    Convert between different units
    
    Args:
        value (float): Value to convert
        from_unit (str): Source unit
        to_unit (str): Target unit
        unit_type (str): Type of unit (mass, energy, distance, emissions)
        
    Returns:
        float: Converted value
        
    Raises:
        ValueError: If unit type or units are not supported
    """
    
    if unit_type not in UNIT_CONVERSIONS:
        raise ValueError(f"Unsupported unit type: {unit_type}")
    
    conversions = UNIT_CONVERSIONS[unit_type]
    
    if from_unit.lower() not in conversions:
        raise ValueError(f"Unsupported source unit: {from_unit}")
    
    if to_unit.lower() not in conversions:
        raise ValueError(f"Unsupported target unit: {to_unit}")
    
    # Convert to base unit, then to target unit
    base_value = value * conversions[from_unit.lower()]
    target_value = base_value / conversions[to_unit.lower()]
    
    return target_value

def normalize_metal_type(metal_type: str) -> str:
    """
    Normalize metal type input to standard format
    
    Args:
        metal_type (str): Input metal type
        
    Returns:
        str: Normalized metal type ("aluminum" or "copper")
    """
    
    metal_lower = metal_type.lower().strip()
    
    if metal_lower in ["aluminum", "aluminium", "al"]:
        return "aluminum"
    elif metal_lower in ["copper", "cu"]:
        return "copper"
    else:
        raise ValueError(f"Unsupported metal type: {metal_type}")

def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """
    Calculate percentage change between two values
    
    Args:
        old_value (float): Original value
        new_value (float): New value
        
    Returns:
        float: Percentage change (positive = increase, negative = decrease)
    """
    
    if old_value == 0:
        return float('inf') if new_value > 0 else 0.0
    
    return ((new_value - old_value) / old_value) * 100

def weighted_average(values: List[float], weights: List[float]) -> float:
    """
    Calculate weighted average
    
    Args:
        values (List[float]): List of values
        weights (List[float]): List of weights (must sum to 1.0)
        
    Returns:
        float: Weighted average
        
    Raises:
        ValueError: If lengths don't match or weights don't sum to ~1.0
    """
    
    if len(values) != len(weights):
        raise ValueError("Values and weights lists must have the same length")
    
    weight_sum = sum(weights)
    if not (0.99 <= weight_sum <= 1.01):  # Allow small rounding errors
        raise ValueError(f"Weights must sum to 1.0, got {weight_sum}")
    
    return sum(v * w for v, w in zip(values, weights))

def interpolate_linear(x1: float, y1: float, x2: float, y2: float, x: float) -> float:
    """
    Perform linear interpolation
    
    Args:
        x1, y1 (float): First point coordinates
        x2, y2 (float): Second point coordinates
        x (float): X value to interpolate
        
    Returns:
        float: Interpolated Y value
    """
    
    if x1 == x2:
        return y1  # Avoid division by zero
    
    return y1 + (y2 - y1) * (x - x1) / (x2 - x1)

def calculate_confidence_interval(mean: float, std_dev: float, 
                                confidence_level: float = 0.95, 
                                sample_size: Optional[int] = None) -> Tuple[float, float]:
    """
    Calculate confidence interval for a mean
    
    Args:
        mean (float): Sample mean
        std_dev (float): Standard deviation
        confidence_level (float): Confidence level (0-1)
        sample_size (int, optional): Sample size (uses t-distribution if provided)
        
    Returns:
        Tuple[float, float]: (lower_bound, upper_bound)
    """
    
    if confidence_level <= 0 or confidence_level >= 1:
        raise ValueError("Confidence level must be between 0 and 1")
    
    # For simplicity, using normal distribution approximation
    # In production, would use scipy.stats for proper t-distribution
    z_score = {
        0.90: 1.645,
        0.95: 1.960,
        0.99: 2.576
    }.get(confidence_level, 1.960)  # Default to 95%
    
    margin_of_error = z_score * std_dev
    
    if sample_size and sample_size < 30:
        # Apply small sample correction (simplified)
        correction_factor = math.sqrt(sample_size / (sample_size - 1))
        margin_of_error *= correction_factor
    
    return (mean - margin_of_error, mean + margin_of_error)

def aggregate_emissions_by_category(emission_data: List[Dict[str, Any]], 
                                  category_field: str = "category") -> Dict[str, float]:
    """
    Aggregate emissions data by category
    
    Args:
        emission_data (List[Dict]): List of emission records
        category_field (str): Field name for categorization
        
    Returns:
        Dict[str, float]: Aggregated emissions by category
    """
    
    aggregated = {}
    
    for record in emission_data:
        if category_field not in record or "emissions_kg_co2e" not in record:
            logger.warning(f"Missing required fields in emission record: {record}")
            continue
        
        category = record[category_field]
        emissions = record["emissions_kg_co2e"]
        
        if category in aggregated:
            aggregated[category] += emissions
        else:
            aggregated[category] = emissions
    
    return aggregated

def calculate_monte_carlo_statistics(values: List[float]) -> Dict[str, float]:
    """
    Calculate statistical metrics for Monte Carlo simulation results
    
    Args:
        values (List[float]): List of simulation results
        
    Returns:
        Dict[str, float]: Statistical summary
    """
    
    if not values:
        return {"error": "No values provided"}
    
    sorted_values = sorted(values)
    n = len(values)
    
    return {
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "std_dev": statistics.stdev(values) if n > 1 else 0.0,
        "min": min(values),
        "max": max(values),
        "percentile_5": sorted_values[int(0.05 * n)],
        "percentile_25": sorted_values[int(0.25 * n)],
        "percentile_75": sorted_values[int(0.75 * n)],
        "percentile_95": sorted_values[int(0.95 * n)],
        "coefficient_of_variation": statistics.stdev(values) / statistics.mean(values) if n > 1 and statistics.mean(values) != 0 else 0.0,
        "sample_size": n
    }

def format_lca_results(results: Dict[str, Any], precision: int = 4) -> Dict[str, Any]:
    """
    Format LCA results for consistent presentation
    
    Args:
        results (Dict): Raw LCA results
        precision (int): Number of decimal places for formatting
        
    Returns:
        Dict: Formatted results
    """
    
    def format_value(value):
        if isinstance(value, float):
            return round(value, precision)
        elif isinstance(value, dict):
            return {k: format_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [format_value(item) for item in value]
        else:
            return value
    
    return format_value(results)

def validate_lca_completeness(lca_results: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate completeness of LCA results
    
    Args:
        lca_results (Dict): LCA calculation results
        
    Returns:
        Tuple[bool, List[str]]: (is_complete, missing_components)
    """
    
    required_components = [
        "lca_metadata",
        "formula_5_breakdown", 
        "emission_source_breakdown",
        "energy_analysis",
        "key_performance_indicators"
    ]
    
    missing = []
    
    for component in required_components:
        if component not in lca_results:
            missing.append(component)
        elif not lca_results[component]:  # Check if empty
            missing.append(f"{component} (empty)")
    
    # Check key numeric results
    key_metrics = [
        ("formula_5_breakdown", "total_net_emissions_kg_co2e"),
        ("formula_5_breakdown", "emission_intensity_kg_co2e_per_kg"),
        ("energy_analysis", "total_energy_consumption_kwh")
    ]
    
    for section, metric in key_metrics:
        if section in lca_results and metric not in lca_results[section]:
            missing.append(f"{section}.{metric}")
    
    return len(missing) == 0, missing

def generate_lca_summary_statistics(lca_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate summary statistics from LCA results
    
    Args:
        lca_results (Dict): Complete LCA results
        
    Returns:
        Dict: Summary statistics
    """
    
    try:
        breakdown = lca_results.get("formula_5_breakdown", {})
        energy = lca_results.get("energy_analysis", {})
        kpis = lca_results.get("key_performance_indicators", {})
        
        return {
            "total_carbon_footprint_kg_co2e": breakdown.get("total_net_emissions_kg_co2e", 0),
            "carbon_intensity_kg_co2e_per_kg": breakdown.get("emission_intensity_kg_co2e_per_kg", 0),
            "total_energy_consumption_kwh": energy.get("total_energy_consumption_kwh", 0),
            "energy_intensity_kwh_per_kg": energy.get("energy_intensity_kwh_per_kg", 0),
            "recycling_content_percent": lca_results.get("lca_metadata", {}).get("recycled_fraction", 0) * 100,
            "circularity_index": kpis.get("circularity_index", 0),
            "resource_efficiency_score": kpis.get("resource_efficiency_score", 0),
            "renewable_energy_share_percent": kpis.get("renewable_energy_share_percent", 0),
            
            "emission_breakdown_percent": calculate_emission_breakdown_percentages(lca_results),
            "impact_hotspots": identify_impact_hotspots(lca_results)
        }
        
    except Exception as e:
        logger.error(f"Error generating summary statistics: {e}")
        return {"error": str(e)}

def calculate_emission_breakdown_percentages(lca_results: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculate percentage breakdown of emissions by source
    
    Args:
        lca_results (Dict): LCA results
        
    Returns:
        Dict[str, float]: Percentage breakdown
    """
    
    try:
        breakdown = lca_results.get("emission_source_breakdown", {})
        total = breakdown.get("total_kg_co2e", 0)
        
        if total == 0:
            return {}
        
        return {
            "electricity_percent": (breakdown.get("electricity_emissions_kg_co2e", 0) / total) * 100,
            "process_gases_percent": (breakdown.get("process_gas_emissions_kg_co2e", 0) / total) * 100,
            "transport_percent": (breakdown.get("transport_emissions_kg_co2e", 0) / total) * 100,
            "eol_credits_percent": abs(breakdown.get("eol_credits_kg_co2e", 0) / total) * 100
        }
        
    except Exception as e:
        logger.error(f"Error calculating emission breakdown: {e}")
        return {}

def identify_impact_hotspots(lca_results: Dict[str, Any], threshold_percent: float = 20.0) -> List[Dict[str, Any]]:
    """
    Identify emission hotspots (sources contributing >threshold% of total)
    
    Args:
        lca_results (Dict): LCA results
        threshold_percent (float): Minimum percentage to be considered a hotspot
        
    Returns:
        List[Dict]: List of hotspots with details
    """
    
    hotspots = []
    
    try:
        percentages = calculate_emission_breakdown_percentages(lca_results)
        
        for source, percent in percentages.items():
            if percent >= threshold_percent:
                hotspots.append({
                    "emission_source": source.replace("_percent", ""),
                    "contribution_percent": percent,
                    "priority": "high" if percent >= 50 else "medium",
                    "improvement_potential": "significant" if percent >= 30 else "moderate"
                })
        
        # Sort by contribution (highest first)
        hotspots.sort(key=lambda x: x["contribution_percent"], reverse=True)
        
    except Exception as e:
        logger.error(f"Error identifying hotspots: {e}")
    
    return hotspots

def create_lca_metadata(metal_type: str, production_kg: float, recycled_fraction: float,
                       product_type: str, region: str, scenario: str,
                       calculation_timestamp: Optional[str] = None) -> Dict[str, Any]:
    """
    Create standardized LCA metadata
    
    Args:
        metal_type (str): Type of metal
        production_kg (float): Production quantity
        recycled_fraction (float): Recycled content fraction
        product_type (str): Product type
        region (str): Geographic region
        scenario (str): Grid scenario
        calculation_timestamp (str, optional): ISO timestamp
        
    Returns:
        Dict: LCA metadata
    """
    
    if calculation_timestamp is None:
        calculation_timestamp = datetime.now().isoformat()
    
    return {
        "calculation_timestamp": calculation_timestamp,
        "methodology": "ISO 14040/14044 compliant",
        "functional_unit": f"1 kg {metal_type}",
        "metal_type": normalize_metal_type(metal_type),
        "production_kg": production_kg,
        "recycled_fraction": recycled_fraction,
        "product_type": product_type,
        "geographic_region": region,
        "grid_scenario": scenario,
        "system_boundary": "cradle_to_gate_with_eol_credits",
        "impact_assessment_method": "IPCC_AR5_GWP100",
        "data_quality": {
            "temporal_coverage": "2024",
            "geographic_coverage": "India",
            "technology_coverage": "Average Indian technology mix"
        },
        "assumptions": [
            "India grid electricity mix used for all processes",
            "Transport distances based on typical Indian supply chains",
            "End-of-life recycling credits included",
            "Informal recycling sector contributions estimated"
        ]
    }

def export_results_to_json(results: Dict[str, Any], filepath: str, 
                          pretty_print: bool = True) -> bool:
    """
    Export LCA results to JSON file
    
    Args:
        results (Dict): Results to export
        filepath (str): Output file path
        pretty_print (bool): Format JSON for readability
        
    Returns:
        bool: Success status
    """
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            if pretty_print:
                json.dump(results, f, indent=2, ensure_ascii=False)
            else:
                json.dump(results, f, ensure_ascii=False)
        
        logger.info(f"Results exported successfully to {filepath}")
        return True
        
    except Exception as e:
        logger.error(f"Error exporting results to {filepath}: {e}")
        return False

# Validation functions for specific data types
def validate_emission_factor(ef: float, ef_type: str) -> Tuple[bool, str]:
    """Validate emission factor values"""
    if ef < 0:
        return False, "Emission factor cannot be negative"
    
    # Reasonable ranges for different types
    ranges = {
        "grid": (0.0, 2.0),      # kg CO2e/kWh
        "transport": (0.0, 0.5),  # kg CO2e/t·km
        "process": (0.0, 20.0)    # kg CO2e/kg metal
    }
    
    if ef_type in ranges:
        min_val, max_val = ranges[ef_type]
        if not (min_val <= ef <= max_val):
            return False, f"Emission factor {ef} outside reasonable range [{min_val}, {max_val}] for type {ef_type}"
    
    return True, ""

def validate_recycled_fraction(fraction: float) -> Tuple[bool, str]:
    """Validate recycled fraction"""
    if not (0.0 <= fraction <= 1.0):
        return False, "Recycled fraction must be between 0.0 and 1.0"
    return True, ""

def validate_production_quantity(quantity: float) -> Tuple[bool, str]:
    """Validate production quantity"""
    if quantity <= 0:
        return False, "Production quantity must be positive"
    if quantity > 1e9:  # 1 billion kg seems unreasonable for single calculation
        return False, "Production quantity seems unreasonably large"
    return True, ""

# Error handling decorator
def handle_calculation_errors(func):
    """Decorator to handle common calculation errors"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ZeroDivisionError:
            logger.error(f"Division by zero in {func.__name__}")
            return {"error": "Division by zero error", "function": func.__name__}
        except ValueError as e:
            logger.error(f"Value error in {func.__name__}: {e}")
            return {"error": f"Invalid input: {str(e)}", "function": func.__name__}
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}")
            return {"error": f"Calculation error: {str(e)}", "function": func.__name__}
    
    return wrapper

# Test the utility functions
if __name__ == "__main__":
    # Test unit conversion
    print(f"Convert 1000 g to kg: {convert_units(1000, 'g', 'kg', 'mass')} kg")
    print(f"Convert 500 miles to km: {convert_units(500, 'miles', 'km', 'distance'):.2f} km")
    
    # Test validation
    test_data = {
        "metal_type": "aluminum",
        "production_kg": 1000.0,
        "recycled_fraction": 0.3
    }
    
    rules = {
        "production_kg": {"type": float, "range": (0, 1e6)},
        "recycled_fraction": {"type": float, "range": (0, 1)}
    }
    
    is_valid, errors = validate_input_data(test_data, ["metal_type", "production_kg"], rules)
    print(f"Validation result: {is_valid}, Errors: {errors}")
    
    # Test statistics
    values = [10.2, 12.5, 11.8, 9.7, 13.1, 10.9, 12.3]
    stats = calculate_monte_carlo_statistics(values)
    print(f"Statistics: Mean={stats['mean']:.2f}, Std={stats['std_dev']:.2f}")