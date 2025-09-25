"""
LCA Tools Package for Metal Industry Carbon Footprint Analysis
Implements comprehensive Life Cycle Assessment calculations for aluminum and copper production
with India-specific data and methodologies.

This package provides:
- Formula 1: Process emission calculations (EF(process) = EI × EF(grid) + EF(direct))
- Formula 2: Grid emission factor calculations (weighted electricity mix)
- Formula 3: Transport emission calculations (Weight × Distance × EF(transport))
- Formula 4: Recycling and circularity metrics
- Formula 5: Total LCA calculations (inventory-based full model)

Author: SIH Team 25069
Version: 1.0.0
License: MIT
"""

__version__ = "1.0.0"
__author__ = "SIH Team 25069"

# Import all calculation functions
from .gwp_constants import (
    GWP_VALUES,
    ALUMINUM_PROCESS_GASES,
    COPPER_PROCESS_GASES,
    convert_to_co2_eq,
    get_gwp_value,
    calculate_total_gwp
)

from .grid_emission_tools import (
    GRID_EMISSION_FACTORS,
    INDIA_REGIONAL_GRIDS,
    INDIA_FUTURE_SCENARIOS,
    calculate_grid_emission_factor,
    get_india_grid_ef,
    compare_grid_scenarios,
    get_renewable_share,
    grid_decarbonization_impact
)

from .process_emission_tools import (
    ALUMINUM_ENERGY_INTENSITY,
    COPPER_ENERGY_INTENSITY,
    ALUMINUM_DIRECT_EMISSIONS,
    COPPER_DIRECT_EMISSIONS,
    calculate_process_emissions,
    calculate_production_chain_emissions,
    compare_primary_vs_secondary,
    sensitivity_analysis_energy_intensity
)

from .transport_tools import (
    INDIA_TRANSPORT_EMISSION_FACTORS,
    INDIA_CITY_DISTANCES,
    INDIA_TRANSPORT_PREFERENCES,
    TRANSPORT_LOAD_FACTORS,
    calculate_transport_emissions,
    calculate_multimodal_transport,
    compare_transport_modes,
    get_city_route_emissions,
    transport_optimization_suggestions
)

from .recycling_tools import (
    INDIA_RECYCLING_RATES,
    PRODUCT_LIFETIMES,
    REGIONAL_COLLECTION_EFFICIENCY,
    RECYCLING_ENERGY_EFFICIENCY,
    calculate_effective_secondary_content,
    calculate_product_secondary_share,
    calculate_avoided_virgin_production,
    calculate_effective_product_emission_factor,
    calculate_circularity_metrics,
    compare_recycling_scenarios,
    generate_circularity_recommendations,
    calculate_end_of_life_scenarios
)

from .total_lca_tools import (
    STANDARD_PRODUCTION_ROUTES,
    TYPICAL_TRANSPORT_DISTANCES,
    calculate_total_lca_emissions,
    calculate_transport_emissions_for_lca,
    calculate_impact_categories,
    calculate_uncertainty_metrics,
    compare_lca_scenarios
)

from .utils import (
    UNIT_CONVERSIONS,
    VALIDATION_PATTERNS,
    validate_input_data,
    convert_units,
    normalize_metal_type,
    calculate_percentage_change,
    weighted_average,
    interpolate_linear,
    calculate_confidence_interval,
    aggregate_emissions_by_category,
    calculate_monte_carlo_statistics,
    format_lca_results,
    validate_lca_completeness,
    generate_lca_summary_statistics,
    calculate_emission_breakdown_percentages,
    identify_impact_hotspots,
    create_lca_metadata,
    export_results_to_json,
    validate_emission_factor,
    validate_recycled_fraction,
    validate_production_quantity,
    handle_calculation_errors
)

