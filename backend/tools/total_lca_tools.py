"""
Total LCA Calculation Tools
Implements Formula 5: Final inventory-based full model for total product emissions
Integrates all previous formulas into comprehensive LCA results
"""

from typing import Dict, List, Optional, Tuple, Any
import logging
import math
from .process_emission_tools import (
    calculate_process_emissions, 
    calculate_production_chain_emissions,
    ALUMINUM_ENERGY_INTENSITY,
    COPPER_ENERGY_INTENSITY
)
from .transport_tools import calculate_transport_emissions, calculate_multimodal_transport
from .recycling_tools import (
    calculate_circularity_metrics,
    calculate_effective_product_emission_factor,
    RECYCLING_ENERGY_EFFICIENCY
)
from .grid_emission_tools import get_india_grid_ef
from .gwp_constants import convert_to_co2_eq

# Standard production routes and their processes
STANDARD_PRODUCTION_ROUTES = {
    "aluminum": {
        "primary_route": [
            "bauxite_mining",
            "alumina_refining", 
            "primary_smelting",
            "casting_rolling"
        ],
        "secondary_route": [
            "secondary_smelting",
            "casting_rolling"
        ],
        "semi_fabrication": {
            "extrusion": ["extrusion"],
            "sheet_rolling": ["sheet_rolling"],
            "foil_production": ["sheet_rolling"]  # Simplified
        }
    },
    "copper": {
        "primary_route": [
            "copper_mining",
            "concentration",
            "smelting",
            "refining"
        ],
        "secondary_route": [
            "secondary_smelting"
        ],
        "semi_fabrication": {
            "wire_drawing": ["wire_drawing"],
            "tube_making": ["tube_making"],
            "casting": ["casting"]
        }
    }
}

# Typical transport distances for different stages (km)
TYPICAL_TRANSPORT_DISTANCES = {
    "aluminum": {
        "mine_to_refinery": 150,
        "refinery_to_smelter": 400,
        "smelter_to_semis": 300,
        "semis_to_customer": 250,
        "scrap_collection": 100,
        "scrap_to_recycler": 200
    },
    "copper": {
        "mine_to_concentrator": 50,
        "concentrator_to_smelter": 300,
        "smelter_to_refinery": 150,
        "refinery_to_semis": 250,
        "semis_to_customer": 200,
        "scrap_collection": 80,
        "scrap_to_recycler": 150
    }
}

