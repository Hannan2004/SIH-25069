"""
LCA Agent - Performs actual LCA calculations with GWP constants
Enhanced with Cerebras AI for intelligent analysis and recommendations
"""

from typing import Dict, List, Optional, Any, Union
import pandas as pd
import numpy as np
import logging
import os
import sys
import json
from datetime import datetime

# Add tools to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from langchain_core.tools import tool
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_cerebras import ChatCerebras

logger = logging.getLogger(__name__)

# GWP Constants (kg CO2-eq per kg)
GWP_VALUES = {
    "CO2": 1.0,
    "CH4": 25.0,
    "N2O": 298.0,
    "SF6": 22800.0,
    "CF4": 7390.0,
    "C2F6": 12200.0,
    "HFC-134a": 1430.0,
    "HFC-152a": 124.0,
    "PFC-14": 7390.0,
    "PFC-116": 12200.0,
    "SO2": 0.0,  # Not a GHG but air pollutant
    "NOx": 0.0,  # Not a GHG but air pollutant
}

# Process gas emissions for metal production (kg gas per kg metal)
ALUMINUM_PROCESS_GASES = {
    "primary_production": {
        "CO2": 1.67,  # Direct CO2 from anode consumption
        "CF4": 0.00008,  # Tetrafluoromethane from anode effects
        "C2F6": 0.000008,  # Hexafluoroethane from anode effects
        "SO2": 0.035,  # Sulfur dioxide
        "NOx": 0.0015,  # Nitrogen oxides
    },
    "secondary_production": {
        "CO2": 0.95,  # Lower CO2 for recycling
        "SO2": 0.008,  # Lower SO2 for recycling
        "NOx": 0.0005,  # Lower NOx for recycling
    }
}

COPPER_PROCESS_GASES = {
    "primary_production": {
        "CO2": 2.85,  # Higher CO2 for copper smelting
        "SO2": 1.25,  # High SO2 from sulfide ores
        "NOx": 0.008,  # Nitrogen oxides
    },
    "secondary_production": {
        "CO2": 0.75,  # Lower for scrap processing
        "SO2": 0.15,  # Much lower SO2
        "NOx": 0.002,  # Lower NOx
    }
}

# Energy intensity factors (MJ per kg metal)
ENERGY_INTENSITY = {
    "aluminum": {
        "primary": 170.0,  # MJ/kg for primary aluminum
        "secondary": 17.0,  # MJ/kg for secondary aluminum
    },
    "copper": {
        "primary": 65.0,  # MJ/kg for primary copper
        "secondary": 12.0,  # MJ/kg for secondary copper
    }
}

# Regional electricity emission factors (kg CO2/MJ)
ELECTRICITY_EMISSION_FACTORS = {
    "china": 0.195,
    "usa": 0.138,
    "europe": 0.098,
    "india": 0.201,
    "japan": 0.128,
    "canada": 0.048,
    "australia": 0.186,
    "brazil": 0.032,
    "national_average": 0.145,  # Global average
    "default": 0.145
}

def normalize_metal_type(metal_type: str) -> str:
    """Normalize metal type string"""
    if not metal_type:
        return "aluminum"
    
    metal = str(metal_type).lower().strip()
    if metal in ["al", "aluminium", "aluminum"]:
        return "aluminum"
    elif metal in ["cu", "copper"]:
        return "copper"
    else:
        return "aluminum"  # Default fallback

def normalize_region(region: str) -> str:
    """Normalize region string"""
    if not region:
        return "national_average"
    
    region = str(region).lower().strip().replace(" ", "_").replace("-", "_")
    
    # Map common variations
    region_mapping = {
        "united_states": "usa",
        "us": "usa",
        "america": "usa",
        "european_union": "europe",
        "eu": "europe",
        "prc": "china",
        "peoples_republic_of_china": "china",
        "commonwealth_of_australia": "australia",
        "aus": "australia",
        "can": "canada",
        "jpn": "japan",
        "ind": "india",
        "bra": "brazil"
    }
    
    return region_mapping.get(region, region if region in ELECTRICITY_EMISSION_FACTORS else "national_average")

