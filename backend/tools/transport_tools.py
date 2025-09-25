"""
Transport Emission Calculation Tools
Implements Formula 3: Emissions(transport) = Weight(t) × Distance(km) × EF(transport)
Covers India-specific transport modes with regional variations
"""

from typing import Dict, List, Optional, Tuple
import logging
import math

# Transport Emission Factors (kg CO2e/t·km) - India specific data
INDIA_TRANSPORT_EMISSION_FACTORS = {
    # Road Transport
    "truck_heavy": 0.062,           # Heavy trucks (>16t) - diesel
    "truck_medium": 0.089,          # Medium trucks (3.5-16t) - diesel
    "truck_light": 0.158,           # Light trucks (<3.5t) - diesel
    "truck_electric": 0.018,        # Electric trucks (using India grid mix)
    
    # Rail Transport
    "rail_freight": 0.022,          # Indian Railways freight (electric + diesel mix)
    "rail_electric": 0.016,         # Fully electric rail freight
    "rail_diesel": 0.041,           # Diesel locomotive freight
    
    # Water Transport
    "coastal_shipping": 0.015,      # Coastal/inland waterways
    "river_barge": 0.012,          # River barges
    
    # Intermodal
    "multimodal": 0.035,           # Average for multimodal transport
    
    # Specialized
    "container_truck": 0.055,       # Container trucks to/from ports
    "bulk_truck": 0.048,           # Bulk material trucks
    "pipeline": 0.002              # Pipelines (for liquid materials)
}

# Distance matrices for major Indian industrial cities (km)
INDIA_CITY_DISTANCES = {
    # Format: {(origin, destination): {transport_mode: distance}}
    ("mumbai", "delhi"): {
        "road": 1155, "rail": 1384, "air": 1136
    },
    ("mumbai", "kolkata"): {
        "road": 1672, "rail": 1968, "air": 1657
    },
    ("mumbai", "chennai"): {
        "road": 1028, "rail": 1279, "air": 1024
    },
    ("delhi", "kolkata"): {
        "road": 1305, "rail": 1472, "air": 1318
    },
    ("delhi", "chennai"): {
        "road": 1768, "rail": 2180, "air": 1759
    },
    ("kolkata", "chennai"): {
        "road": 1366, "rail": 1659, "air": 1338
    },
    # Port cities
    ("mumbai", "kandla"): {
        "road": 697, "rail": 956, "coastal": 585
    },
    ("chennai", "tuticorin"): {
        "road": 596, "rail": 624, "coastal": 412
    },
    ("kolkata", "paradip"): {
        "road": 267, "rail": 489, "coastal": 198
    },
    # Mining regions to processing centers
    ("bhubaneswar", "jamshedpur"): {
        "road": 350, "rail": 438
    },
    ("raipur", "bhilai"): {
        "road": 42, "rail": 68
    }
}

# Regional transport preferences and constraints
INDIA_TRANSPORT_PREFERENCES = {
    "northern": {
        "preferred": ["rail_freight", "truck_heavy"],
        "constraints": ["limited_waterways"],
        "rail_electrification": 0.85  # 85% electrified
    },
    "western": {
        "preferred": ["coastal_shipping", "rail_freight", "truck_heavy"],
        "constraints": ["port_congestion"],
        "rail_electrification": 0.78
    },
    "southern": {
        "preferred": ["rail_freight", "coastal_shipping", "truck_heavy"],
        "constraints": ["hill_sections"],
        "rail_electrification": 0.72
    },
    "eastern": {
        "preferred": ["rail_freight", "river_barge", "truck_heavy"],
        "constraints": ["monsoon_flooding"],
        "rail_electrification": 0.68
    },
    "northeastern": {
        "preferred": ["truck_medium", "river_barge"],
        "constraints": ["limited_rail", "terrain_challenges"],
        "rail_electrification": 0.45
    }
}

# Load factors and capacity utilization
TRANSPORT_LOAD_FACTORS = {
    "truck_heavy": 0.75,           # 75% capacity utilization
    "truck_medium": 0.70,
    "truck_light": 0.65,
    "rail_freight": 0.80,          # Higher load factor for rail
    "coastal_shipping": 0.85,
    "river_barge": 0.82,
    "container_truck": 0.78
}