def calculate_total_lca_emissions(metal_type: str,
                                production_kg: float,
                                recycled_fraction: float,
                                product_type: str = "generic",
                                region: str = "national_average",
                                scenario: str = "current_2024",
                                transport_config: Optional[Dict] = None,
                                custom_processes: Optional[Dict] = None,
                                include_eol_credit: bool = True,
                                system_boundary: str = "cradle_to_gate") -> Dict[str, Any]:
    """
    Calculate total LCA emissions using Formula 5 - Inventory based full model
    
    Total CO2e = (1-r) × (Elec(p) × EF(grid) + tkm × EF(transport) + ProcessGases(p) + Other(p)) + 
                 r × (Elec(s) × EF(grid) + tkm × EF(transport) + ProcessGases(s) + Others(s))
    
    Args:
        metal_type (str): "aluminum" or "copper"
        production_kg (float): Production quantity in kg
        recycled_fraction (float): Fraction recycled (0-1), corresponds to 'r' in formula
        product_type (str): Specific product type for circularity analysis
        region (str): Indian grid region
        scenario (str): Grid scenario (current_2024, renewable_target_2030, etc.)
        transport_config (Dict, optional): Custom transport configuration
        custom_processes (Dict, optional): Custom process configurations
        include_eol_credit (bool): Include end-of-life recycling credits
        system_boundary (str): LCA system boundary
        
    Returns:
        Dict: Comprehensive LCA results with all emission components
    """
    
    # Validate inputs
    if metal_type.lower() not in ["aluminum", "copper"]:
        raise ValueError(f"Unsupported metal type: {metal_type}")
    
    if not 0 <= recycled_fraction <= 1:
        raise ValueError(f"Recycled fraction must be between 0 and 1, got {recycled_fraction}")
    
    # Get production routes
    routes = STANDARD_PRODUCTION_ROUTES[metal_type.lower()]
    primary_processes = custom_processes.get("primary", routes["primary_route"]) if custom_processes else routes["primary_route"]
    secondary_processes = custom_processes.get("secondary", routes["secondary_route"]) if custom_processes else routes["secondary_route"]
    
    # Calculate primary route emissions (1-r) term
    primary_fraction = 1.0 - recycled_fraction
    primary_production_kg = production_kg * primary_fraction
    
    primary_results = {}
    if primary_production_kg > 0:
        primary_results = calculate_production_chain_emissions(
            metal_type, primary_production_kg, primary_processes, 
            region=region, scenario=scenario
        )
    
    # Calculate secondary route emissions (r) term  
    secondary_production_kg = production_kg * recycled_fraction
    
    secondary_results = {}
    if secondary_production_kg > 0:
        secondary_results = calculate_production_chain_emissions(
            metal_type, secondary_production_kg, secondary_processes,
            region=region, scenario=scenario
        )
    
    # Calculate transport emissions (tkm × EF(transport))
    transport_emissions = calculate_transport_emissions_for_lca(
        metal_type, production_kg, recycled_fraction, transport_config
    )
    
    # Calculate total emissions by component
    primary_total = primary_results.get("total_chain_emissions_kg_co2e", 0.0)
    secondary_total = secondary_results.get("total_chain_emissions_kg_co2e", 0.0)
    transport_total = transport_emissions.get("total_transport_emissions_kg_co2e", 0.0)
    
    # Total emissions before end-of-life credits
    total_emissions_pre_eol = primary_total + secondary_total + transport_total
    
    # Calculate end-of-life credits if enabled
    eol_credits = 0.0
    circularity_results = {}
    
    if include_eol_credit:
        try:
            circularity_results = calculate_circularity_metrics(
                metal_type, product_type, recycled_fraction, region
            )
            
            # Calculate avoided burden from future recycling
            if circularity_results:
                avoided_impact = circularity_results["formula_4_results"]["avoided_virgin_impact_kg_co2e_per_kg"]
                eol_credits = avoided_impact * production_kg
        except Exception as e:
            logging.warning(f"Could not calculate end-of-life credits: {e}")
    
    # Final total emissions
    total_emissions_net = total_emissions_pre_eol - eol_credits
    
    # Calculate additional metrics and breakdowns
    emission_intensity = total_emissions_net / production_kg if production_kg > 0 else 0
    
    # Energy consumption breakdown
    primary_energy = primary_results.get("total_energy_consumption_kwh", 0.0)
    secondary_energy = secondary_results.get("total_energy_consumption_kwh", 0.0)
    total_energy = primary_energy + secondary_energy
    
    # Emission source breakdown
    grid_ef = get_india_grid_ef(region, scenario)
    electricity_emissions = total_energy * grid_ef
    
    # Process gas emissions (from direct emissions in process calculations)
    process_gas_emissions = 0.0
    if primary_results.get("process_results"):
        for process in primary_results["process_results"]:
            process_gas_emissions += process.get("direct_emissions_kg_co2e", 0.0)
    
    if secondary_results.get("process_results"):
        for process in secondary_results["process_results"]:
            process_gas_emissions += process.get("direct_emissions_kg_co2e", 0.0)
    
    # Calculate environmental impact categories (simplified)
    impact_categories = calculate_impact_categories(
        total_emissions_net, metal_type, production_kg
    )
    
    # Uncertainty analysis (simplified)
    uncertainty_analysis = calculate_uncertainty_metrics(
        primary_total, secondary_total, transport_total, recycled_fraction
    )
    
    return {
        "lca_metadata": {
            "metal_type": metal_type,
            "production_kg": production_kg,
            "recycled_fraction": recycled_fraction,
            "product_type": product_type,
            "region": region,
            "scenario": scenario,
            "system_boundary": system_boundary,
            "functional_unit": f"1 kg {metal_type}",
            "methodology": "ISO 14040/14044 compliant"
        },
        
        "formula_5_breakdown": {
            "primary_route_emissions_kg_co2e": primary_total,
            "secondary_route_emissions_kg_co2e": secondary_total,
            "transport_emissions_kg_co2e": transport_total,
            "total_pre_eol_kg_co2e": total_emissions_pre_eol,
            "eol_credits_kg_co2e": eol_credits,
            "total_net_emissions_kg_co2e": total_emissions_net,
            "emission_intensity_kg_co2e_per_kg": emission_intensity
        },
        
        "emission_source_breakdown": {
            "electricity_emissions_kg_co2e": electricity_emissions,
            "process_gas_emissions_kg_co2e": process_gas_emissions,
            "transport_emissions_kg_co2e": transport_total,
            "eol_credits_kg_co2e": -eol_credits,  # Negative for credits
            "total_kg_co2e": total_emissions_net
        },
        
        "energy_analysis": {
            "primary_route_energy_kwh": primary_energy,
            "secondary_route_energy_kwh": secondary_energy,
            "total_energy_consumption_kwh": total_energy,
            "energy_intensity_kwh_per_kg": total_energy / production_kg if production_kg > 0 else 0,
            "grid_emission_factor_kg_co2e_per_kwh": grid_ef,
            "energy_savings_from_recycling_kwh": (primary_energy / primary_fraction - secondary_energy / recycled_fraction) * recycled_fraction if recycled_fraction > 0 and primary_fraction > 0 else 0
        },
        
        "route_comparison": {
            "primary_route_intensity_kg_co2e_per_kg": primary_total / primary_production_kg if primary_production_kg > 0 else 0,
            "secondary_route_intensity_kg_co2e_per_kg": secondary_total / secondary_production_kg if secondary_production_kg > 0 else 0,
            "recycling_benefit_kg_co2e_per_kg": (primary_total / primary_production_kg - secondary_total / secondary_production_kg) if primary_production_kg > 0 and secondary_production_kg > 0 else 0,
            "recycling_emission_reduction_percent": ((primary_total / primary_production_kg - secondary_total / secondary_production_kg) / (primary_total / primary_production_kg)) * 100 if primary_production_kg > 0 and secondary_production_kg > 0 else 0
        },
        
        "detailed_results": {
            "primary_route_details": primary_results,
            "secondary_route_details": secondary_results,
            "transport_details": transport_emissions,
            "circularity_details": circularity_results
        },
        
        "impact_categories": impact_categories,
        "uncertainty_analysis": uncertainty_analysis,
        
        "key_performance_indicators": {
            "carbon_footprint_kg_co2e": total_emissions_net,
            "carbon_intensity_kg_co2e_per_kg": emission_intensity,
            "renewable_energy_share_percent": get_renewable_energy_share(region, scenario),
            "circularity_index": circularity_results.get("circularity_indicators", {}).get("circularity_index", 0),
            "resource_efficiency_score": calculate_resource_efficiency_score(recycled_fraction, total_energy, production_kg),
            "environmental_benefit_from_recycling_kg_co2e": eol_credits
        }
    }

