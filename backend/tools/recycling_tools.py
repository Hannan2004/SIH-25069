"""
Recycling and Circularity Calculation Tools
Implements Formula 4: Recycling metrics and circularity indicators
Covers India-specific recycling infrastructure and informal sector dynamics
"""

from typing import Dict, Optional, List, Tuple
import logging
import math

# India Recycling Infrastructure Data
INDIA_RECYCLING_RATES = {
    "aluminum": {
        "collection_rate": 0.65,        # 65% collection rate in India
        "recycling_efficiency": 0.92,   # 92% recycling efficiency for aluminum
        "informal_sector_share": 0.75,  # 75% handled by informal sector
        "export_scrap_rate": 0.15      # 15% exported as scrap
    },
    "copper": {
        "collection_rate": 0.78,        # 78% collection rate (higher value metal)
        "recycling_efficiency": 0.88,   # 88% recycling efficiency
        "informal_sector_share": 0.85,  # 85% handled by informal sector
        "export_scrap_rate": 0.05      # 5% exported as scrap
    }
}

# Product Lifetime Data (years) - India specific where available
PRODUCT_LIFETIMES = {
    "aluminum": {
        "beverage_cans": 0.25,          # 3 months average
        "automotive_parts": 12,         # 12 years average vehicle life
        "building_construction": 50,     # Building components
        "electrical_conductors": 25,     # Electrical applications
        "packaging_foil": 0.1,          # 1 month for flexible packaging
        "cookware": 8,                  # Household cookware
        "window_frames": 30            # Architectural applications
    },
    "copper": {
        "electrical_wiring": 40,        # Building electrical systems
        "plumbing_tubes": 35,          # Plumbing systems
        "telecom_cables": 15,          # Telecommunications
        "automotive_wiring": 12,        # Vehicle electrical systems
        "industrial_equipment": 20,     # Industrial machinery
        "electronics": 5,              # Consumer electronics
        "roofing_sheets": 50          # Architectural copper
    }
}

# Regional Collection Efficiency Variations
REGIONAL_COLLECTION_EFFICIENCY = {
    "urban_tier1": 0.85,              # Metro cities (Mumbai, Delhi, etc.)
    "urban_tier2": 0.72,              # Tier-2 cities
    "urban_tier3": 0.58,              # Smaller cities
    "rural": 0.35,                    # Rural areas
    "industrial_zones": 0.90,         # Industrial clusters
    "coastal_areas": 0.68             # Coastal regions
}

# Recycling Process Energy and Emissions
RECYCLING_ENERGY_EFFICIENCY = {
    "aluminum": {
        "energy_savings_vs_primary": 0.95,    # 95% energy savings
        "emission_reduction_vs_primary": 0.92  # 92% emission reduction
    },
    "copper": {
        "energy_savings_vs_primary": 0.85,    # 85% energy savings
        "emission_reduction_vs_primary": 0.75  # 75% emission reduction
    }
}

def calculate_effective_secondary_content(collection_rate: float,
                                        recycling_efficiency: float,
                                        losses_in_use: float = 0.0) -> float:
    """
    Calculate Effective Secondary Content (ESC) using Formula 4.1
    
    ESC = CollectionRate × RecyclingEfficiency
    
    Args:
        collection_rate (float): Collection rate (0-1)
        recycling_efficiency (float): Recycling efficiency (0-1)
        losses_in_use (float): Losses during use phase (0-1)
        
    Returns:
        float: Effective secondary content (0-1)
    """
    
    # Account for losses during use phase
    available_for_collection = 1.0 - losses_in_use
    
    # Calculate ESC
    esc = collection_rate * recycling_efficiency * available_for_collection
    
    return min(esc, 1.0)  # Cap at 100%

def calculate_product_secondary_share(existing_secondary_content: float,
                                    effective_secondary_content: float) -> float:
    """
    Calculate Product's Secondary Share using Formula 4.2
    
    SS = ExistingSecondaryContent + ESC
    
    Args:
        existing_secondary_content (float): Current recycled content (0-1)
        effective_secondary_content (float): ESC from Formula 4.1
        
    Returns:
        float: Total secondary share (0-1)
    """
    
    secondary_share = existing_secondary_content + effective_secondary_content
    
    return min(secondary_share, 1.0)  # Cap at 100%

