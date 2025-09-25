"""
Process Emission Calculation Tools
Implements Formula 1: EF(process) = EI × EF(grid) + EF(direct)
Covers aluminum and copper production processes with India-specific data
"""

from typing import Dict, Optional, Tuple
import logging
from .grid_emission_tools import calculate_grid_emission_factor, get_india_grid_ef
from .gwp_constants import convert_to_co2_eq, ALUMINUM_PROCESS_GASES, COPPER_PROCESS_GASES

# Energy Intensity Data (kWh/kg metal) - India specific where available
ALUMINUM_ENERGY_INTENSITY = {
    "bauxite_mining": 0.15,          # Mining and beneficiation
    "alumina_refining": 3.2,         # Bayer process (India average)
    "primary_smelting": 13.8,        # Hall-Héroult electrolysis (India average)
    "secondary_smelting": 0.85,      # Aluminum recycling/remelting
    "casting_rolling": 1.2,          # Semi-fabrication
    "extrusion": 1.8,               # Aluminum extrusion
    "sheet_rolling": 2.1             # Sheet and foil production
}

COPPER_ENERGY_INTENSITY = {
    "copper_mining": 0.8,            # Open pit and underground mining
    "concentration": 1.5,            # Flotation and concentration
    "smelting": 2.8,                # Pyrometallurgy (India average)
    "refining": 0.95,               # Electrorefining
    "secondary_smelting": 1.2,       # Copper scrap processing
    "wire_drawing": 0.6,            # Wire and cable production
    "tube_making": 0.8,             # Copper tubes and pipes
    "casting": 0.5                  # Copper casting
}

# Direct Process Emissions (kg CO2e/kg metal) - non-energy related
ALUMINUM_DIRECT_EMISSIONS = {
    "bauxite_mining": {
        "CO2": 0.02,                # Diesel equipment, explosives
        "CH4": 0.0001,             # Minimal methane from equipment
        "N2O": 0.000005            # Negligible N2O
    },
    "alumina_refining": {
        "CO2": 0.18,               # Limestone calcination in Bayer process
        "SO2": 0.002,              # Sulfur in bauxite (converted to CO2e elsewhere)
        "N2O": 0.00001            # Process emissions
    },
    "primary_smelting": {
        "CO2": 1.65,               # Carbon anode consumption (major source)
        "CF4": 0.0008,             # Anode effects (critical for aluminum)
        "C2F6": 0.00012,           # Anode effects
        "SO2": 0.001               # Sulfur in anodes
    },
    "secondary_smelting": {
        "CO2": 0.08,               # Fuel combustion, flux use
        "CH4": 0.00005,           # Organic contamination burning
        "N2O": 0.000002           # Minimal process emissions
    }
}

COPPER_DIRECT_EMISSIONS = {
    "copper_mining": {
        "CO2": 0.12,               # Diesel equipment, explosives
        "CH4": 0.0002,            # Equipment emissions
        "N2O": 0.000008           # Explosives
    },
    "concentration": {
        "CO2": 0.05,              # Flotation chemicals, lime
        "SO2": 0.015,             # Sulfide oxidation
        "N2O": 0.000003          # Minimal
    },
    "smelting": {
        "CO2": 0.85,              # Major source - flux, fuel combustion
        "SO2": 1.2,               # Sulfur in concentrate (major environmental concern)
        "N2O": 0.0001            # High temperature processes
    },
    "refining": {
        "CO2": 0.15,              # Electrolyte preparation
        "SO2": 0.02,              # Residual sulfur
        "N2O": 0.00005           # Nitric acid use (minor)
    },
    "secondary_smelting": {
        "CO2": 0.18,              # Fuel, flux use
        "SO2": 0.08,              # Impurities in scrap
        "CH4": 0.00008,          # Organic burning
        "N2O": 0.000003          # Minimal
    }
}

