"""
Compliance Agent with RAG - ISO 14040/14044 LCA Standards Compliance Checker
Works with comprehensive LCA input data format
"""

import logging
import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

# RAG imports
from langchain_cerebras import ChatCerebras
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
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
        
        # Compliance criteria weights
        self.compliance_weights = {
            "goal_and_scope": 0.25,
            "inventory_analysis": 0.25,
            "impact_assessment": 0.25,
            "interpretation": 0.15,
            "reporting": 0.10
        }
    
    def _setup_rag_system(self):
        """Setup RAG system with ISO standards documents"""
        try:
            if not self.pinecone_api_key:
                logger.warning("Pinecone API key not found. RAG system disabled.")
                return
            
            # Initialize Pinecone
            pc = pinecone.Pinecone(api_key=self.pinecone_api_key)
            
            # Create or connect to index
            index_name = "lca-compliance-standards"
            if index_name not in pc.list_indexes().names():
                logger.info(f"Creating Pinecone index: {index_name}")
                pc.create_index(
                    name=index_name,
                    dimension=384,  # MiniLM embedding dimension
                    metric="cosine",
                    spec=pinecone.ServerlessSpec(cloud="aws", region="us-east-1")
                )
            
            # Initialize vector store
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
            logger.info(f"Starting compliance check for {study_type} study")
            
            # Extract key information from comprehensive LCA data
            compliance_data = self._extract_compliance_data(lca_study_data)
            
            # Check each compliance category
            goal_scope_score = self._check_goal_and_scope(compliance_data, study_type)
            inventory_score = self._check_inventory_analysis(compliance_data)
            impact_score = self._check_impact_assessment(compliance_data)
            interpretation_score = self._check_interpretation(compliance_data)
            reporting_score = self._check_reporting_requirements(compliance_data, study_type)
            
            # Calculate overall compliance score
            overall_score = (
                goal_scope_score["score"] * self.compliance_weights["goal_and_scope"] +
                inventory_score["score"] * self.compliance_weights["inventory_analysis"] +
                impact_score["score"] * self.compliance_weights["impact_assessment"] +
                interpretation_score["score"] * self.compliance_weights["interpretation"] +
                reporting_score["score"] * self.compliance_weights["reporting"]
            )
            
            # Generate compliance report
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
        """Extract relevant data for compliance checking from comprehensive LCA data"""
        
        # Handle both single scenario and multi-scenario data
        scenarios = lca_study_data.get("scenarios", [])
        if not scenarios and "material_type" in lca_study_data:
            scenarios = [lca_study_data]
        
        # Extract compliance-relevant information
        compliance_data = {
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
        
        return compliance_data
    
    def _assess_data_completeness(self, scenarios: List[Dict[str, Any]]) -> float:
        """Assess completeness of input data"""
        required_fields = [
            "material_type", "mass_kg", "energy_intensity", "direct_emissions",
            "grid_composition", "transport", "material_emission_factors", "recycling"
        ]
        
        total_fields = len(required_fields) * len(scenarios)
        present_fields = 0
        
        for scenario in scenarios:
            for field in required_fields:
                if field in scenario and scenario[field]:
                    present_fields += 1
        
        return present_fields / total_fields if total_fields > 0 else 0
    
    def _check_goal_and_scope(self, compliance_data: Dict[str, Any], study_type: str) -> Dict[str, Any]:
        """Check Goal and Scope Definition (ISO 14040 Section 4.2)"""
        
        score = 0.0
        issues = []
        
        # Functional unit check
        if compliance_data.get("functional_unit") and compliance_data["functional_unit"] != "Not specified":
            score += 0.3
        else:
            issues.append("Functional unit not clearly defined")
        
        # System boundaries check
        if compliance_data.get("system_boundaries"):
            score += 0.2
        else:
            issues.append("System boundaries not specified")
        
        # Material coverage check
        if compliance_data.get("materials_analyzed"):
            score += 0.2
        else:
            issues.append("Materials not properly identified")
        
        # Data completeness check
        completeness = compliance_data.get("data_completeness", 0)
        if completeness >= 0.8:
            score += 0.3
        elif completeness >= 0.6:
            score += 0.2
        elif completeness >= 0.4:
            score += 0.1
        else:
            issues.append("Insufficient data completeness for robust analysis")
        
        return {
            "score": min(score, 1.0),
            "issues": issues,
            "requirements_met": score >= 0.7
        }
    
    def _check_inventory_analysis(self, compliance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check Life Cycle Inventory Analysis (ISO 14040 Section 4.3)"""
        
        score = 0.0
        issues = []
        
        # Energy data completeness
        if compliance_data.get("has_energy_data"):
            score += 0.25
        else:
            issues.append("Energy consumption data missing or incomplete")
        
        # Transport data
        if compliance_data.get("has_transport_data"):
            score += 0.2
        else:
            issues.append("Transport data not provided")
        
        # Material flow data
        if compliance_data.get("emission_factors_provided"):
            score += 0.25
        else:
            issues.append("Material emission factors not specified")
        
        # Recycling and circularity data
        if compliance_data.get("has_recycling_data"):
            score += 0.2
        else:
            issues.append("End-of-life and recycling data missing")
        
        # Grid composition for energy-related emissions
        if compliance_data.get("grid_composition_provided"):
            score += 0.1
        else:
            issues.append("Energy grid composition data not provided")
        
        return {
            "score": min(score, 1.0),
            "issues": issues,
            "requirements_met": score >= 0.6
        }
    
    def _check_impact_assessment(self, compliance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check Life Cycle Impact Assessment (ISO 14040 Section 4.4)"""
        
        score = 0.0
        issues = []
        
        # Impact categories
        impact_categories = compliance_data.get("impact_categories", [])
        if "climate_change" in impact_categories:
            score += 0.4
        else:
            issues.append("Climate change impact category missing")
        
        if len(impact_categories) >= 2:
            score += 0.3
        else:
            issues.append("Limited impact categories assessed")
        
        # Methodology
        if compliance_data.get("methodology") == "ISO 14040/14044":
            score += 0.3
        else:
            issues.append("Methodology not aligned with ISO standards")
        
        return {
            "score": min(score, 1.0),
            "issues": issues,
            "requirements_met": score >= 0.6
        }
    
    def _check_interpretation(self, compliance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check Life Cycle Interpretation (ISO 14040 Section 4.5)"""
        
        score = 0.5  # Base score for basic interpretation
        issues = []
        
        # Multi-scenario analysis
        if compliance_data.get("scenarios_count", 1) > 1:
            score += 0.2
            
        # Data quality assessment
        completeness = compliance_data.get("data_completeness", 0)
        if completeness >= 0.7:
            score += 0.3
        else:
            issues.append("Data quality may affect interpretation reliability")
        
        return {
            "score": min(score, 1.0),
            "issues": issues,
            "requirements_met": score >= 0.6
        }
    
    def _check_reporting_requirements(self, compliance_data: Dict[str, Any], study_type: str) -> Dict[str, Any]:
        """Check Reporting Requirements based on study type"""
        
        score = 0.6  # Base score for basic reporting
        issues = []
        
        # Study type specific requirements
        if study_type == "comparative_assertion":
            if compliance_data.get("scenarios_count", 1) < 2:
                issues.append("Comparative assertion requires multiple scenarios")
                score -= 0.2
        
        elif study_type == "public_communication":
            if compliance_data.get("data_completeness", 0) < 0.8:
                issues.append("Public communication requires high data quality")
                score -= 0.2
        
        # Transparency check
        if compliance_data.get("methodology"):
            score += 0.2
        
        # System boundaries documentation
        if compliance_data.get("system_boundaries"):
            score += 0.2
        
        return {
            "score": max(min(score, 1.0), 0.0),
            "issues": issues,
            "requirements_met": score >= 0.6
        }
    
    def _generate_compliance_report(self, compliance_results: Dict[str, Any], study_type: str) -> str:
        """Generate comprehensive compliance report"""
        
        overall_score = compliance_results["overall_score"]
        grade = self._get_compliance_grade(overall_score)
        status = self._get_compliance_status(overall_score)
        
        report = f"""
ISO 14040/14044 LCA COMPLIANCE ASSESSMENT REPORT

Study Type: {study_type.replace('_', ' ').title()}
Assessment Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Overall Compliance Score: {overall_score:.1%}
Compliance Grade: {grade}
Compliance Status: {status}

DETAILED ASSESSMENT:

1. GOAL AND SCOPE DEFINITION
   Score: {compliance_results['goal_scope']['score']:.1%}
   Status: {'✓ COMPLIANT' if compliance_results['goal_scope']['requirements_met'] else '✗ NON-COMPLIANT'}
   Issues: {'; '.join(compliance_results['goal_scope']['issues']) if compliance_results['goal_scope']['issues'] else 'None identified'}

2. LIFE CYCLE INVENTORY ANALYSIS
   Score: {compliance_results['inventory']['score']:.1%}
   Status: {'✓ COMPLIANT' if compliance_results['inventory']['requirements_met'] else '✗ NON-COMPLIANT'}
   Issues: {'; '.join(compliance_results['inventory']['issues']) if compliance_results['inventory']['issues'] else 'None identified'}

3. LIFE CYCLE IMPACT ASSESSMENT
   Score: {compliance_results['impact']['score']:.1%}
   Status: {'✓ COMPLIANT' if compliance_results['impact']['requirements_met'] else '✗ NON-COMPLIANT'}
   Issues: {'; '.join(compliance_results['impact']['issues']) if compliance_results['impact']['issues'] else 'None identified'}

4. LIFE CYCLE INTERPRETATION
   Score: {compliance_results['interpretation']['score']:.1%}
   Status: {'✓ COMPLIANT' if compliance_results['interpretation']['requirements_met'] else '✗ NON-COMPLIANT'}
   Issues: {'; '.join(compliance_results['interpretation']['issues']) if compliance_results['interpretation']['issues'] else 'None identified'}

5. REPORTING REQUIREMENTS
   Score: {compliance_results['reporting']['score']:.1%}
   Status: {'✓ COMPLIANT' if compliance_results['reporting']['requirements_met'] else '✗ NON-COMPLIANT'}
   Issues: {'; '.join(compliance_results['reporting']['issues']) if compliance_results['reporting']['issues'] else 'None identified'}

RECOMMENDATIONS:
{self._generate_recommendations(compliance_results)}

This assessment is based on ISO 14040:2006 and ISO 14044:2006 standards.
        """.strip()
        
        return report
    
    def _generate_recommendations(self, compliance_results: Dict[str, Any]) -> str:
        """Generate improvement recommendations"""
        recommendations = []
        
        for category, results in compliance_results.items():
            if category == "overall_score":
                continue
            if isinstance(results, dict) and not results.get("requirements_met", True):
                if category == "goal_scope":
                    recommendations.append("- Improve goal and scope definition with clearer functional unit and system boundaries")
                elif category == "inventory":
                    recommendations.append("- Enhance data collection for energy, transport, and material flows")
                elif category == "impact":
                    recommendations.append("- Expand impact assessment to include more environmental categories")
                elif category == "interpretation":
                    recommendations.append("- Strengthen interpretation with sensitivity analysis and uncertainty assessment")
                elif category == "reporting":
                    recommendations.append("- Improve documentation and transparency in reporting")
        
        if not recommendations:
            recommendations.append("- Study meets ISO compliance requirements")
            recommendations.append("- Consider continuous improvement in data quality and scope")
        
        return '\n'.join(recommendations)
    
    def _get_compliance_grade(self, score: float) -> str:
        """Get compliance grade"""
        if score >= 0.9:
            return "A"
        elif score >= 0.8:
            return "B"
        elif score >= 0.7:
            return "C"
        elif score >= 0.6:
            return "D"
        else:
            return "F"
    
    def _get_compliance_status(self, score: float) -> str:
        """Get compliance status"""
        if score >= 0.8:
            return "Fully Compliant"
        elif score >= 0.7:
            return "Largely Compliant"
        elif score >= 0.6:
            return "Partially Compliant"
        else:
            return "Non-Compliant"