def calculate_avoided_virgin_production(effective_secondary_content: float,
                                      virgin_emission_factor: float) -> float:
    """
    Calculate Avoided Virgin Production using Formula 4.3
    
    AvoidedImpact = ESC × EF(virgin)
    
    Args:
        effective_secondary_content (float): ESC from Formula 4.1
        virgin_emission_factor (float): Virgin production EF (kg CO2e/kg)
        
    Returns:
        float: Avoided emissions (kg CO2e/kg)
    """
    
    avoided_impact = effective_secondary_content * virgin_emission_factor
    
    return avoided_impact

def calculate_effective_product_emission_factor(secondary_share: float,
                                              virgin_ef: float,
                                              secondary_ef: float) -> float:
    """
    Calculate Effective Product Emission Factor using Formula 4.4
    
    EF(product) = (1 - SS) × EF(virgin) + SS × EF(secondary)
    
    Args:
        secondary_share (float): Secondary share from Formula 4.2
        virgin_ef (float): Virgin production emission factor (kg CO2e/kg)
        secondary_ef (float): Secondary production emission factor (kg CO2e/kg)
        
    Returns:
        float: Weighted emission factor (kg CO2e/kg)
    """
    
    primary_share = 1.0 - secondary_share
    
    effective_ef = (primary_share * virgin_ef) + (secondary_share * secondary_ef)
    
    return effective_ef

def calculate_circularity_metrics(metal_type: str,
                                product_type: str,
                                current_secondary_content: float = 0.0,
                                region: str = "urban_tier1",
                                custom_collection_rate: Optional[float] = None,
                                custom_recycling_efficiency: Optional[float] = None,
                                virgin_ef: Optional[float] = None,
                                secondary_ef: Optional[float] = None) -> Dict[str, any]:
    """
    Calculate comprehensive circularity metrics for a product
    
    Args:
        metal_type (str): "aluminum" or "copper"
        product_type (str): Specific product type
        current_secondary_content (float): Current recycled content (0-1)
        region (str): Geographic region for collection efficiency
        custom_collection_rate (float, optional): Override default collection rate
        custom_recycling_efficiency (float, optional): Override default efficiency
        virgin_ef (float, optional): Virgin production emission factor
        secondary_ef (float, optional): Secondary production emission factor
        
    Returns:
        Dict: Comprehensive circularity analysis
    """
    
    # Get base recycling data
    if metal_type.lower() not in INDIA_RECYCLING_RATES:
        raise ValueError(f"Unsupported metal type: {metal_type}")
    
    base_data = INDIA_RECYCLING_RATES[metal_type.lower()]
    
    # Get collection rate
    if custom_collection_rate is not None:
        collection_rate = custom_collection_rate
    else:
        base_collection = base_data["collection_rate"]
        regional_efficiency = REGIONAL_COLLECTION_EFFICIENCY.get(region, 0.75)
        collection_rate = base_collection * (regional_efficiency / 0.75)  # Normalize to average
    
    # Get recycling efficiency
    recycling_efficiency = custom_recycling_efficiency or base_data["recycling_efficiency"]
    
    # Get product lifetime
    product_lifetime = PRODUCT_LIFETIMES.get(metal_type.lower(), {}).get(product_type, 15)  # Default 15 years
    
    # Calculate losses during use (simplified model)
    use_losses = min(0.05 + (0.001 * product_lifetime), 0.15)  # 5-15% losses based on lifetime
    
    # Apply Formula 4 calculations
    esc = calculate_effective_secondary_content(collection_rate, recycling_efficiency, use_losses)
    secondary_share = calculate_product_secondary_share(current_secondary_content, esc)
    
    # Estimate emission factors if not provided
    if virgin_ef is None:
        # Use approximate values based on metal type
        virgin_ef = 11.5 if metal_type.lower() == "aluminum" else 3.2  # kg CO2e/kg
    
    if secondary_ef is None:
        # Calculate based on energy savings
        energy_savings = RECYCLING_ENERGY_EFFICIENCY[metal_type.lower()]["energy_savings_vs_primary"]
        secondary_ef = virgin_ef * (1 - energy_savings)
    
    avoided_impact = calculate_avoided_virgin_production(esc, virgin_ef)
    effective_ef = calculate_effective_product_emission_factor(secondary_share, virgin_ef, secondary_ef)
    
    # Calculate additional circularity indicators
    circularity_index = calculate_circularity_index(
        secondary_share, product_lifetime, recycling_efficiency, collection_rate
    )
    
    material_flow_efficiency = calculate_material_flow_efficiency(
        collection_rate, recycling_efficiency, use_losses
    )
    
    return {
        "metal_type": metal_type,
        "product_type": product_type,
        "region": region,
        "input_parameters": {
            "current_secondary_content": current_secondary_content,
            "collection_rate": collection_rate,
            "recycling_efficiency": recycling_efficiency,
            "product_lifetime_years": product_lifetime,
            "use_losses": use_losses
        },
        "formula_4_results": {
            "effective_secondary_content": esc,
            "total_secondary_share": secondary_share,
            "avoided_virgin_impact_kg_co2e_per_kg": avoided_impact,
            "effective_emission_factor_kg_co2e_per_kg": effective_ef
        },
        "circularity_indicators": {
            "circularity_index": circularity_index,
            "material_flow_efficiency": material_flow_efficiency,
            "emission_reduction_vs_virgin_percent": ((virgin_ef - effective_ef) / virgin_ef) * 100,
            "resource_efficiency_score": secondary_share * recycling_efficiency
        },
        "benchmarking": {
            "virgin_ef_kg_co2e_per_kg": virgin_ef,
            "secondary_ef_kg_co2e_per_kg": secondary_ef,
            "emission_savings_kg_co2e_per_kg": virgin_ef - effective_ef,
            "informal_sector_contribution": base_data["informal_sector_share"]
        }
    }