# Package-level convenience functions
def quick_lca_calculation(metal_type: str, 
                         production_kg: float, 
                         recycled_fraction: float = 0.0,
                         region: str = "national_average") -> dict:
    """
    Quick LCA calculation with default parameters
    
    Args:
        metal_type (str): "aluminum" or "copper"
        production_kg (float): Production quantity in kg
        recycled_fraction (float): Recycled content fraction (0-1)
        region (str): Indian grid region
        
    Returns:
        dict: Simplified LCA results
    """
    
    try:
        # Validate inputs
        metal_type = normalize_metal_type(metal_type)
        
        if not validate_production_quantity(production_kg)[0]:
            raise ValueError("Invalid production quantity")
        
        if not validate_recycled_fraction(recycled_fraction)[0]:
            raise ValueError("Invalid recycled fraction")
        
        # Calculate full LCA
        full_results = calculate_total_lca_emissions(
            metal_type=metal_type,
            production_kg=production_kg,
            recycled_fraction=recycled_fraction,
            region=region
        )
        
        # Extract key results
        return {
            "metal_type": metal_type,
            "production_kg": production_kg,
            "recycled_fraction": recycled_fraction,
            "total_emissions_kg_co2e": full_results["formula_5_breakdown"]["total_net_emissions_kg_co2e"],
            "emission_intensity_kg_co2e_per_kg": full_results["formula_5_breakdown"]["emission_intensity_kg_co2e_per_kg"],
            "energy_consumption_kwh": full_results["energy_analysis"]["total_energy_consumption_kwh"],
            "circularity_index": full_results["key_performance_indicators"]["circularity_index"],
            "recycling_benefit_percent": full_results["route_comparison"]["recycling_emission_reduction_percent"],
            "calculation_timestamp": full_results["lca_metadata"]["calculation_timestamp"]
        }
        
    except Exception as e:
        return {"error": str(e), "function": "quick_lca_calculation"}

def get_emission_factors_summary() -> dict:
    """
    Get summary of all emission factors used in calculations
    
    Returns:
        dict: Summary of emission factors by category
    """
    
    return {
        "grid_emission_factors": {
            "description": "Grid emission factors by energy source (kg CO2e/kWh)",
            "factors": GRID_EMISSION_FACTORS
        },
        "transport_emission_factors": {
            "description": "Transport emission factors by mode (kg CO2e/t·km)",
            "factors": INDIA_TRANSPORT_EMISSION_FACTORS
        },
        "aluminum_energy_intensity": {
            "description": "Energy intensity by process (kWh/kg aluminum)",
            "factors": ALUMINUM_ENERGY_INTENSITY
        },
        "copper_energy_intensity": {
            "description": "Energy intensity by process (kWh/kg copper)",
            "factors": COPPER_ENERGY_INTENSITY
        },
        "gwp_values": {
            "description": "Global Warming Potential values (kg CO2e/kg gas)",
            "factors": GWP_VALUES
        }
    }

def validate_calculation_inputs(metal_type: str, 
                               production_kg: float, 
                               recycled_fraction: float,
                               region: str = "national_average",
                               scenario: str = "current_2024") -> tuple:
    """
    Comprehensive input validation for LCA calculations
    
    Args:
        metal_type (str): Metal type
        production_kg (float): Production quantity
        recycled_fraction (float): Recycled fraction
        region (str): Grid region
        scenario (str): Grid scenario
        
    Returns:
        tuple: (is_valid, list_of_errors)
    """
    
    errors = []
    
    # Validate metal type
    try:
        normalize_metal_type(metal_type)
    except ValueError as e:
        errors.append(str(e))
    
    # Validate production quantity
    is_valid, error = validate_production_quantity(production_kg)
    if not is_valid:
        errors.append(error)
    
    # Validate recycled fraction
    is_valid, error = validate_recycled_fraction(recycled_fraction)
    if not is_valid:
        errors.append(error)
    
    # Validate region
    if region not in VALIDATION_PATTERNS["region"]:
        errors.append(f"Invalid region: {region}. Must be one of {VALIDATION_PATTERNS['region']}")
    
    # Validate scenario
    if scenario not in VALIDATION_PATTERNS["scenario"]:
        errors.append(f"Invalid scenario: {scenario}. Must be one of {VALIDATION_PATTERNS['scenario']}")
    
    return len(errors) == 0, errors