def calculate_process_emissions(process_name: str, 
                              metal_type: str,
                              production_kg: float,
                              electricity_mix: Optional[Dict[str, float]] = None,
                              region: str = "national_average",
                              scenario: str = "current_2024",
                              custom_energy_intensity: Optional[float] = None,
                              custom_direct_emissions: Optional[Dict[str, float]] = None) -> Dict[str, float]:
    """
    Calculate total process emissions using Formula 1
    
    EF(process) = EI × EF(grid) + EF(direct)
    
    Args:
        process_name (str): Name of the process (e.g., "primary_smelting")
        metal_type (str): "aluminum" or "copper"
        production_kg (float): Production quantity in kg
        electricity_mix (Dict, optional): Custom electricity mix
        region (str): Indian grid region
        scenario (str): Time scenario for grid mix
        custom_energy_intensity (float, optional): Override default energy intensity
        custom_direct_emissions (Dict, optional): Override default direct emissions
        
    Returns:
        Dict[str, float]: Detailed emissions breakdown
    """
    
    # Get energy intensity data
    if metal_type.lower() == "aluminum":
        energy_data = ALUMINUM_ENERGY_INTENSITY
        direct_data = ALUMINUM_DIRECT_EMISSIONS
    elif metal_type.lower() == "copper":
        energy_data = COPPER_ENERGY_INTENSITY
        direct_data = COPPER_DIRECT_EMISSIONS
    else:
        raise ValueError(f"Unsupported metal type: {metal_type}")
    
    # Get process-specific energy intensity
    if custom_energy_intensity:
        energy_intensity = custom_energy_intensity
    elif process_name in energy_data:
        energy_intensity = energy_data[process_name]
    else:
        raise ValueError(f"Unknown process '{process_name}' for {metal_type}")
    
    # Calculate grid emission factor
    if electricity_mix:
        grid_ef = calculate_grid_emission_factor(electricity_mix)
    else:
        grid_ef = get_india_grid_ef(region, scenario)
    
    # Calculate electricity-based emissions
    electricity_emissions = energy_intensity * grid_ef * production_kg
    
    # Get direct process emissions
    if custom_direct_emissions:
        process_gases = custom_direct_emissions
    elif process_name in direct_data:
        process_gases = direct_data[process_name]
    else:
        process_gases = {}
        logging.warning(f"No direct emissions data for process '{process_name}'")
    
    # Convert process gases to CO2 equivalent
    process_emissions_kg = {gas: amount * production_kg for gas, amount in process_gases.items()}
    direct_emissions = convert_to_co2_eq(process_emissions_kg) if process_emissions_kg else 0.0
    
    # Total emissions
    total_emissions = electricity_emissions + direct_emissions
    
    return {
        "process": process_name,
        "metal_type": metal_type,
        "production_kg": production_kg,
        "energy_intensity_kwh_per_kg": energy_intensity,
        "grid_ef_kg_co2e_per_kwh": grid_ef,
        "electricity_emissions_kg_co2e": electricity_emissions,
        "direct_emissions_kg_co2e": direct_emissions,
        "total_emissions_kg_co2e": total_emissions,
        "emission_intensity_kg_co2e_per_kg": total_emissions / production_kg if production_kg > 0 else 0,
        "process_gas_breakdown": process_emissions_kg
    }

def calculate_production_chain_emissions(metal_type: str,
                                       production_kg: float,
                                       processes: list,
                                       electricity_mix: Optional[Dict[str, float]] = None,
                                       region: str = "national_average",
                                       scenario: str = "current_2024") -> Dict[str, any]:
    """
    Calculate emissions for entire production chain
    
    Args:
        metal_type (str): "aluminum" or "copper"
        production_kg (float): Final product quantity
        processes (list): List of processes in production chain
        electricity_mix (Dict, optional): Custom electricity mix
        region (str): Indian grid region
        scenario (str): Time scenario
        
    Returns:
        Dict: Chain-level emissions analysis
    """
    
    chain_results = []
    total_chain_emissions = 0.0
    total_energy_consumption = 0.0
    
    for process in processes:
        try:
            result = calculate_process_emissions(
                process, metal_type, production_kg,
                electricity_mix, region, scenario
            )
            chain_results.append(result)
            total_chain_emissions += result["total_emissions_kg_co2e"]
            total_energy_consumption += result["energy_intensity_kwh_per_kg"] * production_kg
            
        except ValueError as e:
            logging.error(f"Error calculating emissions for process '{process}': {e}")
            continue
    
    return {
        "metal_type": metal_type,
        "production_kg": production_kg,
        "processes": processes,
        "process_results": chain_results,
        "total_chain_emissions_kg_co2e": total_chain_emissions,
        "total_energy_consumption_kwh": total_energy_consumption,
        "chain_emission_intensity_kg_co2e_per_kg": total_chain_emissions / production_kg if production_kg > 0 else 0,
        "energy_intensity_kwh_per_kg": total_energy_consumption / production_kg if production_kg > 0 else 0,
        "grid_scenario": {"region": region, "scenario": scenario}
    }

