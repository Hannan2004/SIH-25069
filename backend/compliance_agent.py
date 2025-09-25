"""
Compliance Agent - Ensures LCA calculations comply with ISO 14040/14044 standards
Enhanced with Pinecone RAG for ISO document knowledge base and Cerebras AI
"""

from typing import Dict, List, Optional, Any, Union
import pandas as pd
import numpy as np
import logging
import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path
import hashlib

# Add tools to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from langchain_core.tools import tool
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.documents import Document
from langchain_cerebras import ChatCerebras
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Updated imports for your preferred pattern
from pinecone import Pinecone, ServerlessSpec
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore

logger = logging.getLogger(__name__)

# ISO 14040/14044 Compliance Requirements
ISO_COMPLIANCE_REQUIREMENTS = {
    "iso_14040": {
        "principles": [
            "Life cycle perspective",
            "Relative approach and functional unit", 
            "Iterative approach",
            "Transparency",
            "Comprehensiveness",
            "Priority of scientific approach"
        ],
        "phases": [
            "Goal and scope definition",
            "Inventory analysis",
            "Impact assessment", 
            "Interpretation"
        ]
    },
    "iso_14044": {
        "goal_and_scope": [
            "Intended application",
            "Reasons for carrying out the study",
            "Intended audience",
            "Functional unit definition",
            "System boundaries",
            "Data requirements",
            "Assumptions and limitations",
            "Critical review requirements"
        ],
        "lci_requirements": [
            "Data collection procedures",
            "Data quality requirements",
            "Allocation procedures",
            "Treatment of missing data",
            "Uncertainty analysis"
        ],
        "lcia_requirements": [
            "Impact category selection",
            "Classification",
            "Characterization", 
            "Normalization (optional)",
            "Grouping (optional)",
            "Weighting (optional)"
        ],
        "interpretation_requirements": [
            "Identification of significant issues",
            "Evaluation of completeness",
            "Evaluation of consistency", 
            "Evaluation of sensitivity",
            "Conclusions and recommendations"
        ]
    }
}

# LCA Study Categories per ISO standards
LCA_STUDY_TYPES = {
    "comparative_assertion": {
        "critical_review_required": True,
        "public_disclosure": True,
        "additional_requirements": [
            "Same functional unit",
            "Equivalent system boundaries",
            "Same impact categories",
            "Same data quality requirements"
        ]
    },
    "internal_decision_support": {
        "critical_review_required": False,
        "public_disclosure": False,
        "additional_requirements": []
    },
    "public_communication": {
        "critical_review_required": True,
        "public_disclosure": True,
        "additional_requirements": [
            "Transparent reporting",
            "External verification"
        ]
    }
}

