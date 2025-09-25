"""
Grid Emission Factor Calculation Tools
Implements Formula 2: Weighted average grid emission factors for different electricity mixes
Focused on India's grid composition with regional and temporal variations
"""

from typing import Dict, Optional
import logging

# India Grid Emission Factors by Source (kg CO2e/kWh)
# Based on IPCC lifecycle assessments and India-specific studies
GRID_EMISSION_FACTORS = {
    "coal": 0.82,      # Thermal coal power plants
    "gas": 0.49,       # Natural gas combined cycle
    "oil": 0.65,       # Oil-fired thermal plants
    "nuclear": 0.012,  # Nuclear power lifecycle
    "hydro": 0.024,    # Hydroelectric lifecycle
    "wind": 0.011,     # Wind power lifecycle
    "solar": 0.045,    # Solar PV lifecycle (includes manufacturing)
    "other": 0.1       # Biomass, waste-to-energy, etc.
}

# India Regional Grid Mix (2023-24 data) - percentages
INDIA_REGIONAL_GRIDS = {
    "national_average": {
        "coal": 70.2,
        "gas": 2.8,
        "oil": 0.1,
        "nuclear": 3.1,
        "hydro": 12.4,
        "wind": 7.8,
        "solar": 3.2,
        "other": 0.4
    },
    "northern": {
        "coal": 65.5,
        "gas": 4.2,
        "oil": 0.1,
        "nuclear": 4.8,
        "hydro": 15.2,
        "wind": 6.1,
        "solar": 3.8,
        "other": 0.3
    },
    "western": {
        "coal": 68.9,
        "gas": 6.1,
        "oil": 0.2,
        "nuclear": 5.2,
        "hydro": 8.3,
        "wind": 7.4,
        "solar": 3.6,
        "other": 0.3
    },
    "southern": {
        "coal": 62.4,
        "gas": 2.1,
        "oil": 0.1,
        "nuclear": 7.8,
        "hydro": 18.2,
        "wind": 6.9,
        "solar": 2.2,
        "other": 0.3
    },
    "eastern": {
        "coal": 78.5,
        "gas": 1.2,
        "oil": 0.1,
        "nuclear": 1.8,
        "hydro": 12.1,
        "wind": 4.2,
        "solar": 1.8,
        "other": 0.3
    },
    "northeastern": {
        "coal": 45.2,
        "gas": 15.8,
        "oil": 2.1,
        "nuclear": 0.0,
        "hydro": 32.4,
        "wind": 2.1,
        "solar": 1.8,
        "other": 0.6
    }
}

# Future scenario projections for India (2030 renewable targets)
INDIA_FUTURE_SCENARIOS = {
    "current_2024": INDIA_REGIONAL_GRIDS["national_average"],
    "renewable_target_2030": {
        "coal": 55.0,     # Reduced coal dependence
        "gas": 8.0,       # Increased gas for flexibility
        "oil": 0.1,
        "nuclear": 4.5,
        "hydro": 12.0,
        "wind": 12.0,     # Significant wind expansion
        "solar": 8.0,     # Major solar deployment
        "other": 0.4
    },
    "ambitious_2030": {
        "coal": 45.0,     # Aggressive coal reduction
        "gas": 10.0,
        "oil": 0.1,
        "nuclear": 6.0,
        "hydro": 13.0,
        "wind": 15.0,     # Very high renewable penetration
        "solar": 10.5,
        "other": 0.4
    }
}

def calculate_grid_emission_factor(electricity_mix: Dict[str, float], 
                                 custom_factors: Optional[Dict[str, float]] = None) -> float:
    """
    Calculate grid emission factor using Formula 2
    
    EF(grid) = [(coal% * 0.82) + (gas% * 0.49) + ... + (solar% * 0.045)] / 100
    
    Args:
        electricity_mix (Dict[str, float]): Percentage share of each energy source
        custom_factors (Dict[str, float], optional): Custom emission factors to override defaults
        
    Returns:
        float: Grid emission factor in kg CO2e/kWh
        
    Raises:
        ValueError: If percentages don't sum to ~100% or invalid sources
    """
    # Use custom factors if provided, otherwise use defaults
    factors = custom_factors if custom_factors else GRID_EMISSION_FACTORS
    
    # Validate input
    total_percentage = sum(electricity_mix.values())
    if not (99.0 <= total_percentage <= 101.0):  # Allow small rounding errors
        logging.warning(f"Electricity mix percentages sum to {total_percentage}%, not 100%")
    
    # Check for unknown sources
    unknown_sources = set(electricity_mix.keys()) - set(factors.keys())
    if unknown_sources:
        raise ValueError(f"Unknown electricity sources: {unknown_sources}")
    
    # Calculate weighted emission factor
    weighted_ef = 0.0
    for source, percentage in electricity_mix.items():
        if source in factors:
            weighted_ef += (percentage * factors[source]) / 100
        else:
            logging.warning(f"No emission factor found for source: {source}")
    
    return round(weighted_ef, 6)  # Round to 6 decimal places