class LCAAgent:
    """Enhanced LCA Agent with Cerebras AI integration"""
    
    def __init__(self, cerebras_api_key: str = None):
        # Initialize ChatCerebras
        self.cerebras_api_key = cerebras_api_key or os.getenv("CEREBRAS_API_KEY")
        self.llm = ChatCerebras(
            api_key=self.cerebras_api_key,
            model="qwen-3-32b",
        ) if self.cerebras_api_key else None
        
        # Initialize calculation parameters
        self.gwp_values = GWP_VALUES
        self.aluminum_gases = ALUMINUM_PROCESS_GASES
        self.copper_gases = COPPER_PROCESS_GASES
        self.energy_intensity = ENERGY_INTENSITY
        self.electricity_factors = ELECTRICITY_EMISSION_FACTORS
        
    def perform_lca_analysis(self, data: Dict[str, Any], 
                           analysis_type: str = "comprehensive") -> Dict[str, Any]:
        """
        Perform comprehensive LCA analysis with AI insights
        
        Args:
            data: Input data containing metal production information
            analysis_type: Type of analysis ('quick', 'detailed', 'comprehensive')
            
        Returns:
            Dict: Complete LCA analysis results with AI insights
        """
        
        try:
            # Validate inputs
            validation_result = self._validate_inputs(data)
            if not validation_result["valid"]:
                return {"error": validation_result["errors"], "success": False}
            
            # Perform core LCA calculations
            lca_results = self._calculate_lca(data, analysis_type)
            
            # Generate scenarios if comprehensive analysis
            scenarios = {}
            if analysis_type == "comprehensive":
                scenarios = self._generate_scenarios(data)
            
            # Generate AI insights
            ai_insights = self._generate_ai_lca_insights(data, lca_results, scenarios) if self.llm else {}
            
            return {
                "success": True,
                "lca_results": lca_results,
                "scenarios": scenarios,
                "ai_insights": ai_insights,
                "analysis_metadata": {
                    "analysis_type": analysis_type,
                    "calculation_timestamp": datetime.now().isoformat(),
                    "data_points_analyzed": len(data.get("production_data", [])),
                    "gwp_methodology": "IPCC AR4 100-year GWP values"
                }
            }
            
        except Exception as e:
            logger.error(f"Error in LCA analysis: {e}")
            return {"error": str(e), "success": False}
    
    def _validate_inputs(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate input data for LCA calculations"""
        
        errors = []
        warnings = []
        
        # Check required fields
        required_fields = ["metal_type", "production_kg", "recycled_fraction"]
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        # Validate data types and ranges
        if "production_kg" in data:
            try:
                production_kg = float(data["production_kg"])
                if production_kg <= 0:
                    errors.append("production_kg must be positive")
                elif production_kg > 1e9:
                    warnings.append("Very large production quantity detected")
            except (ValueError, TypeError):
                errors.append("production_kg must be a number")
        
        if "recycled_fraction" in data:
            try:
                recycled_fraction = float(data["recycled_fraction"])
                if not 0 <= recycled_fraction <= 1:
                    errors.append("recycled_fraction must be between 0 and 1")
            except (ValueError, TypeError):
                errors.append("recycled_fraction must be a number")
        
        # Validate metal type
        if "metal_type" in data:
            normalized_metal = normalize_metal_type(data["metal_type"])
            if normalized_metal not in ["aluminum", "copper"]:
                warnings.append(f"Metal type '{data['metal_type']}' not fully supported, using aluminum defaults")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def _calculate_lca(self, data: Dict[str, Any], analysis_type: str) -> Dict[str, Any]:
        """Perform core LCA calculations"""
        
        # Normalize inputs
        metal_type = normalize_metal_type(data.get("metal_type", "aluminum"))
        production_kg = float(data.get("production_kg", 0))
        recycled_fraction = float(data.get("recycled_fraction", 0))
        region = normalize_region(data.get("region", "national_average"))
        
        # Calculate primary and secondary production
        primary_fraction = 1 - recycled_fraction
        primary_production_kg = production_kg * primary_fraction
        secondary_production_kg = production_kg * recycled_fraction
        
        # Get process gas emissions
        if metal_type == "aluminum":
            primary_gases = self.aluminum_gases["primary_production"]
            secondary_gases = self.aluminum_gases["secondary_production"]
        else:  # copper
            primary_gases = self.copper_gases["primary_production"]
            secondary_gases = self.copper_gases["secondary_production"]
        
        # Calculate direct process emissions
        direct_emissions = self._calculate_direct_emissions(
            primary_production_kg, secondary_production_kg, 
            primary_gases, secondary_gases
        )
        
        # Calculate energy-related emissions
        energy_emissions = self._calculate_energy_emissions(
            metal_type, primary_production_kg, secondary_production_kg, region
        )
        
        # Calculate total emissions
        total_emissions = self._sum_emissions(direct_emissions, energy_emissions)
        
        # Calculate emission factors (per kg of metal)
        emission_factors = {
            gas: total_emissions[gas] / production_kg if production_kg > 0 else 0
            for gas in total_emissions
        }
        
        # Calculate GWP impact
        gwp_impact = self._calculate_gwp_impact(total_emissions)
        gwp_factor = gwp_impact / production_kg if production_kg > 0 else 0
        
        results = {
            "input_parameters": {
                "metal_type": metal_type,
                "production_kg": production_kg,
                "recycled_fraction": recycled_fraction,
                "primary_production_kg": primary_production_kg,
                "secondary_production_kg": secondary_production_kg,
                "region": region
            },
            "direct_emissions": direct_emissions,
            "energy_emissions": energy_emissions,
            "total_emissions": total_emissions,
            "emission_factors": emission_factors,
            "gwp_impact": {
                "total_kg_co2_eq": gwp_impact,
                "kg_co2_eq_per_kg_metal": gwp_factor
            },
            "production_breakdown": {
                "primary_percentage": primary_fraction * 100,
                "secondary_percentage": recycled_fraction * 100,
                "primary_emissions_kg_co2_eq": self._calculate_gwp_impact(
                    self._calculate_direct_emissions(primary_production_kg, 0, primary_gases, {})
                ),
                "secondary_emissions_kg_co2_eq": self._calculate_gwp_impact(
                    self._calculate_direct_emissions(0, secondary_production_kg, {}, secondary_gases)
                )
            }
        }
        
        # Add detailed analysis if requested
        if analysis_type in ["detailed", "comprehensive"]:
            results["detailed_analysis"] = self._detailed_analysis(results)
        
        return results
    
    def _calculate_direct_emissions(self, primary_kg: float, secondary_kg: float,
                                  primary_gases: Dict[str, float], 
                                  secondary_gases: Dict[str, float]) -> Dict[str, float]:
        """Calculate direct process emissions"""
        
        emissions = {}
        
        # Primary production emissions
        for gas, factor in primary_gases.items():
            emissions[gas] = emissions.get(gas, 0) + primary_kg * factor
        
        # Secondary production emissions
        for gas, factor in secondary_gases.items():
            emissions[gas] = emissions.get(gas, 0) + secondary_kg * factor
        
        return emissions
    
    def _calculate_energy_emissions(self, metal_type: str, primary_kg: float, 
                                  secondary_kg: float, region: str) -> Dict[str, float]:
        """Calculate energy-related emissions"""
        
        # Get energy intensities
        primary_energy = self.energy_intensity[metal_type]["primary"]  # MJ/kg
        secondary_energy = self.energy_intensity[metal_type]["secondary"]  # MJ/kg
        
        # Calculate total energy consumption
        total_energy_mj = (primary_kg * primary_energy) + (secondary_kg * secondary_energy)
        
        # Get electricity emission factor
        emission_factor = self.electricity_factors.get(region, self.electricity_factors["default"])
        
        # Calculate CO2 emissions from electricity
        energy_co2 = total_energy_mj * emission_factor
        
        return {
            "CO2": energy_co2,
            "energy_consumption_mj": total_energy_mj,
            "electricity_emission_factor": emission_factor
        }
    
    def _sum_emissions(self, direct: Dict[str, float], energy: Dict[str, float]) -> Dict[str, float]:
        """Sum direct and energy emissions"""
        
        total = direct.copy()
        
        # Add energy CO2 to direct CO2
        total["CO2"] = total.get("CO2", 0) + energy.get("CO2", 0)
        
        # Add energy metadata
        total["energy_consumption_mj"] = energy.get("energy_consumption_mj", 0)
        total["electricity_emission_factor"] = energy.get("electricity_emission_factor", 0)
        
        return total
    
    def _calculate_gwp_impact(self, emissions: Dict[str, float]) -> float:
        """Calculate total GWP impact in kg CO2-eq"""
        
        gwp_impact = 0.0
        
        for gas, amount in emissions.items():
            if gas in self.gwp_values:
                gwp_impact += amount * self.gwp_values[gas]
        
        return gwp_impact
    
    def _detailed_analysis(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Perform detailed analysis on results"""
        
        total_emissions = results["total_emissions"]
        gwp_impact = results["gwp_impact"]["total_kg_co2_eq"]
        
        # Emission source breakdown
        emission_breakdown = {}
        for gas, amount in total_emissions.items():
            if gas in self.gwp_values and amount > 0:
                gas_gwp = amount * self.gwp_values[gas]
                emission_breakdown[gas] = {
                    "amount_kg": amount,
                    "gwp_kg_co2_eq": gas_gwp,
                    "percentage_of_total": (gas_gwp / gwp_impact * 100) if gwp_impact > 0 else 0
                }
        
        # Benchmarking
        metal_type = results["input_parameters"]["metal_type"]
        benchmark_data = self._get_benchmark_data(metal_type)
        
        return {
            "emission_breakdown": emission_breakdown,
            "benchmark_comparison": benchmark_data,
            "hotspot_analysis": self._identify_hotspots(emission_breakdown),
            "improvement_potential": self._calculate_improvement_potential(results)
        }
    
    def _get_benchmark_data(self, metal_type: str) -> Dict[str, Any]:
        """Get industry benchmark data"""
        
        benchmarks = {
            "aluminum": {
                "industry_average_kg_co2_per_kg": 11.5,
                "best_practice_kg_co2_per_kg": 7.2,
                "worst_case_kg_co2_per_kg": 18.3,
                "recycling_average_kg_co2_per_kg": 1.8
            },
            "copper": {
                "industry_average_kg_co2_per_kg": 4.6,
                "best_practice_kg_co2_per_kg": 2.8,
                "worst_case_kg_co2_per_kg": 8.2,
                "recycling_average_kg_co2_per_kg": 1.2
            }
        }
        
        return benchmarks.get(metal_type, benchmarks["aluminum"])
    
    def _identify_hotspots(self, emission_breakdown: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify emission hotspots"""
        
        hotspots = []
        
        # Sort by GWP contribution
        sorted_gases = sorted(
            emission_breakdown.items(),
            key=lambda x: x[1]["gwp_kg_co2_eq"],
            reverse=True
        )
        
        for gas, data in sorted_gases[:3]:  # Top 3 contributors
            if data["percentage_of_total"] > 5:  # Only significant contributors
                hotspots.append({
                    "emission_source": gas,
                    "contribution_percentage": data["percentage_of_total"],
                    "improvement_priority": "high" if data["percentage_of_total"] > 50 else "medium"
                })
        
        return hotspots
    
    def _calculate_improvement_potential(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate improvement potential through recycling"""
        
        params = results["input_parameters"]
        current_recycling = params["recycled_fraction"]
        
        # Calculate potential improvements
        scenarios = {}
        for target_recycling in [0.3, 0.5, 0.7, 0.9]:
            if target_recycling > current_recycling:
                # Recalculate with higher recycling rate
                improved_data = params.copy()
                improved_data["recycled_fraction"] = target_recycling
                
                improved_results = self._calculate_lca(improved_data, "quick")
                current_gwp = results["gwp_impact"]["kg_co2_eq_per_kg_metal"]
                improved_gwp = improved_results["gwp_impact"]["kg_co2_eq_per_kg_metal"]
                
                reduction_percentage = ((current_gwp - improved_gwp) / current_gwp * 100) if current_gwp > 0 else 0
                
                scenarios[f"{int(target_recycling*100)}%_recycling"] = {
                    "kg_co2_eq_per_kg_metal": improved_gwp,
                    "reduction_percentage": reduction_percentage,
                    "absolute_reduction_kg_co2_eq_per_kg": current_gwp - improved_gwp
                }
        
        return scenarios
    
    def _generate_scenarios(self, data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Generate comparison scenarios"""
        
        base_data = data.copy()
        scenarios = {}
        
        # Scenario 1: 100% Primary production
        primary_data = base_data.copy()
        primary_data["recycled_fraction"] = 0.0
        scenarios["100_percent_primary"] = self._calculate_lca(primary_data, "detailed")
        
        # Scenario 2: 50% Recycled content
        recycled_50_data = base_data.copy()
        recycled_50_data["recycled_fraction"] = 0.5
        scenarios["50_percent_recycled"] = self._calculate_lca(recycled_50_data, "detailed")
        
        # Scenario 3: 90% Recycled content
        recycled_90_data = base_data.copy()
        recycled_90_data["recycled_fraction"] = 0.9
        scenarios["90_percent_recycled"] = self._calculate_lca(recycled_90_data, "detailed")
        
        # Scenario 4: Different region (China - high carbon intensity)
        china_data = base_data.copy()
        china_data["region"] = "china"
        scenarios["china_production"] = self._calculate_lca(china_data, "detailed")
        
        # Scenario 5: Different region (Canada - low carbon intensity)
        canada_data = base_data.copy()
        canada_data["region"] = "canada"
        scenarios["canada_production"] = self._calculate_lca(canada_data, "detailed")
        
        return scenarios
    
    def _generate_ai_lca_insights(self, data: Dict[str, Any], 
                                lca_results: Dict[str, Any],
                                scenarios: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI-powered LCA insights and recommendations"""
        
        if not self.llm:
            return {"error": "AI insights not available - LLM not configured"}
        
        try:
            # Prepare summary for AI
            summary = {
                "metal_type": data.get("metal_type"),
                "production_kg": data.get("production_kg"),
                "recycled_fraction": data.get("recycled_fraction"),
                "region": data.get("region"),
                "total_gwp_kg_co2_eq": lca_results["gwp_impact"]["total_kg_co2_eq"],
                "gwp_per_kg_metal": lca_results["gwp_impact"]["kg_co2_eq_per_kg_metal"],
                "primary_percentage": lca_results["production_breakdown"]["primary_percentage"],
                "top_emission_sources": []
            }
            
            # Add top emission sources if detailed analysis available
            if "detailed_analysis" in lca_results:
                breakdown = lca_results["detailed_analysis"]["emission_breakdown"]
                summary["top_emission_sources"] = [
                    {"gas": gas, "percentage": data["percentage_of_total"]}
                    for gas, data in sorted(breakdown.items(), 
                                          key=lambda x: x[1]["percentage_of_total"], 
                                          reverse=True)[:3]
                ]
            
            system_prompt = """You are an expert LCA analyst specializing in metal production carbon footprints.
            Analyze the provided LCA results and provide insights on:
            
            1. Environmental performance assessment
            2. Key emission drivers and hotspots
            3. Benchmarking against industry standards
            4. Specific recommendations for carbon footprint reduction
            5. Recycling and circular economy opportunities
            6. Regional production strategy recommendations
            
            Focus on actionable, technical recommendations for sustainability improvement.
            Keep response structured and professional."""
            
            user_message = f"Analyze this LCA assessment: {json.dumps(summary, indent=2)}"
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_message)
            ]
            
            response = self.llm.invoke(messages)
            ai_analysis = response.content
            
            # Generate specific recommendations
            recommendations = self._generate_ai_recommendations(lca_results, scenarios)
            
            return {
                "ai_analysis": ai_analysis,
                "sustainability_score": self._calculate_sustainability_score(lca_results),
                "key_recommendations": recommendations,
                "scenario_insights": self._analyze_scenarios_with_ai(scenarios) if scenarios else {},
                "benchmarking_assessment": self._ai_benchmarking_assessment(lca_results)
            }
            
        except Exception as e:
            logger.error(f"Error generating AI LCA insights: {e}")
            return {"error": f"Failed to generate AI insights: {str(e)}"}
    
    def _calculate_sustainability_score(self, lca_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate sustainability score based on LCA results"""
        
        gwp_per_kg = lca_results["gwp_impact"]["kg_co2_eq_per_kg_metal"]
        metal_type = lca_results["input_parameters"]["metal_type"]
        recycled_fraction = lca_results["input_parameters"]["recycled_fraction"]
        
        # Get benchmark
        benchmark = self._get_benchmark_data(metal_type)
        industry_average = benchmark["industry_average_kg_co2_per_kg"]
        best_practice = benchmark["best_practice_kg_co2_per_kg"]
        
        # Calculate performance score (0-100)
        if gwp_per_kg <= best_practice:
            performance_score = 100
        elif gwp_per_kg >= industry_average * 1.5:  # 50% worse than average
            performance_score = 0
        else:
            # Linear interpolation
            performance_score = max(0, 100 * (industry_average * 1.5 - gwp_per_kg) / 
                                  (industry_average * 1.5 - best_practice))
        
        # Recycling bonus
        recycling_score = recycled_fraction * 100
        
        # Overall sustainability score
        sustainability_score = (performance_score * 0.7) + (recycling_score * 0.3)
        
        return {
            "overall_score": round(sustainability_score, 1),
            "performance_score": round(performance_score, 1),
            "recycling_score": round(recycling_score, 1),
            "grade": self._get_sustainability_grade(sustainability_score),
            "benchmark_comparison": {
                "vs_industry_average": round(((industry_average - gwp_per_kg) / industry_average * 100), 1),
                "vs_best_practice": round(((best_practice - gwp_per_kg) / best_practice * 100), 1)
            }
        }
    
    def _get_sustainability_grade(self, score: float) -> str:
        """Convert sustainability score to letter grade"""
        if score >= 90:
            return "A+"
        elif score >= 80:
            return "A"
        elif score >= 70:
            return "B+"
        elif score >= 60:
            return "B"
        elif score >= 50:
            return "C+"
        elif score >= 40:
            return "C"
        elif score >= 30:
            return "D"
        else:
            return "F"
    
    def _generate_ai_recommendations(self, lca_results: Dict[str, Any], 
                                   scenarios: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate specific AI-powered recommendations"""
        
        recommendations = []
        
        params = lca_results["input_parameters"]
        current_recycling = params["recycled_fraction"]
        gwp_per_kg = lca_results["gwp_impact"]["kg_co2_eq_per_kg_metal"]
        
        # Recycling recommendations
        if current_recycling < 0.3:
            recommendations.append({
                "category": "Recycling",
                "priority": "High",
                "action": "Increase recycled content to at least 30%",
                "potential_reduction": "15-25% GWP reduction",
                "implementation": "Source more secondary materials, improve collection systems"
            })
        elif current_recycling < 0.5:
            recommendations.append({
                "category": "Recycling",
                "priority": "Medium",
                "action": "Target 50% recycled content",
                "potential_reduction": "10-15% GWP reduction",
                "implementation": "Expand recycling partnerships, design for recyclability"
            })
        
        # Regional recommendations
        region = params["region"]
        if region in ["china", "india", "australia"]:  # High carbon intensity regions
            recommendations.append({
                "category": "Regional Strategy",
                "priority": "Medium",
                "action": "Consider production in lower carbon intensity regions",
                "potential_reduction": "20-40% GWP reduction",
                "implementation": "Evaluate production facilities in Canada, Europe, or Brazil"
            })
        
        # Technology recommendations
        metal_type = params["metal_type"]
        benchmark = self._get_benchmark_data(metal_type)
        
        if gwp_per_kg > benchmark["industry_average_kg_co2_per_kg"]:
            recommendations.append({
                "category": "Process Efficiency",
                "priority": "High",
                "action": "Implement energy efficiency measures and process optimization",
                "potential_reduction": "10-20% GWP reduction",
                "implementation": "Upgrade equipment, improve process controls, waste heat recovery"
            })
        
        return recommendations
    
    def _analyze_scenarios_with_ai(self, scenarios: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze scenarios to provide insights"""
        
        scenario_comparison = {}
        
        for scenario_name, scenario_data in scenarios.items():
            gwp_per_kg = scenario_data["gwp_impact"]["kg_co2_eq_per_kg_metal"]
            scenario_comparison[scenario_name] = {
                "gwp_per_kg_metal": gwp_per_kg,
                "sustainability_score": self._calculate_sustainability_score(scenario_data)["overall_score"]
            }
        
        # Find best and worst scenarios
        best_scenario = min(scenario_comparison.items(), key=lambda x: x[1]["gwp_per_kg_metal"])
        worst_scenario = max(scenario_comparison.items(), key=lambda x: x[1]["gwp_per_kg_metal"])
        
        return {
            "scenario_comparison": scenario_comparison,
            "best_scenario": {
                "name": best_scenario[0],
                "gwp_per_kg": best_scenario[1]["gwp_per_kg_metal"]
            },
            "worst_scenario": {
                "name": worst_scenario[0],  
                "gwp_per_kg": worst_scenario[1]["gwp_per_kg_metal"]
            },
            "improvement_potential": round(
                ((worst_scenario[1]["gwp_per_kg_metal"] - best_scenario[1]["gwp_per_kg_metal"]) /
                 worst_scenario[1]["gwp_per_kg_metal"] * 100), 1
            )
        }
    
    def _ai_benchmarking_assessment(self, lca_results: Dict[str, Any]) -> Dict[str, Any]:
        """AI-powered benchmarking assessment"""
        
        metal_type = lca_results["input_parameters"]["metal_type"]
        gwp_per_kg = lca_results["gwp_impact"]["kg_co2_eq_per_kg_metal"]
        benchmark = self._get_benchmark_data(metal_type)
        
        performance_level = "poor"
        if gwp_per_kg <= benchmark["best_practice_kg_co2_per_kg"]:
            performance_level = "excellent"
        elif gwp_per_kg <= benchmark["industry_average_kg_co2_per_kg"]:
            performance_level = "good"
        elif gwp_per_kg <= benchmark["industry_average_kg_co2_per_kg"] * 1.2:
            performance_level = "average"
        
        return {
            "performance_level": performance_level,
            "benchmark_data": benchmark,
            "current_performance": gwp_per_kg,
            "gap_to_best_practice": gwp_per_kg - benchmark["best_practice_kg_co2_per_kg"],
            "improvement_target": benchmark["best_practice_kg_co2_per_kg"]
        }

# LCA Calculation Tools
@tool
def calculate_total_lca_emissions(metal_type: str, production_kg: float, 
                                recycled_fraction: float, region: str = "national_average") -> Dict[str, Any]:
    """Calculate total LCA emissions for metal production"""
    agent = LCAAgent()
    
    data = {
        "metal_type": metal_type,
        "production_kg": production_kg,
        "recycled_fraction": recycled_fraction,
        "region": region
    }
    
    return agent.perform_lca_analysis(data, "detailed")

@tool
def quick_lca_calculation(metal_type: str, production_kg: float, 
                        recycled_fraction: float) -> Dict[str, Any]:
    """Quick LCA calculation for basic carbon footprint"""
    agent = LCAAgent()
    
    data = {
        "metal_type": metal_type,
        "production_kg": production_kg,
        "recycled_fraction": recycled_fraction
    }
    
    result = agent.perform_lca_analysis(data, "quick")
    
    if result.get("success"):
        return {
            "kg_co2_eq_total": result["lca_results"]["gwp_impact"]["total_kg_co2_eq"],
            "kg_co2_eq_per_kg_metal": result["lca_results"]["gwp_impact"]["kg_co2_eq_per_kg_metal"],
            "metal_type": metal_type,
            "production_kg": production_kg,
            "recycled_fraction": recycled_fraction
        }
    else:
        return result

@tool
def compare_lca_scenarios(base_data: Dict[str, Any], scenario_modifications: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compare multiple LCA scenarios"""
    agent = LCAAgent()
    
    results = {}
    
    # Calculate base scenario
    base_result = agent.perform_lca_analysis(base_data, "detailed")
    if base_result.get("success"):
        results["base_scenario"] = base_result["lca_results"]
    
    # Calculate modified scenarios
    for i, modification in enumerate(scenario_modifications):
        scenario_data = base_data.copy()
        scenario_data.update(modification)
        
        scenario_result = agent.perform_lca_analysis(scenario_data, "detailed")
        if scenario_result.get("success"):
            results[f"scenario_{i+1}"] = scenario_result["lca_results"]
    
    return results

@tool
def validate_calculation_inputs(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate LCA calculation inputs"""
    agent = LCAAgent()
    return agent._validate_inputs(data)

@tool
def calculate_benchmark_comparison(metal_type: str, gwp_per_kg: float) -> Dict[str, Any]:
    """Compare GWP performance against industry benchmarks"""
    agent = LCAAgent()
    
    benchmark_data = agent._get_benchmark_data(normalize_metal_type(metal_type))
    
    return {
        "current_gwp_per_kg": gwp_per_kg,
        "industry_benchmarks": benchmark_data,
        "performance_vs_average": round(((benchmark_data["industry_average_kg_co2_per_kg"] - gwp_per_kg) / 
                                       benchmark_data["industry_average_kg_co2_per_kg"] * 100), 1),
        "performance_vs_best_practice": round(((benchmark_data["best_practice_kg_co2_per_kg"] - gwp_per_kg) / 
                                             benchmark_data["best_practice_kg_co2_per_kg"] * 100), 1),
        "improvement_potential_kg_co2": gwp_per_kg - benchmark_data["best_practice_kg_co2_per_kg"]
    }

@tool
def format_lca_results(lca_results: Dict[str, Any], format_type: str = "summary") -> str:
    """Format LCA results for display"""
    
    if not lca_results.get("success"):
        return f"LCA calculation failed: {lca_results.get('error', 'Unknown error')}"
    
    results = lca_results["lca_results"]
    params = results["input_parameters"]
    gwp = results["gwp_impact"]
    
    if format_type == "summary":
        return f"""
LCA Results Summary:
==================
Metal Type: {params['metal_type'].title()}
Production: {params['production_kg']:,.0f} kg
Recycled Content: {params['recycled_fraction']*100:.1f}%
Region: {params['region'].replace('_', ' ').title()}

Carbon Footprint:
- Total: {gwp['total_kg_co2_eq']:,.1f} kg CO2-eq
- Per kg metal: {gwp['kg_co2_eq_per_kg_metal']:.2f} kg CO2-eq/kg

Production Split:
- Primary: {results['production_breakdown']['primary_percentage']:.1f}%
- Secondary: {results['production_breakdown']['secondary_percentage']:.1f}%
"""
    
    elif format_type == "detailed" and "detailed_analysis" in results:
        detailed = results["detailed_analysis"]
        
        emission_details = ""
        for gas, data in detailed["emission_breakdown"].items():
            emission_details += f"- {gas}: {data['amount_kg']:.3f} kg ({data['percentage_of_total']:.1f}% of GWP)\n"
        
        return f"""
Detailed LCA Results:
===================
{format_lca_results(lca_results, "summary")}

Emission Breakdown:
{emission_details}

Sustainability Score: {lca_results.get('ai_insights', {}).get('sustainability_score', {}).get('overall_score', 'N/A')}
"""
    
    return "Invalid format type. Use 'summary' or 'detailed'."