def calculate_circularity_index(secondary_share: float,
                              product_lifetime: float,
                              recycling_efficiency: float,
                              collection_rate: float) -> float:
    """
    Calculate comprehensive circularity index (0-1 scale)
    
    Args:
        secondary_share (float): Total secondary content (0-1)
        product_lifetime (float): Product lifetime in years
        recycling_efficiency (float): Recycling efficiency (0-1)
        collection_rate (float): Collection rate (0-1)
        
    Returns:
        float: Circularity index (0-1, higher = more circular)
    """
    
    # Lifetime factor (longer lifetime = more circular, with diminishing returns)
    lifetime_factor = min(product_lifetime / 50, 1.0)  # Normalize to 50-year max
    
    # End-of-life factor
    eol_factor = collection_rate * recycling_efficiency
    
    # Material efficiency factor
    material_factor = secondary_share
    
    # Weighted circularity index
    circularity_index = (
        0.4 * material_factor +      # 40% weight on material circularity
        0.35 * eol_factor +          # 35% weight on end-of-life management
        0.25 * lifetime_factor       # 25% weight on product durability
    )
    
    return round(circularity_index, 3)

def calculate_material_flow_efficiency(collection_rate: float,
                                     recycling_efficiency: float,
                                     use_losses: float) -> float:
    """
    Calculate material flow efficiency through the system
    
    Args:
        collection_rate (float): Collection rate (0-1)
        recycling_efficiency (float): Recycling efficiency (0-1)
        use_losses (float): Losses during use phase (0-1)
        
    Returns:
        float: Material flow efficiency (0-1)
    """
    
    # Account for losses at each stage
    material_retained = (1 - use_losses) * collection_rate * recycling_efficiency
    
    return round(material_retained, 3)