def compare_primary_vs_secondary(metal_type: str,
                                production_kg: float,
                                electricity_mix: Optional[Dict[str, float]] = None,
                                region: str = "national_average",
                                scenario: str = "current_2024") -> Dict[str, any]:
    """
    Compare primary vs secondary production emissions
    
    Args:
        metal_type (str): "aluminum" or "copper"
        production_kg (float): Production quantity
        electricity_mix (Dict, optional): Custom electricity mix
        region (str): Indian grid region
        scenario (str): Time scenario
        
    Returns:
        Dict: Comparison analysis
    """
    
    if metal_type.lower() == "aluminum":
        primary_processes = ["bauxite_mining", "alumina_refining", "primary_smelting"]
        secondary_processes = ["secondary_smelting"]
    elif metal_type.lower() == "copper":
        primary_processes = ["copper_mining", "concentration", "smelting", "refining"]
        secondary_processes = ["secondary_smelting"]
    else:
        raise ValueError(f"Unsupported metal type: {metal_type}")
    
    primary_results = calculate_production_chain_emissions(
        metal_type, production_kg, primary_processes, electricity_mix, region, scenario
    )
    
    secondary_results = calculate_production_chain_emissions(
        metal_type, production_kg, secondary_processes, electricity_mix, region, scenario
    )
    
    # Calculate savings
    emission_savings = primary_results["total_chain_emissions_kg_co2e"] - secondary_results["total_chain_emissions_kg_co2e"]
    energy_savings = primary_results["total_energy_consumption_kwh"] - secondary_results["total_energy_consumption_kwh"]
    
    return {
        "metal_type": metal_type,
        "production_kg": production_kg,
        "primary_route": primary_results,
        "secondary_route": secondary_results,
        "savings": {
            "emission_savings_kg_co2e": emission_savings,
            "emission_reduction_percentage": (emission_savings / primary_results["total_chain_emissions_kg_co2e"]) * 100,
            "energy_savings_kwh": energy_savings,
            "energy_reduction_percentage": (energy_savings / primary_results["total_energy_consumption_kwh"]) * 100
        }
    }

def sensitivity_analysis_energy_intensity(process_name: str,
                                        metal_type: str,
                                        production_kg: float,
                                        variation_percent: float = 20.0,
                                        region: str = "national_average") -> Dict[str, float]:
    """
    Perform sensitivity analysis on energy intensity parameter
    
    Args:
        process_name (str): Process to analyze
        metal_type (str): "aluminum" or "copper"
        production_kg (float): Production quantity
        variation_percent (float): Percentage variation to test (±%)
        region (str): Indian grid region
        
    Returns:
        Dict: Sensitivity analysis results
    """
    
    # Base case
    base_result = calculate_process_emissions(process_name, metal_type, production_kg, region=region)
    base_emissions = base_result["total_emissions_kg_co2e"]
    base_energy = base_result["energy_intensity_kwh_per_kg"]
    
    # High case (+variation%)
    high_energy = base_energy * (1 + variation_percent / 100)
    high_result = calculate_process_emissions(
        process_name, metal_type, production_kg, 
        custom_energy_intensity=high_energy, region=region
    )
    
    # Low case (-variation%)
    low_energy = base_energy * (1 - variation_percent / 100)
    low_result = calculate_process_emissions(
        process_name, metal_type, production_kg,
        custom_energy_intensity=low_energy, region=region
    )
    
    return {
        "parameter": "energy_intensity",
        "variation_percent": variation_percent,
        "base_emissions_kg_co2e": base_emissions,
        "high_case_emissions_kg_co2e": high_result["total_emissions_kg_co2e"],
        "low_case_emissions_kg_co2e": low_result["total_emissions_kg_co2e"],
        "sensitivity_kg_co2e_per_percent": (high_result["total_emissions_kg_co2e"] - low_result["total_emissions_kg_co2e"]) / (2 * variation_percent),
        "sensitivity_relative": ((high_result["total_emissions_kg_co2e"] - low_result["total_emissions_kg_co2e"]) / base_emissions) * 100 / (2 * variation_percent)
    }

# Validation and testing
if __name__ == "__main__":
    # Test aluminum primary smelting
    al_result = calculate_process_emissions("primary_smelting", "aluminum", 1000.0)
    print(f"Aluminum Primary Smelting (1000 kg): {al_result['total_emissions_kg_co2e']:.2f} kg CO2e")
    print(f"Emission Intensity: {al_result['emission_intensity_kg_co2e_per_kg']:.4f} kg CO2e/kg Al")
    
    # Test primary vs secondary comparison
    comparison = compare_primary_vs_secondary("aluminum", 1000.0)
    print(f"\nPrimary vs Secondary Aluminum:")
    print(f"Primary: {comparison['primary_route']['chain_emission_intensity_kg_co2e_per_kg']:.4f} kg CO2e/kg")
    print(f"Secondary: {comparison['secondary_route']['chain_emission_intensity_kg_co2e_per_kg']:.4f} kg CO2e/kg")
    print(f"Reduction: {comparison['savings']['emission_reduction_percentage']:.1f}%")
    
    # Test sensitivity analysis
    sensitivity = sensitivity_analysis_energy_intensity("primary_smelting", "aluminum", 1000.0)
    print(f"\nSensitivity Analysis (±20% energy intensity):")
    print(f"Sensitivity: {sensitivity['sensitivity_relative']:.2f}% change in emissions per 1% change in energy intensity")