class ComplianceAgent:
    """Enhanced Compliance Agent with Pinecone RAG and Cerebras AI"""
    
    def __init__(self, cerebras_api_key: str = None, pinecone_api_key: str = None, 
                 pinecone_environment: str = None, index_name: str = "iso-lca-standards"):
        # Initialize ChatCerebras
        self.cerebras_api_key = cerebras_api_key or os.getenv("CEREBRAS_API_KEY")
        self.llm = ChatCerebras(
            api_key=self.cerebras_api_key,
            model="qwen-3-32b",
        ) if self.cerebras_api_key else None
        
        # Initialize Pinecone
        self.pinecone_api_key = pinecone_api_key or os.getenv("PINECONE_API_KEY")
        self.pinecone_environment = pinecone_environment or os.getenv("PINECONE_ENVIRONMENT")
        self.index_name = index_name
        
        # Initialize embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        # Load compliance requirements
        self.iso_requirements = ISO_COMPLIANCE_REQUIREMENTS
        self.study_types = LCA_STUDY_TYPES
        
        # Initialize document processing
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        
        # Setup vector store
        self.vector_store = self._setup_vector_store()
    
    def _setup_vector_store(self) -> PineconeVectorStore:
        """Set up Pinecone vector store for ISO 14040/14044 standards"""
        
        if not self.pinecone_api_key or not self.embeddings:
            logging.warning("Pinecone API key or embeddings not available, skipping vector store setup")
            return None
        
        try:
            pc = Pinecone(api_key=self.pinecone_api_key)
            
            existing_indexes = pc.list_indexes().names()

            if self.index_name not in existing_indexes:
                pc.create_index(
                    name=self.index_name,
                    dimension=384,  # all-MiniLM-L6-v2 dimension
                    metric='cosine',
                    spec=ServerlessSpec(
                        cloud='aws',
                        region='us-east-1'
                    )
                )
                time.sleep(10)

            index = pc.Index(self.index_name)
            stats = index.describe_index_stats()
            
            if stats.total_vector_count > 0:
                return PineconeVectorStore(
                    index=index,
                    embedding=self.embeddings
                )

            # Try to load actual ISO PDF documents first
            documents = self._load_iso_documents()
            
            # If no PDFs found, create synthetic ISO knowledge base
            if not documents:
                iso_knowledge = [
                    "ISO 14040 establishes principles and framework for life cycle assessment including goal and scope definition",
                    "ISO 14044 specifies requirements for LCA studies including inventory analysis and impact assessment",
                    "Functional unit must be clearly defined and quantified as the reference unit for LCA study",
                    "System boundaries define which processes are included in the LCA study scope",
                    "Life cycle inventory analysis involves data collection and calculation procedures for inputs and outputs",
                    "Life cycle impact assessment includes classification, characterization, and optional normalization steps",
                    "Critical review is mandatory for comparative assertions disclosed to the public",
                    "Data quality requirements include temporal, geographical, and technological representativeness",
                    "Allocation procedures must be documented when processes deliver multiple products",
                    "Interpretation phase includes identification of significant issues and sensitivity analysis",
                    "Transparency principle requires clear documentation of methodology and assumptions",
                    "Iterative approach allows refinement of goal, scope and methodology throughout the study",
                    "Impact category selection should be justified and relevant to the study goal",
                    "Classification assigns inventory data to impact categories",
                    "Characterization calculates category indicator results using characterization factors",
                    "Uncertainty analysis should assess reliability of LCA results",
                    "Sensitivity analysis evaluates influence of assumptions and methodological choices",
                    "Documentation must be sufficient to enable critical review and reproducibility"
                ]
                
                documents = []
                for i, knowledge in enumerate(iso_knowledge):
                    doc = Document(
                        page_content=knowledge,
                        metadata={"source": "ISO_Standards_Knowledge", "chunk": i, "document_type": "iso_standard"}
                    )
                    documents.append(doc)

            # Create vector store from documents
            vector_store = PineconeVectorStore.from_documents(
                documents=documents,
                embedding=self.embeddings,
                index_name=self.index_name
            )

            return vector_store
        
        except Exception as e:
            logger.error(f"Error setting up vector store: {e}")
            return None

    def _load_iso_documents(self) -> List[Document]:
        """Load ISO documents from PDFs if available"""
        documents = []
        
        try:
            current_dir = Path(__file__).parent
            iso_files = [
                "ISO-14040-2006.pdf",
                "ISO-14044-2006.pdf"
            ]
            
            for file_name in iso_files:
                file_path = current_dir / file_name
                if file_path.exists():
                    try:
                        # Load PDF
                        loader = PyPDFLoader(str(file_path))
                        pdf_documents = loader.load()
                        
                        # Split into chunks
                        chunks = self.text_splitter.split_documents(pdf_documents)
                        
                        # Add metadata
                        for chunk in chunks:
                            chunk.metadata.update({
                                "source": file_name,
                                "document_type": "iso_standard"
                            })
                        
                        documents.extend(chunks)
                        logger.info(f"Loaded {len(chunks)} chunks from {file_name}")
                        
                    except Exception as e:
                        logger.error(f"Failed to load {file_name}: {e}")
                else:
                    logger.warning(f"ISO document not found: {file_path}")
            
            return documents
            
        except Exception as e:
            logger.error(f"Error loading ISO documents: {e}")
            return []
    
    def _query_iso_knowledge_base(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Query the ISO standards knowledge base"""
        
        if not self.vector_store:
            logger.warning("Vector store not available for querying")
            return []
        
        try:
            # Search vector store
            results = self.vector_store.similarity_search_with_score(
                query=query,
                k=top_k,
                filter={"document_type": "iso_standard"}
            )
            
            # Format results
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    "content": doc.page_content,
                    "source": doc.metadata.get('source', ''),
                    "page": doc.metadata.get('page', 0),
                    "score": score
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error querying ISO knowledge base: {e}")
            return []
    
    def check_lca_compliance(self, lca_study_data: Dict[str, Any], 
                           study_type: str = "internal_decision_support") -> Dict[str, Any]:
        """
        Comprehensive LCA compliance check against ISO 14040/14044
        
        Args:
            lca_study_data: Complete LCA study data
            study_type: Type of LCA study (comparative_assertion, internal_decision_support, etc.)
            
        Returns:
            Dict: Comprehensive compliance assessment
        """
        
        try:
            # Validate study type
            if study_type not in self.study_types:
                return {
                    "error": f"Invalid study type. Must be one of: {list(self.study_types.keys())}",
                    "success": False
                }
            
            # Perform basic compliance checks
            basic_compliance = self._check_basic_compliance(lca_study_data, study_type)
            
            # Perform detailed phase-specific checks
            phase_compliance = self._check_phase_compliance(lca_study_data)
            
            # Check data quality requirements
            data_quality_compliance = self._check_data_quality_compliance(lca_study_data)
            
            # Generate AI-enhanced compliance insights
            ai_compliance_insights = self._generate_ai_compliance_insights(
                lca_study_data, basic_compliance, phase_compliance, data_quality_compliance
            ) if self.llm else {}
            
            # Calculate overall compliance score
            overall_score = self._calculate_compliance_score(
                basic_compliance, phase_compliance, data_quality_compliance
            )
            
            return {
                "success": True,
                "study_type": study_type,
                "overall_compliance_score": overall_score,
                "basic_compliance": basic_compliance,
                "phase_compliance": phase_compliance,
                "data_quality_compliance": data_quality_compliance,
                "ai_insights": ai_compliance_insights,
                "compliance_report": self._generate_compliance_report(
                    overall_score, basic_compliance, phase_compliance, data_quality_compliance
                ),
                "assessment_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in compliance check: {e}")
            return {"error": str(e), "success": False}
    
    def _check_basic_compliance(self, data: Dict[str, Any], study_type: str) -> Dict[str, Any]:
        """Check basic ISO compliance requirements"""
        
        compliance_issues = []
        compliance_score = 0
        total_checks = 0
        
        study_requirements = self.study_types[study_type]
        
        # Check ISO 14040 principles
        iso_14040_checks = {
            "functional_unit_defined": "functional_unit" in data,
            "system_boundaries_defined": "system_boundaries" in data,
            "goal_and_scope_defined": "goal" in data and "scope" in data,
            "impact_categories_defined": "impact_categories" in data or "lca_results" in data
        }
        
        for check_name, passed in iso_14040_checks.items():
            total_checks += 1
            if passed:
                compliance_score += 1
            else:
                compliance_issues.append(f"Missing: {check_name.replace('_', ' ').title()}")
        
        # Check study type specific requirements  
        if study_requirements["critical_review_required"]:
            total_checks += 1
            if data.get("critical_review_completed", False):
                compliance_score += 1
            else:
                compliance_issues.append("Critical review required but not completed")
        
        # Check transparency requirements
        transparency_checks = {
            "methodology_documented": "methodology" in data or "calculation_method" in data,
            "assumptions_documented": "assumptions" in data,
            "limitations_documented": "limitations" in data,
            "data_sources_documented": "data_sources" in data or "data_provenance" in data
        }
        
        for check_name, passed in transparency_checks.items():
            total_checks += 1
            if passed:
                compliance_score += 1
            else:
                compliance_issues.append(f"Missing: {check_name.replace('_', ' ').title()}")
        
        return {
            "compliance_score": compliance_score / total_checks if total_checks > 0 else 0,
            "total_checks": total_checks,
            "passed_checks": compliance_score,
            "compliance_issues": compliance_issues,
            "compliant": len(compliance_issues) == 0
        }
    
    def _check_phase_compliance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Check compliance for each LCA phase per ISO 14044"""
        
        phase_results = {}
        
        # Phase 1: Goal and Scope Definition
        phase_results["goal_and_scope"] = self._check_goal_and_scope_compliance(data)
        
        # Phase 2: Life Cycle Inventory (LCI)
        phase_results["inventory_analysis"] = self._check_lci_compliance(data)
        
        # Phase 3: Life Cycle Impact Assessment (LCIA)
        phase_results["impact_assessment"] = self._check_lcia_compliance(data)
        
        # Phase 4: Life Cycle Interpretation
        phase_results["interpretation"] = self._check_interpretation_compliance(data)
        
        return phase_results
    
    def _check_goal_and_scope_compliance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Check Goal and Scope definition compliance"""
        
        required_elements = self.iso_requirements["iso_14044"]["goal_and_scope"]
        compliance_issues = []
        compliance_score = 0
        
        # Map data fields to ISO requirements
        field_mapping = {
            "intended_application": ["intended_application", "application", "purpose"],
            "reasons_for_study": ["reasons", "justification", "rationale"],
            "intended_audience": ["audience", "stakeholders", "target_audience"],
            "functional_unit": ["functional_unit", "reference_unit"],
            "system_boundaries": ["system_boundaries", "boundaries", "scope_boundaries"],
            "data_requirements": ["data_requirements", "data_quality_requirements"],
            "assumptions_and_limitations": ["assumptions", "limitations"],
            "critical_review_requirements": ["critical_review", "review_requirements"]
        }
        
        for requirement in required_elements:
            field_key = requirement.lower().replace(" ", "_")
            mapped_fields = field_mapping.get(field_key, [field_key])
            
            found = any(field in data for field in mapped_fields)
            
            if found:
                compliance_score += 1
            else:
                compliance_issues.append(f"Missing: {requirement}")
        
        return {
            "compliance_score": compliance_score / len(required_elements),
            "total_requirements": len(required_elements),
            "met_requirements": compliance_score,
            "compliance_issues": compliance_issues,
            "compliant": len(compliance_issues) == 0
        }
    
    def _check_lci_compliance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Check Life Cycle Inventory compliance"""
        
        required_elements = self.iso_requirements["iso_14044"]["lci_requirements"]
        compliance_issues = []
        compliance_score = 0
        
        # Check for LCI data and procedures
        lci_checks = {
            "data_collection_procedures": any(field in data for field in 
                                           ["data_collection", "data_procedures", "methodology"]),
            "data_quality_requirements": any(field in data for field in 
                                           ["data_quality", "data_assessment", "quality_indicators"]),
            "allocation_procedures": any(field in data for field in 
                                       ["allocation", "allocation_method", "partitioning"]),
            "treatment_of_missing_data": any(field in data for field in 
                                           ["missing_data_treatment", "data_gaps", "imputation"]),
            "uncertainty_analysis": any(field in data for field in 
                                      ["uncertainty", "sensitivity", "monte_carlo"])
        }
        
        for requirement in required_elements:
            check_key = requirement.lower().replace(" ", "_")
            
            if lci_checks.get(check_key, False):
                compliance_score += 1
            else:
                compliance_issues.append(f"Missing: {requirement}")
        
        return {
            "compliance_score": compliance_score / len(required_elements),
            "total_requirements": len(required_elements),
            "met_requirements": compliance_score,
            "compliance_issues": compliance_issues,
            "compliant": len(compliance_issues) == 0
        }
    
    def _check_lcia_compliance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Check Life Cycle Impact Assessment compliance"""
        
        required_elements = self.iso_requirements["iso_14044"]["lcia_requirements"]
        compliance_issues = []
        compliance_score = 0
        
        # Check for LCIA elements
        lcia_checks = {
            "impact_category_selection": any(field in data for field in 
                                           ["impact_categories", "environmental_impacts", "lca_results"]),
            "classification": any(field in data for field in 
                                ["classification", "impact_classification", "emission_mapping"]),
            "characterization": any(field in data for field in 
                                  ["characterization", "impact_factors", "gwp_values"]),
            "normalization": any(field in data for field in 
                               ["normalization", "normalized_results"]),
            "grouping": any(field in data for field in 
                          ["grouping", "impact_grouping"]),
            "weighting": any(field in data for field in 
                           ["weighting", "weighted_results"])
        }
        
        # Mandatory elements (first 3 are required, others optional)
        mandatory_elements = required_elements[:3]
        optional_elements = required_elements[3:]
        
        for requirement in mandatory_elements:
            check_key = requirement.lower().replace(" ", "_")
            
            if lcia_checks.get(check_key, False):
                compliance_score += 1
            else:
                compliance_issues.append(f"Missing mandatory: {requirement}")
        
        # Optional elements don't count against compliance but are noted
        optional_info = []
        for requirement in optional_elements:
            check_key = requirement.lower().replace(" ", "_").replace("_(optional)", "")
            
            if lcia_checks.get(check_key, False):
                optional_info.append(f"Included optional: {requirement}")
        
        return {
            "compliance_score": compliance_score / len(mandatory_elements),
            "total_requirements": len(mandatory_elements),
            "met_requirements": compliance_score,
            "compliance_issues": compliance_issues,
            "optional_elements_included": optional_info,
            "compliant": len(compliance_issues) == 0
        }
    
    def _check_interpretation_compliance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Check Life Cycle Interpretation compliance"""
        
        required_elements = self.iso_requirements["iso_14044"]["interpretation_requirements"]
        compliance_issues = []
        compliance_score = 0
        
        # Check for interpretation elements
        interpretation_checks = {
            "identification_of_significant_issues": any(field in data for field in 
                                                      ["significant_issues", "hotspots", "key_findings"]),
            "evaluation_of_completeness": any(field in data for field in 
                                            ["completeness", "data_completeness", "coverage"]),
            "evaluation_of_consistency": any(field in data for field in 
                                           ["consistency", "data_consistency", "validation"]),
            "evaluation_of_sensitivity": any(field in data for field in 
                                           ["sensitivity", "sensitivity_analysis", "scenarios"]),
            "conclusions_and_recommendations": any(field in data for field in 
                                                 ["conclusions", "recommendations", "findings"])
        }
        
        for requirement in required_elements:
            check_key = requirement.lower().replace(" ", "_")
            
            if interpretation_checks.get(check_key, False):
                compliance_score += 1
            else:
                compliance_issues.append(f"Missing: {requirement}")
        
        return {
            "compliance_score": compliance_score / len(required_elements),
            "total_requirements": len(required_elements),
            "met_requirements": compliance_score,
            "compliance_issues": compliance_issues,
            "compliant": len(compliance_issues) == 0
        }
    
    def _check_data_quality_compliance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Check data quality requirements compliance"""
        
        quality_issues = []
        quality_score = 0
        total_checks = 8
        
        # Data quality indicators per ISO 14044
        quality_checks = {
            "temporal_coverage": any(field in data for field in 
                                   ["temporal_coverage", "time_period", "data_year"]),
            "geographical_coverage": any(field in data for field in 
                                       ["geographical_coverage", "region", "location"]),
            "technological_coverage": any(field in data for field in 
                                        ["technology", "process_technology", "production_method"]),
            "precision": any(field in data for field in 
                           ["precision", "measurement_precision", "uncertainty"]),
            "completeness": any(field in data for field in 
                              ["data_completeness", "coverage", "data_gaps"]),
            "representativeness": any(field in data for field in 
                                    ["representativeness", "data_quality", "validation"]),
            "consistency": any(field in data for field in 
                             ["data_consistency", "validation", "verification"]),
            "reproducibility": any(field in data for field in 
                                 ["reproducibility", "methodology", "documentation"])
        }
        
        for check_name, passed in quality_checks.items():
            if passed:
                quality_score += 1
            else:
                quality_issues.append(f"Missing: {check_name.replace('_', ' ').title()}")
        
        return {
            "quality_score": quality_score / total_checks,
            "total_checks": total_checks,
            "passed_checks": quality_score,
            "quality_issues": quality_issues,
            "compliant": quality_score >= total_checks * 0.7  # 70% threshold for data quality
        }
    
    def _generate_ai_compliance_insights(self, lca_data: Dict[str, Any],
                                       basic_compliance: Dict[str, Any],
                                       phase_compliance: Dict[str, Any],
                                       data_quality: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI-enhanced compliance insights using RAG"""
        
        if not self.llm:
            return {"error": "AI insights not available - LLM not configured"}
        
        try:
            # Query ISO knowledge base for relevant compliance information
            compliance_context = self._get_compliance_context(basic_compliance, phase_compliance)
            
            # Prepare summary for AI analysis
            compliance_summary = {
                "overall_compliance_level": "high" if all(
                    c.get("compliant", False) for c in [basic_compliance, data_quality]
                ) else "medium" if any(
                    c.get("compliance_score", 0) > 0.5 for c in [basic_compliance, data_quality]
                ) else "low",
                "major_issues": (basic_compliance.get("compliance_issues", []) + 
                               data_quality.get("quality_issues", []))[:5],
                "phase_scores": {
                    phase: result.get("compliance_score", 0)
                    for phase, result in phase_compliance.items()
                },
                "data_quality_score": data_quality.get("quality_score", 0)
            }
            
            system_prompt = f"""You are an expert LCA compliance auditor specializing in ISO 14040/14044 standards.
            
            Relevant ISO compliance context:
            {compliance_context}
            
            Analyze the LCA study compliance and provide:
            1. Critical compliance gaps and their implications
            2. Specific recommendations for achieving full ISO compliance
            3. Priority actions for improvement
            4. Risk assessment for non-compliance
            5. Best practices for maintaining ongoing compliance
            
            Focus on actionable, standard-specific guidance for compliance improvement."""
            
            user_message = f"Analyze this LCA compliance assessment: {json.dumps(compliance_summary, indent=2)}"
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_message)
            ]
            
            response = self.llm.invoke(messages)
            ai_analysis = response.content
            
            return {
                "ai_compliance_analysis": ai_analysis,
                "compliance_recommendations": self._extract_compliance_recommendations(ai_analysis),
                "risk_assessment": self._assess_compliance_risks(compliance_summary),
                "improvement_roadmap": self._generate_improvement_roadmap(
                    basic_compliance, phase_compliance, data_quality
                )
            }
            
        except Exception as e:
            logger.error(f"Error generating AI compliance insights: {e}")
            return {"error": f"Failed to generate AI insights: {str(e)}"}
    
    def _get_compliance_context(self, basic_compliance: Dict[str, Any], 
                              phase_compliance: Dict[str, Any]) -> str:
        """Get relevant ISO compliance context from RAG knowledge base"""
        
        # Identify key compliance issues
        issues = basic_compliance.get("compliance_issues", [])
        for phase, result in phase_compliance.items():
            issues.extend(result.get("compliance_issues", []))
        
        # Query knowledge base for relevant information
        compliance_queries = [
            "ISO 14040 principles and requirements",
            "ISO 14044 goal and scope definition requirements",
            "ISO 14044 life cycle inventory requirements", 
            "ISO 14044 impact assessment requirements",
            "ISO 14044 interpretation requirements"
        ]
        
        # Add specific queries based on identified issues
        for issue in issues[:3]:  # Top 3 issues
            compliance_queries.append(f"ISO 14044 {issue.lower()}")
        
        context_parts = []
        for query in compliance_queries:
            results = self._query_iso_knowledge_base(query, top_k=2)
            for result in results:
                context_parts.append(f"Source: {result['source']}, Page: {result['page']}\n{result['content']}")
        
        return "\n\n".join(context_parts[:10])  # Limit context length
    
    def _extract_compliance_recommendations(self, ai_analysis: str) -> List[Dict[str, str]]:
        """Extract specific compliance recommendations from AI analysis"""
        
        recommendations = []
        lines = ai_analysis.split('\n')
        
        current_recommendation = None
        for line in lines:
            line = line.strip()
            
            # Look for recommendation indicators
            if any(indicator in line.lower() for indicator in 
                  ['recommend', 'should', 'must', 'ensure', 'implement', 'establish']):
                if current_recommendation:
                    recommendations.append(current_recommendation)
                
                # Determine priority based on keywords
                priority = "high"
                if any(word in line.lower() for word in ['critical', 'mandatory', 'must', 'required']):
                    priority = "high"
                elif any(word in line.lower() for word in ['should', 'recommend', 'important']):
                    priority = "medium"
                elif any(word in line.lower() for word in ['consider', 'optional', 'enhance']):
                    priority = "low"
                
                current_recommendation = {
                    "recommendation": line,
                    "priority": priority,
                    "category": "compliance"
                }
            elif current_recommendation and line:
                # Continue building current recommendation
                current_recommendation["recommendation"] += " " + line
        
        if current_recommendation:
            recommendations.append(current_recommendation)
        
        return recommendations[:8]  # Top 8 recommendations
    
    def _assess_compliance_risks(self, compliance_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risks associated with current compliance level"""
        
        compliance_level = compliance_summary["overall_compliance_level"]
        major_issues = len(compliance_summary["major_issues"])
        
        # Risk assessment matrix
        risk_levels = {
            "high": {
                "description": "Significant compliance gaps with potential for study rejection",
                "implications": ["Study results may not be accepted", "Legal/regulatory issues possible", 
                              "Reputation damage risk", "Decision-making reliability compromised"],
                "mitigation_urgency": "immediate"
            },
            "medium": {
                "description": "Moderate compliance gaps requiring attention",
                "implications": ["Study credibility may be questioned", "Limited stakeholder acceptance",
                              "Need for additional verification", "Potential for misinterpretation"],
                "mitigation_urgency": "within 30 days"
            },
            "low": {
                "description": "Minor compliance gaps with minimal impact",
                "implications": ["Documentation improvements needed", "Enhanced transparency required",
                              "Minor credibility concerns", "Opportunity for best practice adoption"],
                "mitigation_urgency": "within 90 days"
            }
        }
        
        # Determine risk level
        if compliance_level == "low" or major_issues > 5:
            risk_level = "high"
        elif compliance_level == "medium" or major_issues > 2:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        risk_assessment = risk_levels[risk_level].copy()
        risk_assessment["risk_level"] = risk_level
        risk_assessment["major_issues_count"] = major_issues
        
        return risk_assessment
    
    def _generate_improvement_roadmap(self, basic_compliance: Dict[str, Any],
                                    phase_compliance: Dict[str, Any],
                                    data_quality: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate a prioritized improvement roadmap"""
        
        roadmap = []
        
        # Priority 1: Address critical basic compliance issues
        if basic_compliance.get("compliance_score", 0) < 0.7:
            roadmap.append({
                "priority": 1,
                "timeframe": "immediate",
                "category": "Basic Compliance",
                "actions": basic_compliance.get("compliance_issues", [])[:3],
                "estimated_effort": "high"
            })
        
        # Priority 2: Address phase-specific compliance gaps
        critical_phases = []
        for phase, result in phase_compliance.items():
            if result.get("compliance_score", 0) < 0.5:
                critical_phases.append(phase)
        
        if critical_phases:
            roadmap.append({
                "priority": 2,
                "timeframe": "1-2 weeks",
                "category": "Phase Compliance",
                "actions": [f"Complete {phase.replace('_', ' ')} documentation" for phase in critical_phases],
                "estimated_effort": "medium"
            })
        
        # Priority 3: Improve data quality
        if data_quality.get("quality_score", 0) < 0.7:
            roadmap.append({
                "priority": 3,
                "timeframe": "2-4 weeks", 
                "category": "Data Quality",
                "actions": data_quality.get("quality_issues", [])[:3],
                "estimated_effort": "medium"
            })
        
        # Priority 4: Enhancement opportunities
        roadmap.append({
            "priority": 4,
            "timeframe": "1-3 months",
            "category": "Enhancement",
            "actions": [
                "Implement uncertainty analysis",
                "Add sensitivity analysis",
                "Enhance documentation",
                "Consider third-party verification"
            ],
            "estimated_effort": "low"
        })
        
        return roadmap
    
    def _calculate_compliance_score(self, basic_compliance: Dict[str, Any],
                                  phase_compliance: Dict[str, Any],
                                  data_quality: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall compliance score"""
        
        # Weighted scoring
        weights = {
            "basic_compliance": 0.4,
            "phase_compliance": 0.4,
            "data_quality": 0.2
        }
        
        # Calculate phase compliance average
        phase_scores = [result.get("compliance_score", 0) for result in phase_compliance.values()]
        avg_phase_score = np.mean(phase_scores) if phase_scores else 0
        
        # Calculate weighted overall score
        overall_score = (
            basic_compliance.get("compliance_score", 0) * weights["basic_compliance"] +
            avg_phase_score * weights["phase_compliance"] +
            data_quality.get("quality_score", 0) * weights["data_quality"]
        )
        
        # Determine compliance grade
        if overall_score >= 0.9:
            grade = "A"
            status = "Fully Compliant"
        elif overall_score >= 0.8:
            grade = "B"
            status = "Largely Compliant"
        elif overall_score >= 0.7:
            grade = "C"
            status = "Moderately Compliant"
        elif overall_score >= 0.6:
            grade = "D"
            status = "Minimally Compliant"
        else:
            grade = "F"
            status = "Non-Compliant"
        
        return {
            "overall_score": round(overall_score, 3),
            "grade": grade,
            "status": status,
            "component_scores": {
                "basic_compliance": basic_compliance.get("compliance_score", 0),
                "phase_compliance": avg_phase_score,
                "data_quality": data_quality.get("quality_score", 0)
            },
            "weights_applied": weights
        }
    
    def _generate_compliance_report(self, overall_score: Dict[str, Any],
                                  basic_compliance: Dict[str, Any],
                                  phase_compliance: Dict[str, Any],
                                  data_quality: Dict[str, Any]) -> str:
        """Generate a formatted compliance report"""
        
        report = f"""
ISO 14040/14044 LCA COMPLIANCE ASSESSMENT REPORT
===============================================

OVERALL COMPLIANCE STATUS: {overall_score['status']}
Grade: {overall_score['grade']} ({overall_score['overall_score']:.1%})

COMPLIANCE BREAKDOWN:
-------------------
✓ Basic Compliance: {basic_compliance.get('compliance_score', 0):.1%} ({basic_compliance.get('passed_checks', 0)}/{basic_compliance.get('total_checks', 0)} checks passed)
✓ Phase Compliance: {overall_score['component_scores']['phase_compliance']:.1%}
✓ Data Quality: {data_quality.get('quality_score', 0):.1%} ({data_quality.get('passed_checks', 0)}/{data_quality.get('total_checks', 0)} criteria met)

PHASE-SPECIFIC RESULTS:
----------------------"""
        
        for phase, result in phase_compliance.items():
            status_icon = "✓" if result.get("compliant", False) else "✗"
            report += f"""
{status_icon} {phase.replace('_', ' ').title()}: {result.get('compliance_score', 0):.1%} ({result.get('met_requirements', 0)}/{result.get('total_requirements', 0)})"""
        
        # Add critical issues
        all_issues = (basic_compliance.get('compliance_issues', []) + 
                     data_quality.get('quality_issues', []))
        
        if all_issues:
            report += f"""

CRITICAL ISSUES TO ADDRESS:
--------------------------"""
            for i, issue in enumerate(all_issues[:5], 1):
                report += f"""
{i}. {issue}"""
        
        report += f"""

Assessment completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Methodology: ISO 14040/14044 Standard Compliance Framework
"""
        
        return report

# Compliance Tools
@tool
def check_iso_compliance(lca_study_data: Dict[str, Any], 
                        study_type: str = "internal_decision_support") -> Dict[str, Any]:
    """Check LCA study compliance with ISO 14040/14044 standards"""
    agent = ComplianceAgent()
    return agent.check_lca_compliance(lca_study_data, study_type)

@tool
def validate_functional_unit(functional_unit_description: str) -> Dict[str, Any]:
    """Validate functional unit definition against ISO requirements"""
    agent = ComplianceAgent()
    
    # Query ISO knowledge base for functional unit requirements
    context = agent._query_iso_knowledge_base("functional unit definition requirements", top_k=3)
    
    # Basic validation checks
    validation_results = {
        "clearly_defined": len(functional_unit_description.strip()) > 10,
        "quantitative": any(char.isdigit() for char in functional_unit_description),
        "unit_specified": any(unit in functional_unit_description.lower() 
                            for unit in ['kg', 'ton', 'piece', 'unit', 'liter', 'm2', 'm3']),
        "function_described": len(functional_unit_description.split()) > 3
    }
    
    compliance_score = sum(validation_results.values()) / len(validation_results)
    
    return {
        "functional_unit": functional_unit_description,
        "compliance_score": compliance_score,
        "validation_results": validation_results,
        "compliant": compliance_score >= 0.75,
        "iso_context": [result["content"][:200] for result in context],
        "recommendations": [
            "Include quantitative measure" if not validation_results["quantitative"] else None,
            "Specify measurement unit" if not validation_results["unit_specified"] else None,
            "Provide more detailed description" if not validation_results["function_described"] else None
        ]
    }

@tool
def check_system_boundaries(system_boundaries: Dict[str, Any]) -> Dict[str, Any]:
    """Validate system boundaries definition against ISO requirements"""
    agent = ComplianceAgent()
    
    required_elements = [
        "cradle_to_gate", "gate_to_gate", "cradle_to_grave", "temporal_boundaries",
        "geographical_boundaries", "technological_boundaries", "included_processes",
        "excluded_processes", "cut_off_criteria"
    ]
    
    compliance_results = {}
    for element in required_elements:
        compliance_results[element] = element in system_boundaries
    
    compliance_score = sum(compliance_results.values()) / len(compliance_results)
    
    return {
        "system_boundaries": system_boundaries,
        "compliance_score": compliance_score,
        "required_elements": required_elements,
        "missing_elements": [elem for elem, present in compliance_results.items() if not present],
        "compliant": compliance_score >= 0.6  # 60% threshold
    }

@tool
def validate_impact_categories(impact_categories: List[str]) -> Dict[str, Any]:
    """Validate selected impact categories against ISO recommendations"""
    
    # Standard impact categories per ISO 14040/14044
    recommended_categories = [
        "climate_change", "global_warming_potential", "ozone_depletion",
        "acidification", "eutrophication", "photochemical_ozone_creation",
        "abiotic_depletion", "land_use", "ecotoxicity", "human_toxicity"
    ]
    
    normalized_input = [cat.lower().replace(' ', '_') for cat in impact_categories]
    
    # Check coverage
    coverage_results = {}
    for category in recommended_categories:
        coverage_results[category] = any(category in input_cat for input_cat in normalized_input)
    
    coverage_score = sum(coverage_results.values()) / len(coverage_results)
    
    return {
        "input_categories": impact_categories,
        "coverage_score": coverage_score,
        "recommended_categories": recommended_categories,
        "missing_recommended": [cat for cat, covered in coverage_results.items() if not covered],
        "compliant": coverage_score >= 0.3 or "climate_change" in str(impact_categories).lower()
    }

@tool
def generate_compliance_checklist(study_type: str = "internal_decision_support") -> Dict[str, Any]:
    """Generate ISO 14040/14044 compliance checklist for LCA study"""
    agent = ComplianceAgent()
    
    study_requirements = agent.study_types.get(study_type, agent.study_types["internal_decision_support"])
    
    checklist = {
        "goal_and_scope": [
            "Define intended application clearly",
            "State reasons for carrying out the study",
            "Identify intended audience",
            "Define functional unit quantitatively",
            "Establish system boundaries",
            "Specify data requirements and quality",
            "Document assumptions and limitations"
        ],
        "inventory_analysis": [
            "Establish data collection procedures",
            "Define data quality requirements",
            "Specify allocation procedures",
            "Plan treatment of missing data",
            "Consider uncertainty analysis"
        ],
        "impact_assessment": [
            "Select relevant impact categories",
            "Perform classification of inventory data",
            "Apply characterization factors",
            "Consider normalization (optional)",
            "Apply grouping (optional)",
            "Apply weighting (optional)"
        ],
        "interpretation": [
            "Identify significant issues",
            "Evaluate completeness",
            "Evaluate consistency",
            "Perform sensitivity analysis",
            "Draw conclusions and recommendations"
        ],
        "reporting": [
            "Document methodology clearly",
            "Report all assumptions",
            "Include uncertainty assessment",
            "Provide transparent results"
        ]
    }
    
    if study_requirements["critical_review_required"]:
        checklist["critical_review"] = [
            "Arrange independent critical review",
            "Address reviewer comments",
            "Document review process"
        ]
    
    return {
        "study_type": study_type,
        "compliance_checklist": checklist,
        "critical_review_required": study_requirements["critical_review_required"],
        "public_disclosure": study_requirements["public_disclosure"],
        "total_items": sum(len(items) for items in checklist.values())
    }

@tool
def format_compliance_report(compliance_results: Dict[str, Any]) -> str:
    """Format compliance assessment results into a readable report"""
    
    if not compliance_results.get("success"):
        return f"Compliance check failed: {compliance_results.get('error', 'Unknown error')}"
    
    overall_score = compliance_results["overall_compliance_score"]
    
    return f"""
ISO 14040/14044 LCA COMPLIANCE REPORT
===================================

Study Type: {compliance_results['study_type'].replace('_', ' ').title()}
Assessment Date: {compliance_results['assessment_timestamp'][:19]}

OVERALL COMPLIANCE STATUS
------------------------
Status: {overall_score['status']}
Grade: {overall_score['grade']}
Score: {overall_score['overall_score']:.1%}

DETAILED BREAKDOWN
-----------------
Basic Compliance: {overall_score['component_scores']['basic_compliance']:.1%}
Phase Compliance: {overall_score['component_scores']['phase_compliance']:.1%}
Data Quality: {overall_score['component_scores']['data_quality']:.1%}

{compliance_results.get('compliance_report', '')}

AI INSIGHTS
-----------
{compliance_results.get('ai_insights', {}).get('ai_compliance_analysis', 'AI insights not available')[:500]}...

For detailed recommendations, review the full compliance assessment results.
"""