def compare_recycling_scenarios(metal_type: str,
                              product_type: str,
                              scenarios: Dict[str, Dict[str, float]]) -> Dict[str, any]:
    """
    Compare different recycling scenarios
    
    Args:
        metal_type (str): "aluminum" or "copper"
        product_type (str): Specific product type
        scenarios (Dict): Dictionary of scenario parameters
        
    Returns:
        Dict: Scenario comparison analysis
    """
    
    results = {}
    
    for scenario_name, params in scenarios.items():
        try:
            result = calculate_circularity_metrics(
                metal_type, product_type,
                current_secondary_content=params.get("secondary_content", 0.0),
                region=params.get("region", "urban_tier1"),
                custom_collection_rate=params.get("collection_rate"),
                custom_recycling_efficiency=params.get("recycling_efficiency")
            )
            results[scenario_name] = result
            
        except Exception as e:
            logging.error(f"Error calculating scenario '{scenario_name}': {e}")
            results[scenario_name] = None
    
    # Find best and worst scenarios
    valid_results = {k: v for k, v in results.items() if v is not None}
    
    if valid_results:
        best_scenario = max(valid_results.keys(),
                           key=lambda k: valid_results[k]["circularity_indicators"]["circularity_index"])
        worst_scenario = min(valid_results.keys(),
                            key=lambda k: valid_results[k]["circularity_indicators"]["circularity_index"])
        
        best_index = valid_results[best_scenario]["circularity_indicators"]["circularity_index"]
        worst_index = valid_results[worst_scenario]["circularity_indicators"]["circularity_index"]
    else:
        best_scenario = worst_scenario = None
        best_index = worst_index = 0
    
    return {
        "metal_type": metal_type,
        "product_type": product_type,
        "scenario_results": results,
        "comparison": {
            "best_scenario": best_scenario,
            "worst_scenario": worst_scenario,
            "circularity_improvement_potential": best_index - worst_index,
            "scenarios_ranked": sorted(valid_results.keys(),
                                     key=lambda k: valid_results[k]["circularity_indicators"]["circularity_index"],
                                     reverse=True)
        }
    }

def generate_circularity_recommendations(circularity_data: Dict[str, any],
                                       target_circularity: float = 0.8) -> List[Dict[str, str]]:
    """
    Generate recommendations to improve circularity
    
    Args:
        circularity_data (Dict): Results from calculate_circularity_metrics
        target_circularity (float): Target circularity index (0-1)
        
    Returns:
        List[Dict]: List of improvement recommendations
    """
    
    recommendations = []
    current_index = circularity_data["circularity_indicators"]["circularity_index"]
    params = circularity_data["input_parameters"]
    
    # Collection rate improvements
    if params["collection_rate"] < 0.8:
        potential_improvement = min(0.9, params["collection_rate"] + 0.2) - params["collection_rate"]
        impact_estimate = potential_improvement * 0.35  # 35% weight in circularity index
        
        recommendations.append({
            "category": "collection_improvement",
            "recommendation": "Improve collection infrastructure and awareness",
            "current_value": f"{params['collection_rate']*100:.1f}%",
            "target_value": f"{min(90, params['collection_rate']*100 + 20):.1f}%",
            "circularity_impact": f"+{impact_estimate:.2f} index points",
            "priority": "high" if params["collection_rate"] < 0.6 else "medium"
        })
    
    # Recycling efficiency improvements
    if params["recycling_efficiency"] < 0.9:
        potential_improvement = min(0.95, params["recycling_efficiency"] + 0.1) - params["recycling_efficiency"]
        impact_estimate = potential_improvement * 0.35
        
        recommendations.append({
            "category": "process_efficiency",
            "recommendation": "Upgrade recycling technology and processes",
            "current_value": f"{params['recycling_efficiency']*100:.1f}%",
            "target_value": f"{min(95, params['recycling_efficiency']*100 + 10):.1f}%",
            "circularity_impact": f"+{impact_estimate:.2f} index points",
            "priority": "medium"
        })
    
    # Secondary content improvements
    current_secondary = circularity_data["formula_4_results"]["total_secondary_share"]
    if current_secondary < 0.6:
        recommendations.append({
            "category": "design_for_circularity",
            "recommendation": "Increase recycled content in new products",
            "current_value": f"{current_secondary*100:.1f}%",
            "target_value": "60%+",
            "circularity_impact": "Significant improvement in material circularity",
            "priority": "high"
        })
    
    # Product lifetime extension
    if params["product_lifetime_years"] < 20:
        recommendations.append({
            "category": "durability",
            "recommendation": "Design for longer product lifetime and repairability",
            "current_value": f"{params['product_lifetime_years']:.1f} years",
            "target_value": "20+ years",
            "circularity_impact": "Enhanced resource efficiency",
            "priority": "medium"
        })
    
    # Regional specific recommendations
    region = circularity_data["region"]
    if region in ["rural", "urban_tier3"]:
        recommendations.append({
            "category": "infrastructure_development",
            "recommendation": "Develop regional collection and processing infrastructure",
            "current_value": f"Limited infrastructure in {region}",
            "target_value": "Improved regional coverage",
            "circularity_impact": "Enhanced collection rates",
            "priority": "high"
        })
    
    # Policy recommendations
    informal_contribution = circularity_data["benchmarking"]["informal_sector_contribution"]
    if informal_contribution > 0.7:
        recommendations.append({
            "category": "policy_integration",
            "recommendation": "Formalize and support informal recycling sector",
            "current_value": f"{informal_contribution*100:.0f}% informal sector",
            "target_value": "Integrated formal-informal system",
            "circularity_impact": "Improved efficiency and working conditions",
            "priority": "medium"
        })
    
    return recommendations