def calculate_transport_emissions(weight_tonnes: float,
                                distance_km: float,
                                transport_mode: str,
                                custom_ef: Optional[float] = None,
                                load_factor: Optional[float] = None,
                                return_trip_empty: bool = True) -> Dict[str, float]:
    """
    Calculate transport emissions using Formula 3
    
    Emissions(transport) = Weight(t) × Distance(km) × EF(transport)
    
    Args:
        weight_tonnes (float): Shipment weight in tonnes
        distance_km (float): Transport distance in km
        transport_mode (str): Mode of transport
        custom_ef (float, optional): Custom emission factor (kg CO2e/t·km)
        load_factor (float, optional): Capacity utilization factor (0-1)
        return_trip_empty (bool): Account for empty return trip
        
    Returns:
        Dict[str, float]: Transport emissions breakdown
    """
    
    # Get emission factor
    if custom_ef:
        emission_factor = custom_ef
    elif transport_mode in INDIA_TRANSPORT_EMISSION_FACTORS:
        emission_factor = INDIA_TRANSPORT_EMISSION_FACTORS[transport_mode]
    else:
        raise ValueError(f"Unknown transport mode: {transport_mode}")
    
    # Get load factor
    if load_factor is None:
        load_factor = TRANSPORT_LOAD_FACTORS.get(transport_mode, 0.75)  # Default 75%
    
    # Adjust for load factor (higher load factor = lower emissions per tonne)
    adjusted_ef = emission_factor / load_factor
    
    # Calculate base emissions
    base_emissions = weight_tonnes * distance_km * adjusted_ef
    
    # Account for return trip if empty
    if return_trip_empty and transport_mode.startswith("truck"):
        # Assume 50% probability of empty return for trucks
        empty_return_factor = 1.5
    else:
        empty_return_factor = 1.0
    
    total_emissions = base_emissions * empty_return_factor
    
    return {
        "weight_tonnes": weight_tonnes,
        "distance_km": distance_km,
        "transport_mode": transport_mode,
        "emission_factor_kg_co2e_per_t_km": emission_factor,
        "adjusted_ef_kg_co2e_per_t_km": adjusted_ef,
        "load_factor": load_factor,
        "empty_return_factor": empty_return_factor,
        "base_emissions_kg_co2e": base_emissions,
        "total_emissions_kg_co2e": total_emissions,
        "emission_intensity_kg_co2e_per_t_km": total_emissions / (weight_tonnes * distance_km) if weight_tonnes > 0 and distance_km > 0 else 0
    }

def calculate_multimodal_transport(shipment_legs: List[Dict],
                                 total_weight_tonnes: float) -> Dict[str, any]:
    """
    Calculate emissions for multimodal transport chains
    
    Args:
        shipment_legs (List[Dict]): List of transport legs with mode and distance
        total_weight_tonnes (float): Total shipment weight
        
    Returns:
        Dict: Multimodal transport analysis
    """
    
    leg_results = []
    total_distance = 0.0
    total_emissions = 0.0
    
    for i, leg in enumerate(shipment_legs):
        try:
            leg_result = calculate_transport_emissions(
                total_weight_tonnes,
                leg["distance_km"],
                leg["transport_mode"],
                leg.get("custom_ef"),
                leg.get("load_factor"),
                leg.get("return_trip_empty", True)
            )
            
            leg_result["leg_number"] = i + 1
            leg_result["leg_description"] = leg.get("description", f"Leg {i+1}")
            
            leg_results.append(leg_result)
            total_distance += leg["distance_km"]
            total_emissions += leg_result["total_emissions_kg_co2e"]
            
        except ValueError as e:
            logging.error(f"Error calculating emissions for leg {i+1}: {e}")
            continue
    
    return {
        "total_weight_tonnes": total_weight_tonnes,
        "total_distance_km": total_distance,
        "total_emissions_kg_co2e": total_emissions,
        "average_emission_intensity_kg_co2e_per_t_km": total_emissions / (total_weight_tonnes * total_distance) if total_weight_tonnes > 0 and total_distance > 0 else 0,
        "number_of_legs": len(leg_results),
        "leg_breakdown": leg_results
    }