def calculate_benchmark_comparison(metal_type: str, 
                                  production_kg: float,
                                  recycled_fraction: float) -> dict:
    """
    Compare results against industry benchmarks
    
    Args:
        metal_type (str): Metal type
        production_kg (float): Production quantity
        recycled_fraction (float): Recycled fraction
        
    Returns:
        dict: Benchmark comparison results
    """
    
    # Industry benchmarks (approximate values)
    benchmarks = {
        "aluminum": {
            "primary_emission_intensity": 11.5,      # kg CO2e/kg
            "secondary_emission_intensity": 0.6,      # kg CO2e/kg
            "energy_intensity_primary": 15.0,        # kWh/kg
            "energy_intensity_secondary": 1.0,       # kWh/kg
            "typical_recycled_content": 0.35         # 35%
        },
        "copper": {
            "primary_emission_intensity": 3.2,       # kg CO2e/kg
            "secondary_emission_intensity": 0.8,      # kg CO2e/kg
            "energy_intensity_primary": 4.0,         # kWh/kg
            "energy_intensity_secondary": 1.5,       # kWh/kg
            "typical_recycled_content": 0.42         # 42%
        }
    }
    
    try:
        metal_type = normalize_metal_type(metal_type)
        
        # Calculate actual performance
        results = quick_lca_calculation(metal_type, production_kg, recycled_fraction)
        
        if "error" in results:
            return results
        
        benchmark = benchmarks[metal_type]
        
        # Compare against benchmarks
        return {
            "metal_type": metal_type,
            "actual_performance": {
                "emission_intensity": results["emission_intensity_kg_co2e_per_kg"],
                "recycled_content": recycled_fraction * 100
            },
            "industry_benchmark": {
                "primary_emission_intensity": benchmark["primary_emission_intensity"],
                "secondary_emission_intensity": benchmark["secondary_emission_intensity"],
                "typical_recycled_content": benchmark["typical_recycled_content"] * 100
            },
            "performance_rating": {
                "emission_performance": "above_average" if results["emission_intensity_kg_co2e_per_kg"] < benchmark["primary_emission_intensity"] else "below_average",
                "recycling_performance": "above_average" if recycled_fraction > benchmark["typical_recycled_content"] else "below_average"
            },
            "improvement_potential": {
                "emission_reduction_kg_co2e_per_kg": max(0, results["emission_intensity_kg_co2e_per_kg"] - benchmark["secondary_emission_intensity"]),
                "recycled_content_increase_percent": max(0, benchmark["typical_recycled_content"] * 100 - recycled_fraction * 100)
            }
        }
        
    except Exception as e:
        return {"error": str(e), "function": "calculate_benchmark_comparison"}

# Export convenience functions for common use cases
def aluminum_lca(production_kg: float, recycled_fraction: float = 0.3) -> dict:
    """Simplified aluminum LCA calculation"""
    return quick_lca_calculation("aluminum", production_kg, recycled_fraction)

def copper_lca(production_kg: float, recycled_fraction: float = 0.4) -> dict:
    """Simplified copper LCA calculation"""
    return quick_lca_calculation("copper", production_kg, recycled_fraction)

# Package metadata and information
PACKAGE_INFO = {
    "name": "lca-tools",
    "version": __version__,
    "description": "Comprehensive LCA tools for metal industry carbon footprint analysis",
    "author": __author__,
    "supported_metals": ["aluminum", "copper"],
    "supported_regions": VALIDATION_PATTERNS["region"],
    "supported_scenarios": VALIDATION_PATTERNS["scenario"],
    "formulas_implemented": [
        "Formula 1: Process emissions (EI × EF(grid) + EF(direct))",
        "Formula 2: Grid emission factors (weighted electricity mix)",
        "Formula 3: Transport emissions (Weight × Distance × EF(transport))", 
        "Formula 4: Recycling and circularity metrics",
        "Formula 5: Total LCA (inventory-based full model)"
    ],
    "key_features": [
        "India-specific emission factors and energy data",
        "Regional grid electricity variations",
        "Comprehensive transport mode coverage",
        "Informal recycling sector integration",
        "Uncertainty analysis and confidence intervals",
        "Circularity and sustainability metrics",
        "ISO 14040/14044 compliant methodology"
    ]
}

def get_package_info() -> dict:
    """Get package information and capabilities"""
    return PACKAGE_INFO