def calculate_end_of_life_scenarios(metal_type: str,
                                  product_mass_kg: float,
                                  scenarios: Dict[str, float]) -> Dict[str, any]:
    """
    Calculate end-of-life impact under different collection scenarios
    
    Args:
        metal_type (str): "aluminum" or "copper"
        product_mass_kg (float): Product mass in kg
        scenarios (Dict): Collection rate scenarios {scenario_name: collection_rate}
        
    Returns:
        Dict: End-of-life scenario analysis
    """
    
    base_data = INDIA_RECYCLING_RATES[metal_type.lower()]
    recycling_efficiency = base_data["recycling_efficiency"]
    
    # Estimate virgin production impact
    virgin_ef = 11.5 if metal_type.lower() == "aluminum" else 3.2  # kg CO2e/kg
    
    scenario_results = {}
    
    for scenario_name, collection_rate in scenarios.items():
        # Calculate effective recovery
        recovered_mass = product_mass_kg * collection_rate * recycling_efficiency
        lost_mass = product_mass_kg - recovered_mass
        
        # Calculate avoided emissions from recovery
        avoided_emissions = recovered_mass * virgin_ef
        
        # Calculate lost value (economic and environmental)
        lost_value_environmental = lost_mass * virgin_ef
        
        scenario_results[scenario_name] = {
            "collection_rate": collection_rate,
            "recovered_mass_kg": recovered_mass,
            "lost_mass_kg": lost_mass,
            "avoided_emissions_kg_co2e": avoided_emissions,
            "lost_environmental_value_kg_co2e": lost_value_environmental,
            "recovery_efficiency": (recovered_mass / product_mass_kg) * 100,
            "net_environmental_benefit": avoided_emissions
        }
    
    return {
        "metal_type": metal_type,
        "product_mass_kg": product_mass_kg,
        "scenario_results": scenario_results,
        "analysis": {
            "best_case_collection": max(scenarios.keys(), key=lambda k: scenarios[k]),
            "worst_case_collection": min(scenarios.keys(), key=lambda k: scenarios[k]),
            "improvement_potential_kg_co2e": max([r["avoided_emissions_kg_co2e"] for r in scenario_results.values()]) - 
                                            min([r["avoided_emissions_kg_co2e"] for r in scenario_results.values()])
        }
    }

# Validation and testing
if __name__ == "__main__":
    # Test aluminum beverage can circularity
    al_can_metrics = calculate_circularity_metrics("aluminum", "beverage_cans", 0.3, "urban_tier1")
    print(f"Aluminum Can Circularity Index: {al_can_metrics['circularity_indicators']['circularity_index']:.3f}")
    print(f"Secondary Share: {al_can_metrics['formula_4_results']['total_secondary_share']*100:.1f}%")
    
    # Test scenario comparison
    scenarios = {
        "current": {"secondary_content": 0.3, "collection_rate": 0.65},
        "improved": {"secondary_content": 0.5, "collection_rate": 0.8},
        "target": {"secondary_content": 0.7, "collection_rate": 0.9}
    }
    
    comparison = compare_recycling_scenarios("aluminum", "beverage_cans", scenarios)
    print(f"\nBest Scenario: {comparison['comparison']['best_scenario']}")
    print(f"Circularity Improvement Potential: {comparison['comparison']['circularity_improvement_potential']:.3f}")
    
    # Test recommendations
    recommendations = generate_circularity_recommendations(al_can_metrics)
    print(f"\nTop Recommendation: {recommendations[0]['recommendation']}")
    print(f"Priority: {recommendations[0]['priority']}")