def compare_transport_modes(weight_tonnes: float,
                          distance_km: float,
                          modes_to_compare: List[str],
                          region: str = "national") -> Dict[str, any]:
    """
    Compare different transport modes for same route
    
    Args:
        weight_tonnes (float): Shipment weight
        distance_km (float): Transport distance
        modes_to_compare (List[str]): List of transport modes to compare
        region (str): Indian region for context
        
    Returns:
        Dict: Transport mode comparison
    """
    
    results = {}
    
    for mode in modes_to_compare:
        try:
            # Adjust distance based on mode (rail vs road may differ)
            adjusted_distance = distance_km
            if mode.startswith("rail") and "road" in modes_to_compare:
                adjusted_distance = distance_km * 1.15  # Rail typically 15% longer
            
            result = calculate_transport_emissions(
                weight_tonnes, adjusted_distance, mode
            )
            results[mode] = result
            
        except ValueError as e:
            logging.error(f"Error calculating emissions for mode '{mode}': {e}")
            results[mode] = None
    
    # Find best and worst options
    valid_results = {k: v for k, v in results.items() if v is not None}
    
    if valid_results:
        best_mode = min(valid_results.keys(), 
                       key=lambda k: valid_results[k]["total_emissions_kg_co2e"])
        worst_mode = max(valid_results.keys(), 
                        key=lambda k: valid_results[k]["total_emissions_kg_co2e"])
        
        best_emissions = valid_results[best_mode]["total_emissions_kg_co2e"]
        worst_emissions = valid_results[worst_mode]["total_emissions_kg_co2e"]
        
        emission_reduction = worst_emissions - best_emissions
        reduction_percentage = (emission_reduction / worst_emissions) * 100 if worst_emissions > 0 else 0
    else:
        best_mode = worst_mode = None
        emission_reduction = reduction_percentage = 0
    
    return {
        "weight_tonnes": weight_tonnes,
        "distance_km": distance_km,
        "region": region,
        "mode_results": results,
        "comparison": {
            "best_mode": best_mode,
            "worst_mode": worst_mode,
            "emission_reduction_kg_co2e": emission_reduction,
            "reduction_percentage": reduction_percentage
        }
    }

def get_city_route_emissions(origin: str,
                           destination: str,
                           weight_tonnes: float,
                           preferred_mode: Optional[str] = None) -> Dict[str, any]:
    """
    Calculate emissions for predefined city routes in India
    
    Args:
        origin (str): Origin city
        destination (str): Destination city
        weight_tonnes (float): Shipment weight
        preferred_mode (str, optional): Preferred transport mode
        
    Returns:
        Dict: Route-specific transport analysis
    """
    
    route_key = (origin.lower(), destination.lower())
    reverse_route_key = (destination.lower(), origin.lower())
    
    # Check if route exists in database
    if route_key in INDIA_CITY_DISTANCES:
        route_data = INDIA_CITY_DISTANCES[route_key]
    elif reverse_route_key in INDIA_CITY_DISTANCES:
        route_data = INDIA_CITY_DISTANCES[reverse_route_key]
    else:
        raise ValueError(f"Route from {origin} to {destination} not found in database")
    
    # Calculate emissions for available modes
    mode_results = {}
    
    for mode, distance in route_data.items():
        # Map route modes to transport modes
        transport_mode_map = {
            "road": "truck_heavy",
            "rail": "rail_freight", 
            "air": "air_freight",
            "coastal": "coastal_shipping"
        }
        
        if mode in transport_mode_map:
            transport_mode = transport_mode_map[mode]
            try:
                result = calculate_transport_emissions(
                    weight_tonnes, distance, transport_mode
                )
                mode_results[mode] = result
            except ValueError:
                continue
    
    # Select recommended mode based on preferences or emissions
    if preferred_mode and preferred_mode in mode_results:
        recommended = preferred_mode
    elif mode_results:
        # Recommend mode with lowest emissions
        recommended = min(mode_results.keys(), 
                         key=lambda k: mode_results[k]["total_emissions_kg_co2e"])
    else:
        recommended = None
    
    return {
        "origin": origin,
        "destination": destination,
        "weight_tonnes": weight_tonnes,
        "available_modes": list(route_data.keys()),
        "mode_results": mode_results,
        "recommended_mode": recommended,
        "route_efficiency": {
            "shortest_distance_km": min(route_data.values()) if route_data else 0,
            "lowest_emissions_kg_co2e": min([r["total_emissions_kg_co2e"] for r in mode_results.values()]) if mode_results else 0
        }
    }

