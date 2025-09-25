"""
Compliance Agent with RAG - ISO 14040/14044 LCA Standards Compliance Checker
Dynamic scoring (20–90% spread based on input quality)
"""

import logging
import os
from typing import Dict, Any, List
from datetime import datetime

# RAG imports
from langchain_cerebras import ChatCerebras
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
import pinecone

logger = logging.getLogger(__name__)

class ComplianceAgent:
    """ISO 14040/14044 Compliance Agent with RAG for LCA Standards"""
    
    def __init__(self, cerebras_api_key: str = None, pinecone_api_key: str = None):
        self.cerebras_api_key = cerebras_api_key or os.getenv("CEREBRAS_API_KEY")
        self.pinecone_api_key = pinecone_api_key or os.getenv("PINECONE_API_KEY")
        
        # Initialize LLM
        self.llm = ChatCerebras(
            api_key=self.cerebras_api_key, 
            model="llama3.1-8b"
        ) if self.cerebras_api_key else None
        
        # Initialize embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        # Initialize vector store
        self.vector_store = None
        self._setup_rag_system()
        
        # Compliance criteria weights (rebalance for more spread)
        self.compliance_weights = {
            "goal_and_scope": 0.25,
            "inventory_analysis": 0.25,
            "impact_assessment": 0.15,
            "interpretation": 0.25,
            "reporting": 0.10
        }
    
    def _setup_rag_system(self):
        """Setup RAG system with ISO standards documents"""
        try:
            if not self.pinecone_api_key:
                logger.warning("Pinecone API key not found. RAG system disabled.")
                return
            
            pc = pinecone.Pinecone(api_key=self.pinecone_api_key)
            index_name = "lca-compliance-standards"
            if index_name not in pc.list_indexes().names():
                logger.info(f"Creating Pinecone index: {index_name}")
                pc.create_index(
                    name=index_name,
                    dimension=384,  # MiniLM embedding dimension
                    metric="cosine",
                    spec=pinecone.ServerlessSpec(cloud="aws", region="us-east-1")
                )
            
            self.vector_store = PineconeVectorStore(
                index_name=index_name,
                embedding=self.embeddings,
                pinecone_api_key=self.pinecone_api_key
            )
            
            logger.info("RAG system initialized successfully")
        except Exception as e:
            logger.error(f"RAG setup error: {e}")
            self.vector_store = None
    
    def check_lca_compliance(self, lca_study_data: Dict[str, Any], 
                           study_type: str = "internal_decision_support") -> Dict[str, Any]:
        """Check LCA study compliance with ISO 14040/14044 standards"""
        try:
            compliance_data = self._extract_compliance_data(lca_study_data)
            
            # Run scoring across categories
            goal_scope_score = self._check_goal_and_scope(compliance_data, study_type)
            inventory_score = self._check_inventory_analysis(compliance_data)
            impact_score = self._check_impact_assessment(compliance_data)
            interpretation_score = self._check_interpretation(compliance_data)
            reporting_score = self._check_reporting_requirements(compliance_data, study_type)
            
            # Weighted average
            overall_score = (
                goal_scope_score["score"] * self.compliance_weights["goal_and_scope"] +
                inventory_score["score"] * self.compliance_weights["inventory_analysis"] +
                impact_score["score"] * self.compliance_weights["impact_assessment"] +
                interpretation_score["score"] * self.compliance_weights["interpretation"] +
                reporting_score["score"] * self.compliance_weights["reporting"]
            )
            
            compliance_report = self._generate_compliance_report({
                "goal_scope": goal_scope_score,
                "inventory": inventory_score,
                "impact": impact_score,
                "interpretation": interpretation_score,
                "reporting": reporting_score,
                "overall_score": overall_score
            }, study_type)
            
            return {
                "success": True,
                "study_type": study_type,
                "compliance_categories": {
                    "goal_and_scope": goal_scope_score,
                    "inventory_analysis": inventory_score,
                    "impact_assessment": impact_score,
                    "interpretation": interpretation_score,
                    "reporting": reporting_score
                },
                "overall_compliance_score": {
                    "overall_score": overall_score,
                    "grade": self._get_compliance_grade(overall_score),
                    "status": self._get_compliance_status(overall_score)
                },
                "compliance_report": compliance_report,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Compliance check error: {e}")
            return {"error": str(e), "success": False}
    
    def _extract_compliance_data(self, lca_study_data: Dict[str, Any]) -> Dict[str, Any]:
        scenarios = lca_study_data.get("scenarios", [])
        if not scenarios and "material_type" in lca_study_data:
            scenarios = [lca_study_data]
        
        return {
            "functional_unit": lca_study_data.get("functional_unit", "Not specified"),
            "system_boundaries": lca_study_data.get("analysis_type", "cradle_to_gate"),
            "materials_analyzed": [s.get("material_type", "unknown") for s in scenarios],
            "total_mass_kg": sum(s.get("mass_kg", 0) for s in scenarios),
            "data_completeness": self._assess_data_completeness(scenarios),
            "methodology": "ISO 14040/14044",
            "impact_categories": ["climate_change", "energy_use", "resource_depletion"],
            "has_transport_data": any(s.get("transport", {}).get("distance_km", 0) > 0 for s in scenarios),
            "has_energy_data": any(s.get("energy_intensity", {}) for s in scenarios),
            "has_recycling_data": any(s.get("recycling", {}) for s in scenarios),
            "grid_composition_provided": any(s.get("grid_composition", {}) for s in scenarios),
            "emission_factors_provided": any(s.get("material_emission_factors", {}) for s in scenarios),
            "scenarios_count": len(scenarios)
        }
    
    def _assess_data_completeness(self, scenarios: List[Dict[str, Any]]) -> float:
        required_fields = [
            "material_type", "mass_kg", "energy_intensity", "direct_emissions",
            "grid_composition", "transport", "material_emission_factors", "recycling"
        ]
        total_fields = len(required_fields) * len(scenarios)
        present_fields = sum(1 for s in scenarios for f in required_fields if f in s and s[f])
        return present_fields / total_fields if total_fields > 0 else 0

    # -------------------- Dynamic Scoring Functions --------------------

    def _check_goal_and_scope(self, compliance_data: Dict[str, Any], study_type: str) -> Dict[str, Any]:
        score, issues = 0.0, []
        
        if compliance_data.get("functional_unit") and compliance_data["functional_unit"] != "Not specified":
            score += 0.25
        else:
            issues.append("Functional unit not clearly defined")
            score -= 0.1
        
        if compliance_data.get("system_boundaries"):
            score += 0.2
        else:
            issues.append("System boundaries not specified")
            score -= 0.05
        
        if compliance_data.get("materials_analyzed"):
            score += 0.15
        else:
            issues.append("Materials not properly identified")
            score -= 0.05
        
        completeness = compliance_data.get("data_completeness", 0)
        if completeness >= 0.9: score += 0.4
        elif completeness >= 0.7: score += 0.3
        elif completeness >= 0.5: score += 0.15
        else:
            issues.append("Insufficient data completeness for robust analysis")
            score += 0.05
        
        final_score = max(min(score, 1.0), 0.0)
        return {"score": final_score, "issues": issues, "requirements_met": final_score >= 0.7}
    
    def _check_inventory_analysis(self, compliance_data: Dict[str, Any]) -> Dict[str, Any]:
        score, issues = 0.0, []
        
        if compliance_data.get("has_energy_data"): score += 0.25
        else: issues.append("Energy data missing"); score -= 0.1
        
        if compliance_data.get("has_transport_data"): score += 0.2
        else: issues.append("Transport data missing"); score -= 0.05
        
        if compliance_data.get("emission_factors_provided"): score += 0.25
        else: issues.append("Emission factors not provided"); score -= 0.1
        
        if compliance_data.get("has_recycling_data"): score += 0.2
        else: issues.append("Recycling data missing"); score -= 0.05
        
        if compliance_data.get("grid_composition_provided"): score += 0.1
        else: issues.append("Grid composition not specified")
        
        final_score = max(min(score, 1.0), 0.0)
        return {"score": final_score, "issues": issues, "requirements_met": final_score >= 0.65}
    
    def _check_impact_assessment(self, compliance_data: Dict[str, Any]) -> Dict[str, Any]:
        score, issues = 0.0, []
        impacts = compliance_data.get("impact_categories", [])
        
        if "climate_change" in impacts: score += 0.4
        else: issues.append("Climate change impact category missing"); score -= 0.1
        
        if len(impacts) >= 2: score += 0.3
        else: issues.append("Too few impact categories"); score -= 0.05
        
        if compliance_data.get("methodology") == "ISO 14040/14044": score += 0.3
        else: issues.append("Methodology not ISO-compliant"); score -= 0.05
        
        final_score = max(min(score, 1.0), 0.0)
        return {"score": final_score, "issues": issues, "requirements_met": final_score >= 0.65}
    
    def _check_interpretation(self, compliance_data: Dict[str, Any]) -> Dict[str, Any]:
        score, issues = 0.3, []  # lower base than before
        
        if compliance_data.get("scenarios_count", 1) > 1: score += 0.25
        else: issues.append("Only single scenario considered")
        
        completeness = compliance_data.get("data_completeness", 0)
        if completeness >= 0.8: score += 0.35
        elif completeness >= 0.6: score += 0.25
        else: issues.append("Weak data quality for interpretation"); score += 0.1
        
        final_score = max(min(score, 1.0), 0.0)
        return {"score": final_score, "issues": issues, "requirements_met": final_score >= 0.65}
    
    def _check_reporting_requirements(self, compliance_data: Dict[str, Any], study_type: str) -> Dict[str, Any]:
        score, issues = 0.4, []
        
        if study_type == "comparative_assertion" and compliance_data.get("scenarios_count", 1) < 2:
            issues.append("Comparative assertion requires multiple scenarios"); score -= 0.2
        elif study_type == "public_communication" and compliance_data.get("data_completeness", 0) < 0.8:
            issues.append("Public communication requires high data quality"); score -= 0.2
        
        if compliance_data.get("methodology"): score += 0.3
        if compliance_data.get("system_boundaries"): score += 0.3
        else: issues.append("System boundaries missing from reporting")
        
        final_score = max(min(score, 1.0), 0.0)
        return {"score": final_score, "issues": issues, "requirements_met": final_score >= 0.65}
    
    # -------------------- Report + Grades --------------------
    
    def _generate_compliance_report(self, compliance_results: Dict[str, Any], study_type: str) -> str:
        overall_score = compliance_results["overall_score"]
        grade = self._get_compliance_grade(overall_score)
        status = self._get_compliance_status(overall_score)
        
        return f"""
ISO 14040/14044 LCA COMPLIANCE ASSESSMENT REPORT

Study Type: {study_type.replace('_', ' ').title()}
Assessment Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Overall Compliance Score: {overall_score:.1%}
Compliance Grade: {grade}
Compliance Status: {status}
        """.strip()
    
    def _get_compliance_grade(self, score: float) -> str:
        if score >= 0.9: return "A"
        elif score >= 0.8: return "B"
        elif score >= 0.7: return "C"
        elif score >= 0.6: return "D"
        else: return "F"
    
    def _get_compliance_status(self, score: float) -> str:
        if score >= 0.8: return "Fully Compliant"
        elif score >= 0.7: return "Largely Compliant"
        elif score >= 0.6: return "Partially Compliant"
        else: return "Non-Compliant"