# Define what gets imported with "from tools import *"
__all__ = [
    # Main calculation functions
    'calculate_total_lca_emissions',
    'quick_lca_calculation',
    'aluminum_lca',
    'copper_lca',
    
    # Individual formula functions
    'calculate_process_emissions',
    'calculate_grid_emission_factor',
    'calculate_transport_emissions',
    'calculate_circularity_metrics',
    
    # Comparison and analysis functions
    'compare_lca_scenarios',
    'compare_primary_vs_secondary',
    'compare_transport_modes',
    'compare_recycling_scenarios',
    
    # Utility functions
    'validate_calculation_inputs',
    'calculate_benchmark_comparison',
    'get_emission_factors_summary',
    'get_package_info',
    'normalize_metal_type',
    'convert_units',
    'format_lca_results',
    'export_results_to_json',
    
    # Constants and data
    'GRID_EMISSION_FACTORS',
    'INDIA_TRANSPORT_EMISSION_FACTORS',
    'ALUMINUM_ENERGY_INTENSITY',
    'COPPER_ENERGY_INTENSITY',
    'INDIA_RECYCLING_RATES',
    'GWP_VALUES',
    'PACKAGE_INFO'
]

# Initialize logging for the package
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())

# Package-level configuration
DEFAULT_CONFIG = {
    "precision": 4,                    # Decimal places for results
    "confidence_level": 0.95,          # Default confidence level for uncertainty analysis
    "default_region": "national_average",
    "default_scenario": "current_2024",
    "include_eol_credits": True,       # Include end-of-life recycling credits
    "system_boundary": "cradle_to_gate_with_eol_credits",
    "impact_method": "IPCC_AR5_GWP100"
}

def set_package_config(**kwargs) -> dict:
    """
    Update package-level configuration
    
    Args:
        **kwargs: Configuration parameters to update
        
    Returns:
        dict: Updated configuration
    """
    
    global DEFAULT_CONFIG
    
    for key, value in kwargs.items():
        if key in DEFAULT_CONFIG:
            DEFAULT_CONFIG[key] = value
        else:
            logging.warning(f"Unknown configuration parameter: {key}")
    
    return DEFAULT_CONFIG.copy()

def get_package_config() -> dict:
    """Get current package configuration"""
    return DEFAULT_CONFIG.copy()

# Version check function
def check_version() -> str:
    """Return current package version"""
    return f"LCA Tools Package v{__version__} by {__author__}"

# Package initialization message
if __name__ != "__main__":
    logging.info(f"LCA Tools Package v{__version__} loaded successfully")
    logging.info(f"Supported metals: {', '.join(PACKAGE_INFO['supported_metals'])}")
    logging.info(f"Ready for carbon footprint analysis")

# Example usage documentation
USAGE_EXAMPLES = {
    "quick_calculation": """
# Quick LCA calculation example
from tools import quick_lca_calculation

results = quick_lca_calculation(
    metal_type="aluminum",
    production_kg=1000.0,
    recycled_fraction=0.3,
    region="western"
)
print(f"Total emissions: {results['total_emissions_kg_co2e']:.2f} kg CO2e")
""",
    
    "detailed_analysis": """
# Detailed LCA analysis example
from tools import calculate_total_lca_emissions, compare_lca_scenarios

# Define scenarios
scenarios = {
    "current": {"recycled_fraction": 0.3, "grid_scenario": "current_2024"},
    "future": {"recycled_fraction": 0.5, "grid_scenario": "renewable_target_2030"}
}

# Compare scenarios
comparison = compare_lca_scenarios("aluminum", 1000.0, scenarios)
best_scenario = comparison["comparison_summary"]["best_scenario"]
print(f"Best scenario: {best_scenario}")
""",
    
    "transport_analysis": """
# Transport emission analysis example
from tools import compare_transport_modes

modes = ["truck_heavy", "rail_freight", "coastal_shipping"]
comparison = compare_transport_modes(100, 500, modes)
print(f"Best transport mode: {comparison['comparison']['best_mode']}")
""",
    
    "circularity_assessment": """
# Circularity assessment example
from tools import calculate_circularity_metrics

circularity = calculate_circularity_metrics(
    "aluminum", "beverage_cans", 0.3, "urban_tier1"
)
index = circularity["circularity_indicators"]["circularity_index"]
print(f"Circularity index: {index:.3f}")
"""
}

def show_usage_examples() -> None:
    """Display usage examples"""
    for example_name, code in USAGE_EXAMPLES.items():
        print(f"\n{example_name.upper()}:")
        print(code)