def get_india_grid_ef(region: str = "national_average", 
                     scenario: str = "current_2024") -> float:
    """
    Get pre-calculated grid emission factor for Indian regions/scenarios
    
    Args:
        region (str): Indian grid region or "national_average"
        scenario (str): Time scenario - "current_2024", "renewable_target_2030", "ambitious_2030"
        
    Returns:
        float: Grid emission factor in kg CO2e/kWh
    """
    if scenario in INDIA_FUTURE_SCENARIOS:
        mix = INDIA_FUTURE_SCENARIOS[scenario]
    elif region in INDIA_REGIONAL_GRIDS:
        mix = INDIA_REGIONAL_GRIDS[region]
    else:
        raise ValueError(f"Unknown region '{region}' or scenario '{scenario}'")
    
    return calculate_grid_emission_factor(mix)

def compare_grid_scenarios(scenarios: list, region: str = "national_average") -> Dict[str, float]:
    """
    Compare grid emission factors across different scenarios
    
    Args:
        scenarios (list): List of scenario names to compare
        region (str): Region to analyze
        
    Returns:
        Dict[str, float]: Dictionary of scenario: emission_factor pairs
    """
    results = {}
    
    for scenario in scenarios:
        try:
            ef = get_india_grid_ef(region, scenario)
            results[scenario] = ef
        except ValueError as e:
            logging.error(f"Error calculating EF for scenario '{scenario}': {e}")
            results[scenario] = None
    
    return results

def get_renewable_share(electricity_mix: Dict[str, float]) -> float:
    """
    Calculate renewable energy share from electricity mix
    
    Args:
        electricity_mix (Dict[str, float]): Percentage share of each energy source
        
    Returns:
        float: Renewable share as percentage
    """
    renewable_sources = ["hydro", "wind", "solar", "other"]  # Assuming 'other' includes renewables
    renewable_share = sum(electricity_mix.get(source, 0) for source in renewable_sources)
    
    return round(renewable_share, 2)

def grid_decarbonization_impact(base_mix: Dict[str, float], 
                              target_mix: Dict[str, float]) -> Dict[str, float]:
    """
    Calculate emission reduction from grid decarbonization
    
    Args:
        base_mix (Dict[str, float]): Current electricity mix
        target_mix (Dict[str, float]): Target electricity mix
        
    Returns:
        Dict[str, float]: Impact analysis results
    """
    base_ef = calculate_grid_emission_factor(base_mix)
    target_ef = calculate_grid_emission_factor(target_mix)
    
    base_renewable = get_renewable_share(base_mix)
    target_renewable = get_renewable_share(target_mix)
    
    return {
        "base_ef_kg_co2e_per_kwh": base_ef,
        "target_ef_kg_co2e_per_kwh": target_ef,
        "ef_reduction_kg_co2e_per_kwh": base_ef - target_ef,
        "ef_reduction_percentage": ((base_ef - target_ef) / base_ef) * 100,
        "base_renewable_share_percent": base_renewable,
        "target_renewable_share_percent": target_renewable,
        "renewable_increase_percent": target_renewable - base_renewable
    }

# Validation and testing
if __name__ == "__main__":
    # Test with India national average
    national_ef = get_india_grid_ef("national_average", "current_2024")
    print(f"India National Grid EF (2024): {national_ef:.4f} kg CO2e/kWh")
    
    # Test future scenarios
    scenarios = ["current_2024", "renewable_target_2030", "ambitious_2030"]
    comparison = compare_grid_scenarios(scenarios)
    print("\nGrid EF Scenario Comparison:")
    for scenario, ef in comparison.items():
        if ef:
            print(f"  {scenario}: {ef:.4f} kg CO2e/kWh")
    
    # Test decarbonization impact
    current_mix = INDIA_FUTURE_SCENARIOS["current_2024"]
    target_mix = INDIA_FUTURE_SCENARIOS["ambitious_2030"]
    impact = grid_decarbonization_impact(current_mix, target_mix)
    print(f"\nDecarbonization Impact: {impact['ef_reduction_percentage']:.1f}% reduction")