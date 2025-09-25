"""
LCA Agent - Enhanced for comprehensive LCA calculations
Handles energy, emissions, transport, and recycling analysis
"""

import logging
import numpy as np
from typing import Dict, Any, List
from datetime import datetime
import os
from langchain_cerebras import ChatCerebras
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)

class LCAAgent:
    """Enhanced LCA Agent for comprehensive environmental impact assessment"""
    
    def __init__(self, cerebras_api_key: str = None):
        self.cerebras_api_key = cerebras_api_key or os.getenv("CEREBRAS_API_KEY")
        self.llm = ChatCerebras(api_key=self.cerebras_api_key, model="qwen-3-32b") if self.cerebras_api_key else None
        
        # Grid emission factors (kg CO2e/kWh)
        self.grid_emission_factors = {
            "coal": 0.820,
            "gas": 0.490,
            "oil": 0.750,
            "nuclear": 0.012,
            "hydro": 0.024,
            "wind": 0.011,
            "solar": 0.041,
            "other": 0.200  # Average for other renewables
        }
    
    def perform_lca_analysis(self, production_data: Dict[str, Any], 
                           analysis_type: str = "cradle_to_gate") -> Dict[str, Any]:
        """Perform comprehensive LCA analysis"""
        try:
            logger.info("Starting comprehensive LCA analysis")
            
            # Handle multiple scenarios
            scenarios = production_data.get("scenarios", [production_data])
            results = []
            
            for scenario in scenarios:
                scenario_result = self._analyze_scenario(scenario, analysis_type)
                results.append(scenario_result)
            
            # Aggregate results
            aggregated_results = self._aggregate_results(results)
            
            # Generate AI insights
            ai_insights = self._generate_ai_insights(aggregated_results) if self.llm else {}
            
            return {
                "success": True,
                "analysis_type": analysis_type,
                "timestamp": datetime.now().isoformat(),
                "lca_results": aggregated_results,
                "scenario_results": results,
                "ai_insights": ai_insights,
                "input_parameters": production_data
            }
            
        except Exception as e:
            logger.error(f"LCA analysis error: {e}")
            return {"error": str(e), "success": False}
    
    def _analyze_scenario(self, scenario: Dict[str, Any], analysis_type: str) -> Dict[str, Any]:
        """Analyze a single scenario"""
        
        # Extract scenario parameters
        material_type = scenario.get("material_type", "unknown")
        mass_kg = scenario.get("mass_kg", 0)
        
        # Calculate production emissions
        production_emissions = self._calculate_production_emissions(scenario)
        
        # Calculate transport emissions
        transport_emissions = self._calculate_transport_emissions(scenario)
        
        # Calculate energy-related emissions
        energy_emissions = self._calculate_energy_emissions(scenario)
        
        # Calculate end-of-life and recycling impacts
        eol_emissions = self._calculate_eol_emissions(scenario, analysis_type)
        
        # Calculate total emissions
        total_emissions = {
            "production_kg_co2e": production_emissions["total"],
            "transport_kg_co2e": transport_emissions["total"],
            "energy_kg_co2e": energy_emissions["total"],
            "end_of_life_kg_co2e": eol_emissions["total"],
            "total_kg_co2e": (
                production_emissions["total"] + 
                transport_emissions["total"] + 
                energy_emissions["total"] + 
                eol_emissions["total"]
            )
        }
        
        # Calculate per-kg impact
        per_kg_impact = total_emissions["total_kg_co2e"] / mass_kg if mass_kg > 0 else 0
        
        # Calculate circularity metrics
        circularity_metrics = self._calculate_circularity_metrics(scenario)
        
        return {
            "scenario_id": scenario.get("scenario_id", "unknown"),
            "material_type": material_type,
            "mass_kg": mass_kg,
            "total_emissions": total_emissions,
            "emissions_per_kg": per_kg_impact,
            "production_breakdown": production_emissions,
            "transport_breakdown": transport_emissions,
            "energy_breakdown": energy_emissions,
            "eol_breakdown": eol_emissions,
            "circularity_metrics": circularity_metrics
        }
    
    def _calculate_production_emissions(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate production-related emissions"""
        
        mass_kg = scenario.get("mass_kg", 0)
        recycling = scenario.get("recycling", {})
        direct_emissions = scenario.get("direct_emissions", {})
        material_ef = scenario.get("material_emission_factors", {})
        
        # Calculate recycled vs virgin content
        recycled_fraction = recycling.get("secondary_content_existing_pct", 0) / 100
        virgin_fraction = 1 - recycled_fraction
        
        # Production emissions
        virgin_emissions = virgin_fraction * mass_kg * (
            direct_emissions.get("virgin_kg_co2e_per_kg", 0) + 
            material_ef.get("virgin_kg_co2e_per_kg", 0)
        )
        
        recycled_emissions = recycled_fraction * mass_kg * (
            direct_emissions.get("recycled_kg_co2e_per_kg", 0) + 
            material_ef.get("secondary_kg_co2e_per_kg", 0)
        )
        
        return {
            "virgin_emissions_kg_co2e": virgin_emissions,
            "recycled_emissions_kg_co2e": recycled_emissions,
            "total": virgin_emissions + recycled_emissions,
            "virgin_fraction": virgin_fraction,
            "recycled_fraction": recycled_fraction
        }
    
    def _calculate_transport_emissions(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate transport-related emissions"""
        
        transport = scenario.get("transport", {})
        
        distance_km = transport.get("distance_km", 0)
        weight_t = transport.get("weight_t", 0)
        ef_kg_co2e_per_tkm = transport.get("emission_factor_kg_co2e_per_tkm", 0)
        
        total_transport_emissions = distance_km * weight_t * ef_kg_co2e_per_tkm
        
        return {
            "mode": transport.get("mode", "unknown"),
            "distance_km": distance_km,
            "weight_t": weight_t,
            "emission_factor": ef_kg_co2e_per_tkm,
            "total": total_transport_emissions
        }
    
    def _calculate_energy_emissions(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate energy-related emissions based on grid composition"""
        
        mass_kg = scenario.get("mass_kg", 0)
        energy_intensity = scenario.get("energy_intensity", {})
        grid_composition = scenario.get("grid_composition", {})
        recycling = scenario.get("recycling", {})
        
        # Calculate recycled fraction
        recycled_fraction = recycling.get("secondary_content_existing_pct", 0) / 100
        virgin_fraction = 1 - recycled_fraction
        
        # Energy consumption
        virgin_energy_kwh = virgin_fraction * mass_kg * energy_intensity.get("virgin_process_kwh_per_kg", 0)
        recycled_energy_kwh = recycled_fraction * mass_kg * energy_intensity.get("recycled_process_kwh_per_kg", 0)
        total_energy_kwh = virgin_energy_kwh + recycled_energy_kwh
        
        # Calculate grid emission factor
        grid_ef = 0
        for source, percentage in grid_composition.items():
            source_clean = source.replace("_pct", "")
            if source_clean in self.grid_emission_factors:
                grid_ef += (percentage / 100) * self.grid_emission_factors[source_clean]
        
        # Energy emissions
        energy_emissions = total_energy_kwh * grid_ef
        
        return {
            "virgin_energy_kwh": virgin_energy_kwh,
            "recycled_energy_kwh": recycled_energy_kwh,
            "total_energy_kwh": total_energy_kwh,
            "grid_emission_factor": grid_ef,
            "total": energy_emissions,
            "grid_breakdown": {source: (pct/100) * self.grid_emission_factors.get(source.replace("_pct", ""), 0) 
                             for source, pct in grid_composition.items()}
        }
    
    def _calculate_eol_emissions(self, scenario: Dict[str, Any], analysis_type: str) -> Dict[str, Any]:
        """Calculate end-of-life emissions (for cradle-to-grave analysis)"""
        
        if analysis_type != "cradle_to_grave":
            return {"total": 0, "note": f"EOL not included in {analysis_type} analysis"}
        
        mass_kg = scenario.get("mass_kg", 0)
        recycling = scenario.get("recycling", {})
        
        # Collection and recycling
        collection_rate = recycling.get("collection_rate_pct", 0) / 100
        recycling_efficiency = recycling.get("recycling_efficiency_pct", 0) / 100
        
        # Calculate recycling credits (simplified)
        recycling_credits = mass_kg * collection_rate * recycling_efficiency * 0.5  # Assume 50% credit
        
        # Disposal emissions for non-recycled portion
        disposal_emissions = mass_kg * (1 - collection_rate * recycling_efficiency) * 0.1  # Assume 0.1 kg CO2e/kg disposal
        
        return {
            "recycling_credits_kg_co2e": -recycling_credits,  # Negative because it's a credit
            "disposal_emissions_kg_co2e": disposal_emissions,
            "total": disposal_emissions - recycling_credits,
            "collection_rate": collection_rate,
            "recycling_efficiency": recycling_efficiency
        }
    
    def _calculate_circularity_metrics(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate circular economy metrics"""
        
        recycling = scenario.get("recycling", {})
        
        # Input circularity (recycled content)
        recycled_content = recycling.get("secondary_content_existing_pct", 0) / 100
        
        # Output circularity (collection and recycling rates)
        collection_rate = recycling.get("collection_rate_pct", 0) / 100
        recycling_efficiency = recycling.get("recycling_efficiency_pct", 0) / 100
        output_circularity = collection_rate * recycling_efficiency
        
        # Overall circularity index
        circularity_index = (recycled_content + output_circularity) / 2
        
        return {
            "recycled_content": recycled_content,
            "collection_rate": collection_rate,
            "recycling_efficiency": recycling_efficiency,
            "output_circularity": output_circularity,
            "circularity_index": circularity_index,
            "circularity_grade": self._get_circularity_grade(circularity_index)
        }
    
    def _get_circularity_grade(self, index: float) -> str:
        """Get circularity grade based on index"""
        if index >= 0.8:
            return "A"
        elif index >= 0.6:
            return "B"
        elif index >= 0.4:
            return "C"
        elif index >= 0.2:
            return "D"
        else:
            return "F"
    
    def _aggregate_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate results from multiple scenarios"""
        
        if not results:
            return {}
        
        if len(results) == 1:
            result = results[0]
            return {
                "input_parameters": {
                    "material_type": result["material_type"],
                    "total_mass_kg": result["mass_kg"],
                    "analysis_type": "single_scenario"
                },
                "gwp_impact": {
                    "total_kg_co2_eq": result["total_emissions"]["total_kg_co2e"],
                    "kg_co2_eq_per_kg_material": result["emissions_per_kg"]
                },
                "emissions_breakdown": result["total_emissions"],
                "production_breakdown": result["production_breakdown"],
                "transport_breakdown": result["transport_breakdown"],
                "energy_breakdown": result["energy_breakdown"],
                "circularity_metrics": result["circularity_metrics"]
            }
        
        # Multi-scenario aggregation
        total_mass = sum(r["mass_kg"] for r in results)
        total_emissions = sum(r["total_emissions"]["total_kg_co2e"] for r in results)
        
        # Weighted averages
        weighted_circularity = sum(r["circularity_metrics"]["circularity_index"] * r["mass_kg"] for r in results) / total_mass
        
        return {
            "input_parameters": {
                "scenarios_count": len(results),
                "total_mass_kg": total_mass,
                "materials": list(set(r["material_type"] for r in results)),
                "analysis_type": "multi_scenario"
            },
            "gwp_impact": {
                "total_kg_co2_eq": total_emissions,
                "kg_co2_eq_per_kg_material": total_emissions / total_mass if total_mass > 0 else 0
            },
            "emissions_breakdown": {
                "production_kg_co2e": sum(r["total_emissions"]["production_kg_co2e"] for r in results),
                "transport_kg_co2e": sum(r["total_emissions"]["transport_kg_co2e"] for r in results),
                "energy_kg_co2e": sum(r["total_emissions"]["energy_kg_co2e"] for r in results),
                "end_of_life_kg_co2e": sum(r["total_emissions"]["end_of_life_kg_co2e"] for r in results),
                "total_kg_co2e": total_emissions
            },
            "circularity_metrics": {
                "weighted_circularity_index": weighted_circularity,
                "circularity_grade": self._get_circularity_grade(weighted_circularity)
            }
        }
    
    def _generate_ai_insights(self, lca_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI-powered insights"""
        try:
            gwp_impact = lca_results.get("gwp_impact", {})
            emissions_breakdown = lca_results.get("emissions_breakdown", {})
            circularity = lca_results.get("circularity_metrics", {})
            
            # Calculate sustainability score
            total_emissions = gwp_impact.get("total_kg_co2_eq", 0)
            emissions_per_kg = gwp_impact.get("kg_co2_eq_per_kg_material", 0)
            circularity_index = circularity.get("weighted_circularity_index", circularity.get("circularity_index", 0))
            
            # Scoring algorithm (0-100)
            # Lower emissions = higher score, higher circularity = higher score
            emission_score = max(0, min(100, 100 - (emissions_per_kg * 5)))  # Normalize emissions
            circularity_score = circularity_index * 100
            
            sustainability_score = (emission_score * 0.6 + circularity_score * 0.4)
            
            return {
                "sustainability_score": {
                    "overall_score": sustainability_score,
                    "emission_score": emission_score,
                    "circularity_score": circularity_score,
                    "grade": self._get_sustainability_grade(sustainability_score)
                },
                "key_recommendations": self._generate_recommendations(lca_results),
                "hotspots": self._identify_hotspots(emissions_breakdown)
            }
            
        except Exception as e:
            logger.error(f"AI insights generation error: {e}")
            return {"error": str(e)}
    
    def _get_sustainability_grade(self, score: float) -> str:
        """Get sustainability grade"""
        if score >= 80:
            return "A"
        elif score >= 70:
            return "B"
        elif score >= 60:
            return "C"
        elif score >= 50:
            return "D"
        else:
            return "F"
    
    def _generate_recommendations(self, lca_results: Dict[str, Any]) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        
        emissions_breakdown = lca_results.get("emissions_breakdown", {})
        circularity = lca_results.get("circularity_metrics", {})
        
        total_emissions = emissions_breakdown.get("total_kg_co2e", 0)
        
        # Check major emission sources
        if total_emissions > 0:
            production_pct = (emissions_breakdown.get("production_kg_co2e", 0) / total_emissions) * 100
            energy_pct = (emissions_breakdown.get("energy_kg_co2e", 0) / total_emissions) * 100
            transport_pct = (emissions_breakdown.get("transport_kg_co2e", 0) / total_emissions) * 100
            
            if production_pct > 50:
                recommendations.append("Focus on production process optimization and increased recycled content")
            if energy_pct > 30:
                recommendations.append("Consider renewable energy sources to reduce grid emissions")
            if transport_pct > 20:
                recommendations.append("Optimize transportation routes and consider lower-emission transport modes")
        
        # Circularity recommendations
        circularity_index = circularity.get("weighted_circularity_index", circularity.get("circularity_index", 0))
        if circularity_index < 0.5:
            recommendations.append("Improve circular economy practices through better collection and recycling")
        
        return recommendations
    
    def _identify_hotspots(self, emissions_breakdown: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify emission hotspots"""
        hotspots = []
        
        total_emissions = emissions_breakdown.get("total_kg_co2e", 0)
        if total_emissions == 0:
            return hotspots
        
        categories = [
            ("Production", emissions_breakdown.get("production_kg_co2e", 0)),
            ("Energy", emissions_breakdown.get("energy_kg_co2e", 0)),
            ("Transport", emissions_breakdown.get("transport_kg_co2e", 0)),
            ("End-of-Life", emissions_breakdown.get("end_of_life_kg_co2e", 0))
        ]
        
        for category, emissions in categories:
            percentage = (emissions / total_emissions) * 100
            if percentage > 25:  # Consider >25% as hotspot
                hotspots.append({
                    "category": category,
                    "emissions_kg_co2e": emissions,
                    "percentage": percentage,
                    "priority": "High" if percentage > 50 else "Medium"
                })
        
        return sorted(hotspots, key=lambda x: x["percentage"], reverse=True)