def calculate_transport_emissions_for_lca(metal_type: str,
                                        production_kg: float, 
                                        recycled_fraction: float,
                                        transport_config: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Calculate transport emissions for LCA including primary and secondary routes
    
    Args:
        metal_type (str): "aluminum" or "copper"
        production_kg (float): Total production quantity
        recycled_fraction (float): Fraction from recycling
        transport_config (Dict, optional): Custom transport configuration
        
    Returns:
        Dict: Transport emissions breakdown
    """
    
    # Get default distances and modes
    distances = TYPICAL_TRANSPORT_DISTANCES[metal_type.lower()]
    
    # Override with custom config if provided
    if transport_config:
        distances.update(transport_config.get("distances", {}))
    
    default_transport_mode = transport_config.get("default_mode", "truck_heavy") if transport_config else "truck_heavy"
    
    transport_results = []
    total_emissions = 0.0
    
    # Primary route transport
    primary_kg = production_kg * (1 - recycled_fraction)
    if primary_kg > 0:
        primary_legs = [
            {"description": "Mine to refinery", "distance": distances.get("mine_to_refinery", 150), "weight": primary_kg},
            {"description": "Refinery to smelter", "distance": distances.get("refinery_to_smelter", 400), "weight": primary_kg},
            {"description": "Smelter to semis", "distance": distances.get("smelter_to_semis", 300), "weight": primary_kg},
            {"description": "Semis to customer", "distance": distances.get("semis_to_customer", 250), "weight": primary_kg}
        ]
        
        for leg in primary_legs:
            result = calculate_transport_emissions(
                leg["weight"] / 1000,  # Convert to tonnes
                leg["distance"],
                default_transport_mode
            )
            result["route_type"] = "primary"
            result["leg_description"] = leg["description"]
            transport_results.append(result)
            total_emissions += result["total_emissions_kg_co2e"]
    
    # Secondary route transport
    secondary_kg = production_kg * recycled_fraction
    if secondary_kg > 0:
        secondary_legs = [
            {"description": "Scrap collection", "distance": distances.get("scrap_collection", 100), "weight": secondary_kg},
            {"description": "Scrap to recycler", "distance": distances.get("scrap_to_recycler", 200), "weight": secondary_kg},
            {"description": "Recycler to customer", "distance": distances.get("semis_to_customer", 250), "weight": secondary_kg}
        ]
        
        for leg in secondary_legs:
            result = calculate_transport_emissions(
                leg["weight"] / 1000,  # Convert to tonnes
                leg["distance"], 
                default_transport_mode
            )
            result["route_type"] = "secondary"
            result["leg_description"] = leg["description"]
            transport_results.append(result)
            total_emissions += result["total_emissions_kg_co2e"]
    
    return {
        "total_transport_emissions_kg_co2e": total_emissions,
        "transport_emission_intensity_kg_co2e_per_kg": total_emissions / production_kg if production_kg > 0 else 0,
        "primary_route_transport_kg_co2e": sum([r["total_emissions_kg_co2e"] for r in transport_results if r.get("route_type") == "primary"]),
        "secondary_route_transport_kg_co2e": sum([r["total_emissions_kg_co2e"] for r in transport_results if r.get("route_type") == "secondary"]),
        "transport_breakdown": transport_results,
        "transport_configuration": {
            "default_mode": default_transport_mode,
            "distances_used": distances
        }
    }

def calculate_impact_categories(total_co2e: float, 
                               metal_type: str, 
                               production_kg: float) -> Dict[str, float]:
    """
    Calculate additional LCIA impact categories (simplified characterization factors)
    
    Args:
        total_co2e (float): Total CO2 equivalent emissions
        metal_type (str): Metal type for category-specific factors
        production_kg (float): Production quantity
        
    Returns:
        Dict: Impact category results
    """
    
    # Simplified characterization factors (would normally use detailed LCIA methods)
    if metal_type.lower() == "aluminum":
        factors = {
            "acidification_so2_eq_per_kg_co2e": 0.008,      # kg SO2-eq per kg CO2-eq
            "eutrophication_po4_eq_per_kg_co2e": 0.0015,    # kg PO4-eq per kg CO2-eq
            "ozone_depletion_cfc11_eq_per_kg_co2e": 1.2e-8,  # kg CFC-11-eq per kg CO2-eq
            "water_consumption_m3_per_kg": 1.8,             # m3 per kg aluminum
            "land_use_m2_year_per_kg": 0.15                 # m2*year per kg aluminum
        }
    else:  # copper
        factors = {
            "acidification_so2_eq_per_kg_co2e": 0.012,      # Higher due to sulfur in copper ores
            "eutrophication_po4_eq_per_kg_co2e": 0.002,
            "ozone_depletion_cfc11_eq_per_kg_co2e": 0.8e-8,
            "water_consumption_m3_per_kg": 2.4,             # m3 per kg copper
            "land_use_m2_year_per_kg": 0.25                 # m2*year per kg copper
        }
    
    return {
        "climate_change_kg_co2_eq": total_co2e,
        "acidification_kg_so2_eq": total_co2e * factors["acidification_so2_eq_per_kg_co2e"],
        "eutrophication_kg_po4_eq": total_co2e * factors["eutrophication_po4_eq_per_kg_co2e"],
        "ozone_depletion_kg_cfc11_eq": total_co2e * factors["ozone_depletion_cfc11_eq_per_kg_co2e"],
        "water_consumption_m3": production_kg * factors["water_consumption_m3_per_kg"],
        "land_use_m2_year": production_kg * factors["land_use_m2_year_per_kg"]
    }

def calculate_uncertainty_metrics(primary_emissions: float,
                                secondary_emissions: float,
                                transport_emissions: float,
                                recycled_fraction: float) -> Dict[str, float]:
    """
    Calculate uncertainty metrics for LCA results (simplified Monte Carlo approach)
    
    Args:
        primary_emissions (float): Primary route emissions
        secondary_emissions (float): Secondary route emissions  
        transport_emissions (float): Transport emissions
        recycled_fraction (float): Recycled content fraction
        
    Returns:
        Dict: Uncertainty analysis results
    """
    
    # Typical uncertainty ranges for different emission sources (coefficient of variation)
    uncertainty_factors = {
        "primary_route_cv": 0.15,      # 15% coefficient of variation
        "secondary_route_cv": 0.20,    # 20% CV (higher uncertainty for recycling data)
        "transport_cv": 0.10,          # 10% CV (transport relatively well known)
        "recycled_fraction_cv": 0.05   # 5% CV (composition usually well known)
    }
    
    # Calculate individual variances
    primary_variance = (primary_emissions * uncertainty_factors["primary_route_cv"]) ** 2
    secondary_variance = (secondary_emissions * uncertainty_factors["secondary_route_cv"]) ** 2
    transport_variance = (transport_emissions * uncertainty_factors["transport_cv"]) ** 2
    
    # Total variance (assuming independence)
    total_variance = primary_variance + secondary_variance + transport_variance
    total_std_dev = math.sqrt(total_variance)
    
    # Total emissions
    total_emissions = primary_emissions + secondary_emissions + transport_emissions
    
    # Confidence intervals (assuming normal distribution)
    confidence_95_lower = total_emissions - (1.96 * total_std_dev)
    confidence_95_upper = total_emissions + (1.96 * total_std_dev)
    
    return {
        "total_emissions_kg_co2e": total_emissions,
        "standard_deviation_kg_co2e": total_std_dev,
        "coefficient_of_variation": total_std_dev / total_emissions if total_emissions > 0 else 0,
        "confidence_95_percent_lower_kg_co2e": max(0, confidence_95_lower),  # Cannot be negative
        "confidence_95_percent_upper_kg_co2e": confidence_95_upper,
        "relative_uncertainty_percent": (total_std_dev / total_emissions) * 100 if total_emissions > 0 else 0,
        "uncertainty_breakdown": {
            "primary_route_std_dev": math.sqrt(primary_variance),
            "secondary_route_std_dev": math.sqrt(secondary_variance),
            "transport_std_dev": math.sqrt(transport_variance)
        }
    }

def get_renewable_energy_share(region: str, scenario: str) -> float:
    """
    Get renewable energy share for given region and scenario
    
    Args:
        region (str): Indian grid region
        scenario (str): Grid scenario
        
    Returns:
        float: Renewable energy share as percentage
    """
    
    # Simplified renewable share calculation
    renewable_shares = {
        "current_2024": 23.5,
        "renewable_target_2030": 32.0,
        "ambitious_2030": 40.5
    }
    
    return renewable_shares.get(scenario, 25.0)  # Default 25%

def calculate_resource_efficiency_score(recycled_fraction: float,
                                      total_energy_kwh: float,
                                      production_kg: float) -> float:
    """
    Calculate resource efficiency score (0-100 scale)
    
    Args:
        recycled_fraction (float): Recycled content fraction
        total_energy_kwh (float): Total energy consumption
        production_kg (float): Production quantity
        
    Returns:
        float: Resource efficiency score (0-100)
    """
    
    # Material efficiency component (0-50 points)
    material_score = recycled_fraction * 50
    
    # Energy efficiency component (0-50 points)
    # Benchmark against typical energy intensities
    energy_intensity = total_energy_kwh / production_kg if production_kg > 0 else 0
    
    # Typical energy intensities (kWh/kg)
    benchmark_primary = {"aluminum": 15.0, "copper": 4.0}
    benchmark_secondary = {"aluminum": 1.0, "copper": 1.5}
    
    # Simplified energy efficiency calculation
    if energy_intensity < 2.0:  # Very efficient (mostly secondary)
        energy_score = 50
    elif energy_intensity < 8.0:  # Moderate efficiency
        energy_score = 35
    elif energy_intensity < 15.0:  # Lower efficiency
        energy_score = 20
    else:  # High energy intensity
        energy_score = 10
    
    total_score = material_score + energy_score
    
    return min(total_score, 100.0)  # Cap at 100

def compare_lca_scenarios(metal_type: str,
                         production_kg: float,
                         scenarios: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compare LCA results across different scenarios
    
    Args:
        metal_type (str): "aluminum" or "copper"
        production_kg (float): Production quantity
        scenarios (Dict): Dictionary of scenario parameters
        
    Returns:
        Dict: Scenario comparison results
    """
    
    results = {}
    
    for scenario_name, params in scenarios.items():
        try:
            result = calculate_total_lca_emissions(
                metal_type=metal_type,
                production_kg=production_kg,
                recycled_fraction=params.get("recycled_fraction", 0.0),
                product_type=params.get("product_type", "generic"),
                region=params.get("region", "national_average"),
                scenario=params.get("grid_scenario", "current_2024"),
                transport_config=params.get("transport_config"),
                include_eol_credit=params.get("include_eol_credit", True)
            )
            results[scenario_name] = result
            
        except Exception as e:
            logging.error(f"Error calculating LCA for scenario '{scenario_name}': {e}")
            results[scenario_name] = None
    
    # Find best and worst scenarios
    valid_results = {k: v for k, v in results.items() if v is not None}
    
    if valid_results:
        best_scenario = min(valid_results.keys(),
                           key=lambda k: valid_results[k]["formula_5_breakdown"]["total_net_emissions_kg_co2e"])
        worst_scenario = max(valid_results.keys(),
                            key=lambda k: valid_results[k]["formula_5_breakdown"]["total_net_emissions_kg_co2e"])
        
        best_emissions = valid_results[best_scenario]["formula_5_breakdown"]["total_net_emissions_kg_co2e"]
        worst_emissions = valid_results[worst_scenario]["formula_5_breakdown"]["total_net_emissions_kg_co2e"]
        
        emission_reduction = worst_emissions - best_emissions
        reduction_percentage = (emission_reduction / worst_emissions) * 100 if worst_emissions > 0 else 0
    else:
        best_scenario = worst_scenario = None
        emission_reduction = reduction_percentage = 0
    
    return {
        "metal_type": metal_type,
        "production_kg": production_kg,
        "scenario_results": results,
        "comparison_summary": {
            "best_scenario": best_scenario,
            "worst_scenario": worst_scenario,
            "emission_reduction_potential_kg_co2e": emission_reduction,
            "reduction_percentage": reduction_percentage,
            "scenarios_ranked": sorted(valid_results.keys(),
                                     key=lambda k: valid_results[k]["formula_5_breakdown"]["total_net_emissions_kg_co2e"])
        }
    }

# Validation and testing
if __name__ == "__main__":
    # Test aluminum LCA with 30% recycled content
    al_lca = calculate_total_lca_emissions("aluminum", 1000.0, 0.3, "beverage_cans")
    print(f"Aluminum LCA (30% recycled, 1000 kg):")
    print(f"Total emissions: {al_lca['formula_5_breakdown']['total_net_emissions_kg_co2e']:.2f} kg CO2e")
    print(f"Emission intensity: {al_lca['formula_5_breakdown']['emission_intensity_kg_co2e_per_kg']:.4f} kg CO2e/kg")
    print(f"Circularity index: {al_lca['key_performance_indicators']['circularity_index']:.3f}")
    
    # Test scenario comparison
    scenarios = {
        "primary_only": {"recycled_fraction": 0.0, "grid_scenario": "current_2024"},
        "mixed_current": {"recycled_fraction": 0.3, "grid_scenario": "current_2024"},
        "mixed_renewable": {"recycled_fraction": 0.3, "grid_scenario": "renewable_target_2030"},
        "high_recycling": {"recycled_fraction": 0.6, "grid_scenario": "renewable_target_2030"}
    }
    
    comparison = compare_lca_scenarios("aluminum", 1000.0, scenarios)
    print(f"\nBest scenario: {comparison['comparison_summary']['best_scenario']}")
    print(f"Emission reduction potential: {comparison['comparison_summary']['reduction_percentage']:.1f}%")
    
    # Test copper LCA
    cu_lca = calculate_total_lca_emissions("copper", 1000.0, 0.4, "electrical_wiring")
    print(f"\nCopper LCA (40% recycled, 1000 kg):")
    print(f"Total emissions: {cu_lca['formula_5_breakdown']['total_net_emissions_kg_co2e']:.2f} kg CO2e")
    print(f"Recycling benefit: {cu_lca['route_comparison']['recycling_emission_reduction_percent']:.1f}%")