def transport_optimization_suggestions(transport_data: Dict[str, any],
                                     region: str = "national") -> List[Dict[str, str]]:
    """
    Generate transport optimization recommendations
    
    Args:
        transport_data (Dict): Transport emissions data
        region (str): Indian region for context
        
    Returns:
        List[Dict]: List of optimization suggestions
    """
    
    suggestions = []
    
    # Modal shift recommendations
    if "mode_results" in transport_data:
        mode_results = transport_data["mode_results"]
        
        # Check if rail is available and beneficial
        rail_modes = [k for k in mode_results.keys() if "rail" in k]
        truck_modes = [k for k in mode_results.keys() if "truck" in k]
        
        if rail_modes and truck_modes:
            rail_emissions = min([mode_results[m]["total_emissions_kg_co2e"] for m in rail_modes])
            truck_emissions = max([mode_results[m]["total_emissions_kg_co2e"] for m in truck_modes])
            
            if rail_emissions < truck_emissions * 0.7:  # 30% or more savings
                savings_percent = ((truck_emissions - rail_emissions) / truck_emissions) * 100
                suggestions.append({
                    "type": "modal_shift",
                    "recommendation": f"Switch from road to rail transport",
                    "impact": f"Reduce emissions by {savings_percent:.1f}%",
                    "priority": "high"
                })
    
    # Load factor optimization
    if "load_factor" in transport_data and transport_data["load_factor"] < 0.8:
        suggestions.append({
            "type": "load_optimization",
            "recommendation": "Improve load factor through better logistics planning",
            "impact": f"Current utilization: {transport_data['load_factor']*100:.1f}%",
            "priority": "medium"
        })
    
    # Multimodal opportunities
    if transport_data.get("distance_km", 0) > 500:
        suggestions.append({
            "type": "multimodal",
            "recommendation": "Consider multimodal transport (rail + truck) for long distances",
            "impact": "Potential 20-40% emission reduction",
            "priority": "medium"
        })
    
    # Regional specific suggestions
    if region in INDIA_TRANSPORT_PREFERENCES:
        prefs = INDIA_TRANSPORT_PREFERENCES[region]
        if "coastal_shipping" in prefs["preferred"]:
            suggestions.append({
                "type": "regional_optimization",
                "recommendation": "Utilize coastal shipping where available",
                "impact": "Up to 75% lower emissions than road transport",
                "priority": "high"
            })
    
    return suggestions

# Validation and testing
if __name__ == "__main__":
    # Test single mode transport
    truck_result = calculate_transport_emissions(100, 500, "truck_heavy")
    print(f"Truck transport (100t, 500km): {truck_result['total_emissions_kg_co2e']:.2f} kg CO2e")
    
    # Test mode comparison
    modes = ["truck_heavy", "rail_freight", "coastal_shipping"]
    comparison = compare_transport_modes(100, 500, modes)
    print(f"\nBest transport mode: {comparison['comparison']['best_mode']}")
    print(f"Emission reduction: {comparison['comparison']['reduction_percentage']:.1f}%")
    
    # Test city route
    try:
        route = get_city_route_emissions("mumbai", "delhi", 50)
        print(f"\nMumbai to Delhi route:")
        print(f"Recommended mode: {route['recommended_mode']}")
        print(f"Lowest emissions: {route['route_efficiency']['lowest_emissions_kg_co2e']:.2f} kg CO2e")
    except ValueError as e:
        print(f"Route error: {e}")
    
    # Test multimodal transport
    legs = [
        {"transport_mode": "truck_heavy", "distance_km": 150, "description": "Factory to rail terminal"},
        {"transport_mode": "rail_freight", "distance_km": 800, "description": "Rail long haul"},
        {"transport_mode": "truck_medium", "distance_km": 75, "description": "Rail terminal to customer"}
    ]
    multimodal = calculate_multimodal_transport(legs, 100)
    print(f"\nMultimodal transport: {multimodal['total_emissions_kg_co2e']:.2f} kg CO2e")