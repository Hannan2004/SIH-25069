"""
GWP (Global Warming Potential) Constants from IPCC Assessment Reports
Used for converting various greenhouse gases to CO2 equivalents in LCA calculations
"""

# IPCC Fifth Assessment Report (AR5) - 100-year GWP values
# Most commonly used in current LCA studies and standards
IPCC_AR5_GWP = {
    # Carbon compounds
    "CO2": 1,
    "CH4": 28,
    "N2O": 265,
    
    # Perfluorocarbons (PFCs) - common in aluminum smelting
    "CF4": 6630,
    "C2F6": 11100,
    "C3F8": 8900,
    "C4F10": 9200,
    "C5F12": 8550,
    "C6F14": 7910,
    
    # Hydrofluorocarbons (HFCs)
    "HFC-23": 12400,
    "HFC-32": 677,
    "HFC-125": 3170,
    "HFC-134a": 1300,
    "HFC-143a": 4800,
    "HFC-152a": 138,
    
    # Sulfur compounds
    "SF6": 23500,
    "SO2F2": 4090,
    
    # Other industrial gases
    "NF3": 16100,
    "PFC-14": 6630,  # Same as CF4
    "PFC-116": 11100,  # Same as C2F6
}

# IPCC Sixth Assessment Report (AR6) - 100-year GWP values
# Latest scientific consensus, updated values
IPCC_AR6_GWP = {
    # Carbon compounds
    "CO2": 1,
    "CH4": 27,  # Updated from AR5
    "N2O": 273,  # Updated from AR5
    
    # Perfluorocarbons (PFCs)
    "CF4": 7380,  # Updated from AR5
    "C2F6": 12400,  # Updated from AR5
    "C3F8": 9290,
    "C4F10": 9650,
    "C5F12": 8960,
    "C6F14": 8300,
    
    # Hydrofluorocarbons (HFCs)
    "HFC-23": 14600,  # Updated from AR5
    "HFC-32": 771,
    "HFC-125": 3740,
    "HFC-134a": 1530,
    "HFC-143a": 5810,
    "HFC-152a": 164,
    
    # Sulfur compounds
    "SF6": 25200,  # Updated from AR5
    "SO2F2": 4780,
    
    # Other industrial gases
    "NF3": 17400,
    "PFC-14": 7380,  # Same as CF4
    "PFC-116": 12400,  # Same as C2F6
}

# Industry-specific GWP mappings for aluminum and copper production
ALUMINUM_PROCESS_GASES = {
    "CF4": "Primary aluminum smelting - anode effect",
    "C2F6": "Primary aluminum smelting - anode effect", 
    "CO2": "Carbon anode consumption",
    "SO2": "Aluminum refining (converted to CO2e using characterization factors)"
}

COPPER_PROCESS_GASES = {
    "CO2": "Copper smelting and refining",
    "SO2": "Copper ore processing and smelting",
    "N2O": "Nitric acid production for copper refining"
}

# Default GWP version to use (can be switched based on study requirements)
DEFAULT_GWP_VERSION = "AR5"

def get_gwp_value(gas_name: str, version: str = DEFAULT_GWP_VERSION) -> float:
    """
    Get GWP value for a specific gas
    
    Args:
        gas_name (str): Chemical formula or name of the gas
        version (str): IPCC version - "AR5" or "AR6"
    
    Returns:
        float: GWP value in kg CO2-eq/kg gas
    
    Raises:
        ValueError: If gas not found or invalid version
    """
    gwp_data = IPCC_AR5_GWP if version == "AR5" else IPCC_AR6_GWP
    
    if version not in ["AR5", "AR6"]:
        raise ValueError(f"Invalid GWP version: {version}. Use 'AR5' or 'AR6'")
    
    if gas_name not in gwp_data:
        raise ValueError(f"GWP value not found for gas: {gas_name}")
    
    return gwp_data[gas_name]

def convert_to_co2_eq(gas_emissions: dict, version: str = DEFAULT_GWP_VERSION) -> float:
    """
    Convert multiple gas emissions to CO2 equivalents
    
    Args:
        gas_emissions (dict): Dictionary of {gas_name: emission_amount_kg}
        version (str): IPCC version to use
    
    Returns:
        float: Total CO2 equivalent emissions in kg
    """
    total_co2_eq = 0.0
    
    for gas, amount in gas_emissions.items():
        gwp = get_gwp_value(gas, version)
        total_co2_eq += amount * gwp
    
    return total_co2_eq

def get_available_gases(version: str = DEFAULT_GWP_VERSION) -> list:
    """
    Get list of available gases for specified GWP version
    
    Args:
        version (str): IPCC version - "AR5" or "AR6"
    
    Returns:
        list: List of available gas names
    """
    gwp_data = IPCC_AR5_GWP if version == "AR5" else IPCC_AR6_GWP
    return list(gwp_data.keys())

# Example usage and validation
if __name__ == "__main__":
    # Test the functions
    print("Available gases in AR5:", len(get_available_gases("AR5")))
    print("Available gases in AR6:", len(get_available_gases("AR6")))
    
    # Example aluminum smelting emissions
    al_emissions = {
        "CO2": 100,  # kg
        "CF4": 0.5,  # kg
        "C2F6": 0.1  # kg
    }
    
    print(f"Total CO2-eq (AR5): {convert_to_co2_eq(al_emissions, 'AR5'):.2f} kg")
    print(f"Total CO2-eq (AR6): {convert_to_co2_eq(al_emissions, 'AR6'):.2f} kg")