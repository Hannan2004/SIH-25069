"""
LCA Analysis System - Main Orchestrator with LangGraph Workflow
Coordinates all agents: Data Ingestion, LCA, Compliance, and Reporting
"""

import os
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional, TypedDict, Annotated
from pathlib import Path
import uuid

# LangGraph imports
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

# Import all agents
from lca_agent import LCAAgent
from data_ingestion_agent import DataIngestionAgent
from compliance_agent import ComplianceAgent
from reporting_agent import ReportingAgent

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the state for LangGraph workflow
class LCAWorkflowState(TypedDict):
    """State for LCA analysis workflow"""
    messages: Annotated[list, add_messages]
    input_data: Dict[str, Any]
    ingested_data: Dict[str, Any]
    lca_results: Dict[str, Any]
    compliance_results: Dict[str, Any]
    report_results: Dict[str, Any]
    workflow_status: str
    analysis_id: str
    errors: list

class LCASystem:
    """Main LCA System with LangGraph workflow orchestration"""
    
    def __init__(self):
        # Initialize all agents
        self.data_agent = DataIngestionAgent()
        self.lca_agent = LCAAgent()
        self.compliance_agent = ComplianceAgent()
        self.reporting_agent = ReportingAgent()
        
        # Build LangGraph workflow
        self.workflow = self._build_workflow()
        self.app = self.workflow.compile()
    
    def _build_workflow(self) -> StateGraph:
        """Build LangGraph workflow"""
        workflow = StateGraph(LCAWorkflowState)
        
        # Add workflow nodes
        workflow.add_node("data_ingestion", self._data_ingestion_node)
        workflow.add_node("lca_analysis", self._lca_analysis_node)
        workflow.add_node("compliance_check", self._compliance_check_node)
        workflow.add_node("report_generation", self._report_generation_node)
        
        # Define workflow edges
        workflow.set_entry_point("data_ingestion")
        workflow.add_edge("data_ingestion", "lca_analysis")
        workflow.add_edge("lca_analysis", "compliance_check")
        workflow.add_edge("compliance_check", "report_generation")
        workflow.add_edge("report_generation", END)
        
        return workflow
    
    def _data_ingestion_node(self, state: LCAWorkflowState) -> LCAWorkflowState:
        """Data ingestion workflow node"""
        try:
            logger.info("Executing data ingestion node")
            
            input_data = state["input_data"]
            
            # Handle file-based input
            if "file_path" in input_data:
                result = self.data_agent.ingest_data(
                    file_path=input_data["file_path"],
                    file_type=input_data.get("file_type", "csv")
                )
            else:
                # Handle direct scenario data
                scenarios = input_data.get("scenarios", [input_data])
                result = {
                    "success": True,
                    "processed_data": {
                        "scenarios": scenarios,
                        "total_scenarios": len(scenarios)
                    },
                    "records_count": len(scenarios)
                }
            
            if not result.get("success"):
                state["errors"].append(f"Data ingestion failed: {result.get('error')}")
                state["workflow_status"] = "failed"
                return state
            
            state["ingested_data"] = result
            state["messages"].append({"role": "system", "content": f"Data ingestion completed: {result.get('records_count', 0)} records processed"})
            
        except Exception as e:
            logger.error(f"Data ingestion node error: {e}")
            state["errors"].append(f"Data ingestion error: {str(e)}")
            state["workflow_status"] = "failed"
        
        return state
    
    def _lca_analysis_node(self, state: LCAWorkflowState) -> LCAWorkflowState:
        """LCA analysis workflow node"""
        try:
            logger.info("Executing LCA analysis node")
            
            if state["workflow_status"] == "failed":
                return state
            
            # Get processed data
            processed_data = state["ingested_data"].get("processed_data", {})
            analysis_type = state["input_data"].get("analysis_type", "cradle_to_gate")
            
            # Perform LCA analysis
            result = self.lca_agent.perform_lca_analysis(
                production_data=processed_data,
                analysis_type=analysis_type
            )
            
            if not result.get("success"):
                state["errors"].append(f"LCA analysis failed: {result.get('error')}")
                state["workflow_status"] = "failed"
                return state
            
            state["lca_results"] = result
            
            # Extract key metrics for message
            lca_data = result.get("lca_results", {})
            gwp_impact = lca_data.get("gwp_impact", {})
            total_emissions = gwp_impact.get("total_kg_co2_eq", 0)
            
            state["messages"].append({
                "role": "system", 
                "content": f"LCA analysis completed: {total_emissions:.1f} kg CO2-eq total emissions"
            })
            
        except Exception as e:
            logger.error(f"LCA analysis node error: {e}")
            state["errors"].append(f"LCA analysis error: {str(e)}")
            state["workflow_status"] = "failed"
        
        return state
    
    def _compliance_check_node(self, state: LCAWorkflowState) -> LCAWorkflowState:
        """Compliance check workflow node"""
        try:
            logger.info("Executing compliance check node")
            
            if state["workflow_status"] == "failed":
                return state
            
            # Get LCA results and study type
            lca_results = state["lca_results"]
            study_type = state["input_data"].get("study_type", "internal_decision_support")
            
            # Perform compliance check
            result = self.compliance_agent.check_lca_compliance(
                lca_study_data=lca_results,
                study_type=study_type
            )
            
            if not result.get("success"):
                state["errors"].append(f"Compliance check failed: {result.get('error')}")
                state["workflow_status"] = "failed"
                return state
            
            state["compliance_results"] = result
            
            # Extract compliance score for message
            overall_score = result.get("overall_compliance_score", {})
            grade = overall_score.get("grade", "N/A")
            score = overall_score.get("overall_score", 0)
            
            state["messages"].append({
                "role": "system",
                "content": f"Compliance check completed: Grade {grade} ({score:.1%} compliance)"
            })
            
        except Exception as e:
            logger.error(f"Compliance check node error: {e}")
            state["errors"].append(f"Compliance check error: {str(e)}")
            state["workflow_status"] = "failed"
        
        return state
    
    def _report_generation_node(self, state: LCAWorkflowState) -> LCAWorkflowState:
        """Report generation workflow node"""
        try:
            logger.info("Executing report generation node")
            
            if state["workflow_status"] == "failed":
                return state
            
            # Get results and report parameters
            lca_results = state["lca_results"]
            compliance_results = state["compliance_results"]
            report_type = state["input_data"].get("report_type", "technical")
            format_type = state["input_data"].get("format_type", "pdf")
            
            # Generate report
            result = self.reporting_agent.generate_report(
                lca_results=lca_results,
                compliance_results=compliance_results,
                report_type=report_type,
                format_type=format_type
            )
            
            if not result.get("success"):
                state["errors"].append(f"Report generation failed: {result.get('error')}")
                state["workflow_status"] = "failed"
                return state
            
            state["report_results"] = result
            state["workflow_status"] = "completed"
            
            # Extract report info for message
            formats_generated = len(result.get("output_files", {}))
            charts_created = result.get("visualizations_created", 0)
            
            state["messages"].append({
                "role": "system",
                "content": f"Report generation completed: {formats_generated} formats, {charts_created} visualizations"
            })
            
        except Exception as e:
            logger.error(f"Report generation node error: {e}")
            state["errors"].append(f"Report generation error: {str(e)}")
            state["workflow_status"] = "failed"
        
        return state
    
    def run_complete_analysis(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run complete LCA analysis using LangGraph workflow"""
        try:
            logger.info("Starting complete LCA analysis workflow")
            
            # Generate unique analysis ID
            analysis_id = str(uuid.uuid4())[:8]
            
            # Initialize workflow state
            initial_state = {
                "messages": [],
                "input_data": input_data,
                "ingested_data": {},
                "lca_results": {},
                "compliance_results": {},
                "report_results": {},
                "workflow_status": "running",
                "analysis_id": analysis_id,
                "errors": []
            }
            
            # Execute workflow
            final_state = self.app.invoke(initial_state)
            
            # Check if workflow completed successfully
            if final_state["workflow_status"] != "completed":
                return {
                    "success": False,
                    "error": "Workflow failed to complete",
                    "errors": final_state["errors"],
                    "analysis_id": analysis_id
                }
            
            # Generate summary
            summary = self._generate_summary(final_state)
            
            return {
                "success": True,
                "analysis_id": analysis_id,
                "workflow_status": final_state["workflow_status"],
                "workflow_messages": final_state["messages"],
                "workflow_timestamp": datetime.now().isoformat(),
                "summary": summary,
                "detailed_results": {
                    "ingestion": final_state["ingested_data"],
                    "lca": final_state["lca_results"],
                    "compliance": final_state["compliance_results"],
                    "reporting": final_state["report_results"]
                }
            }
            
        except Exception as e:
            logger.error(f"Complete analysis error: {e}")
            return {"error": str(e), "success": False}
    
    def _generate_summary(self, state: LCAWorkflowState) -> Dict[str, Any]:
        """Generate analysis summary"""
        try:
            # LCA summary
            lca_results = state["lca_results"].get("lca_results", {})
            gwp_impact = lca_results.get("gwp_impact", {})
            circularity = lca_results.get("circularity_metrics", {})
            sustainability = state["lca_results"].get("ai_insights", {}).get("sustainability_score", {})
            
            lca_summary = {
                "total_carbon_footprint_kg_co2_eq": gwp_impact.get("total_kg_co2_eq", 0),
                "carbon_intensity_per_kg": gwp_impact.get("kg_co2_eq_per_kg_material", 0),
                "circularity_index": circularity.get("circularity_index", circularity.get("weighted_circularity_index", 0)),
                "sustainability_score": sustainability.get("overall_score", 0)
            }
            
            # Compliance summary
            compliance_results = state["compliance_results"]
            overall_compliance = compliance_results.get("overall_compliance_score", {})
            
            compliance_summary = {
                "compliance_score": overall_compliance.get("overall_score", 0),
                "compliance_grade": overall_compliance.get("grade", "N/A"),
                "status": overall_compliance.get("status", "Unknown")
            }
            
            # Report summary
            report_results = state["report_results"]
            report_summary = {
                "formats_generated": len(report_results.get("output_files", {})),
                "charts_created": report_results.get("visualizations_created", 0),
                "report_files": list(report_results.get("output_files", {}).values())
            }
            
            return {
                "lca_summary": lca_summary,
                "compliance_summary": compliance_summary,
                "report_summary": report_summary
            }
            
        except Exception as e:
            logger.error(f"Summary generation error: {e}")
            return {"error": str(e)}

# Convenience functions for direct usage
def run_quick_lca_analysis(material_type: str, mass_kg: float, 
                          recycled_content_pct: float = 30) -> Dict[str, Any]:
    """Quick LCA analysis with default parameters"""
    system = LCASystem()
    
    # Create simplified input data
    input_data = {
        "scenarios": [{
            "material_type": material_type.lower(),
            "mass_kg": mass_kg,
            "energy_intensity": {"virgin_process_kwh_per_kg": 15.0, "recycled_process_kwh_per_kg": 3.0},
            "direct_emissions": {"virgin_kg_co2e_per_kg": 2.0, "recycled_kg_co2e_per_kg": 0.5},
            "grid_composition": {"coal_pct": 30, "gas_pct": 40, "oil_pct": 5, "nuclear_pct": 10, 
                               "hydro_pct": 5, "wind_pct": 5, "solar_pct": 3, "other_pct": 2},
            "transport": {"mode": "truck", "distance_km": 100, "weight_t": mass_kg/1000, 
                         "emission_factor_kg_co2e_per_tkm": 0.062},
            "material_emission_factors": {"virgin_kg_co2e_per_kg": 11.5, "secondary_kg_co2e_per_kg": 0.64},
            "recycling": {"collection_rate_pct": 75, "recycling_efficiency_pct": 90, 
                         "secondary_content_existing_pct": recycled_content_pct}
        }],
        "analysis_type": "cradle_to_gate",
        "study_type": "internal_decision_support",
        "report_type": "technical",
        "format_type": "json"
    }
    
    return system.run_complete_analysis(input_data)

def run_file_analysis(file_path: str, file_type: str = "csv") -> Dict[str, Any]:
    """File-based LCA analysis"""
    system = LCASystem()
    
    input_data = {
        "file_path": file_path,
        "file_type": file_type,
        "analysis_type": "cradle_to_gate",
        "study_type": "internal_decision_support",
        "report_type": "technical",
        "format_type": "all"
    }
    
    return system.run_complete_analysis(input_data)

if __name__ == "__main__":
    # Test the system
    print("Testing LCA System...")
    
    result = run_quick_lca_analysis("aluminum", 1000.0, 30.0)
    
    if result.get("success"):
        print(f"✅ Analysis completed successfully!")
        print(f"Analysis ID: {result['analysis_id']}")
        summary = result.get("summary", {})
        lca_summary = summary.get("lca_summary", {})
        print(f"Carbon Footprint: {lca_summary.get('total_carbon_footprint_kg_co2_eq', 0):.1f} kg CO2-eq")
    else:
        print(f"❌ Analysis failed: {result.get('error')}")