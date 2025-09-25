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
    errors: list
    current_step: str

class LCASystem:
    """Main LCA Analysis System orchestrating all agents with LangGraph"""
    
    def __init__(self):
        # Initialize all agents
        self.data_ingestion_agent = DataIngestionAgent()
        self.lca_agent = LCAAgent()
        self.compliance_agent = ComplianceAgent()
        self.reporting_agent = ReportingAgent()
        
        # Create results directory
        self.results_dir = Path("./results")
        self.results_dir.mkdir(exist_ok=True)
        
        # Create the LangGraph workflow
        self.workflow = self._create_graph()
        
    def _create_graph(self) -> StateGraph:
        """Create the LangGraph workflow for LCA analysis"""
        
        workflow = StateGraph(LCAWorkflowState)

        # Add all agents
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

        return workflow.compile()
    
    def _data_ingestion_node(self, state: LCAWorkflowState) -> LCAWorkflowState:
        """Node for data ingestion and preprocessing"""
        logger.info("Executing data ingestion node...")
        
        try:
            input_data = state["input_data"]
            
            # Handle different input types
            if "file_path" in input_data:
                # File-based input
                ingested_data = self.data_ingestion_agent.ingest_data(
                    file_path=input_data["file_path"],
                    file_type=input_data.get("file_type", "excel")
                )
            else:
                # Direct parameter input
                ingested_data = {
                    "success": True,
                    "processed_data": {
                        "metal_type": input_data.get("metal_type", "steel"),
                        "production_kg": input_data.get("production_kg", 1000),
                        "recycled_fraction": input_data.get("recycled_fraction", 0.3),
                        "region": input_data.get("region", "US_average")
                    },
                    "data_quality": {"completeness": 1.0, "accuracy": 1.0}
                }
            
            state["ingested_data"] = ingested_data
            state["current_step"] = "data_ingestion_complete"
            state["messages"].append({"role": "system", "content": "Data ingestion completed successfully"})
            
            if not ingested_data.get("success"):
                state["errors"].append("Data ingestion failed")
                state["workflow_status"] = "failed"
            
        except Exception as e:
            logger.error(f"Error in data ingestion node: {e}")
            state["errors"].append(f"Data ingestion error: {str(e)}")
            state["workflow_status"] = "failed"
        
        return state
    
    def _lca_analysis_node(self, state: LCAWorkflowState) -> LCAWorkflowState:
        """Node for LCA calculations and analysis"""
        logger.info("Executing LCA analysis node...")
        
        try:
            ingested_data = state["ingested_data"]
            processed_data = ingested_data.get("processed_data", {})
            
            # Run LCA analysis using the correct method name
            lca_results = self.lca_agent.perform_lca_analysis(
                metal_type=processed_data.get("metal_type", "steel"),
                production_kg=processed_data.get("production_kg", 1000),
                recycled_fraction=processed_data.get("recycled_fraction", 0.3),
                region=processed_data.get("region", "US_average")
            )
            
            state["lca_results"] = lca_results
            state["current_step"] = "lca_analysis_complete"
            state["messages"].append({"role": "system", "content": "LCA analysis completed successfully"})
            
            if not lca_results.get("success"):
                state["errors"].append("LCA analysis failed")
                state["workflow_status"] = "failed"
            
        except Exception as e:
            logger.error(f"Error in LCA analysis node: {e}")
            state["errors"].append(f"LCA analysis error: {str(e)}")
            state["workflow_status"] = "failed"
        
        return state
    
    def _compliance_check_node(self, state: LCAWorkflowState) -> LCAWorkflowState:
        """Node for ISO compliance checking"""
        logger.info("Executing compliance check node...")
        
        try:
            lca_results = state["lca_results"]
            input_data = state["input_data"]
            
            # Run compliance check
            compliance_results = self.compliance_agent.check_lca_compliance(
                lca_study_data=lca_results,
                study_type=input_data.get("study_type", "internal_decision_support")
            )
            
            state["compliance_results"] = compliance_results
            state["current_step"] = "compliance_check_complete"
            state["messages"].append({"role": "system", "content": "Compliance check completed successfully"})
            
            if not compliance_results.get("success"):
                state["errors"].append("Compliance check failed")
                state["workflow_status"] = "failed"
            
        except Exception as e:
            logger.error(f"Error in compliance check node: {e}")
            state["errors"].append(f"Compliance check error: {str(e)}")
            state["workflow_status"] = "failed"
        
        return state
    
    def _report_generation_node(self, state: LCAWorkflowState) -> LCAWorkflowState:
        """Node for report generation with visualizations"""
        logger.info("Executing report generation node...")
        
        try:
            lca_results = state["lca_results"]
            compliance_results = state["compliance_results"]
            input_data = state["input_data"]
            
            # Generate comprehensive report
            report_results = self.reporting_agent.generate_report(
                lca_results=lca_results,
                compliance_results=compliance_results,
                report_type=input_data.get("report_type", "technical"),
                format_type=input_data.get("format_type", "pdf")
            )
            
            state["report_results"] = report_results
            state["current_step"] = "report_generation_complete"
            state["workflow_status"] = "completed"
            state["messages"].append({"role": "system", "content": "Report generation completed successfully"})
            
            if not report_results.get("success"):
                state["errors"].append("Report generation failed")
                state["workflow_status"] = "failed"
            
        except Exception as e:
            logger.error(f"Error in report generation node: {e}")
            state["errors"].append(f"Report generation error: {str(e)}")
            state["workflow_status"] = "failed"
        
        return state
    
    def run_complete_analysis(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run complete LCA analysis workflow using LangGraph"""
        
        try:
            logger.info("Starting complete LCA analysis workflow with LangGraph")
            
            # Initialize workflow state
            initial_state = LCAWorkflowState(
                messages=[{"role": "system", "content": "Starting LCA analysis workflow"}],
                input_data=input_data,
                ingested_data={},
                lca_results={},
                compliance_results={},
                report_results={},
                workflow_status="running",
                errors=[],
                current_step="initializing"
            )
            
            # Execute the workflow
            final_state = self.workflow.invoke(initial_state)
            
            # Check if workflow completed successfully
            if final_state["workflow_status"] == "failed":
                return {
                    "success": False,
                    "errors": final_state["errors"],
                    "workflow_timestamp": datetime.now().isoformat()
                }
            
            # Compile final results
            final_results = {
                "success": True,
                "analysis_id": f"LCA_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "input_parameters": input_data,
                "ingested_data": final_state["ingested_data"],
                "lca_results": final_state["lca_results"],
                "compliance_assessment": final_state["compliance_results"],
                "report_generation": final_state["report_results"],
                "workflow_messages": final_state["messages"],
                "workflow_timestamp": datetime.now().isoformat(),
                "summary": self._generate_workflow_summary(
                    final_state["lca_results"], 
                    final_state["compliance_results"], 
                    final_state["report_results"]
                )
            }
            
            # Save results
            self._save_results(final_results)
            
            logger.info("Complete LCA analysis workflow completed successfully")
            return final_results
            
        except Exception as e:
            logger.error(f"Error in complete analysis workflow: {e}")
            return {
                "success": False,
                "error": str(e),
                "workflow_timestamp": datetime.now().isoformat()
            }
    
    def run_file_based_analysis(self, file_path: str, file_type: str = "excel") -> Dict[str, Any]:
        """Run analysis from uploaded file"""
        input_data = {
            "file_path": file_path,
            "file_type": file_type,
            "study_type": "internal_decision_support",
            "report_type": "technical",
            "format_type": "all"  # Generate all formats including visualizations
        }
        
        return self.run_complete_analysis(input_data)
    
    def _generate_workflow_summary(self, lca_results: Dict[str, Any], 
                                 compliance_results: Dict[str, Any],
                                 report_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate workflow summary"""
        
        # Extract key metrics
        lca_data = lca_results.get("lca_results", {})
        gwp_impact = lca_data.get("gwp_impact", {})
        
        return {
            "lca_summary": {
                "total_carbon_footprint_kg_co2_eq": gwp_impact.get("total_kg_co2_eq", 0),
                "carbon_intensity_per_kg": gwp_impact.get("kg_co2_eq_per_kg_metal", 0),
                "sustainability_score": lca_results.get("ai_insights", {}).get("sustainability_score", {}).get("overall_score", 0),
                "circularity_index": lca_data.get("circularity_metrics", {}).get("circularity_index", 0)
            },
            "compliance_summary": {
                "compliance_grade": compliance_results.get("overall_compliance_score", {}).get("grade", "N/A"),
                "compliance_score": compliance_results.get("overall_compliance_score", {}).get("overall_score", 0),
                "status": compliance_results.get("overall_compliance_score", {}).get("status", "Unknown")
            },
            "report_summary": {
                "formats_generated": len(report_results.get("output_files", {})),
                "visualizations_created": report_results.get("visualizations_created", 0),
                "report_files": list(report_results.get("output_files", {}).values())
            }
        }
    
    def _save_results(self, results: Dict[str, Any]):
        """Save analysis results"""
        try:
            analysis_id = results.get("analysis_id")
            results_file = self.results_dir / f"{analysis_id}_complete_results.json"
            
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            logger.info(f"Results saved to: {results_file}")
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")

# Convenience functions
def run_quick_lca_analysis(metal_type: str, production_kg: float, 
                          recycled_fraction: float = 0.3) -> Dict[str, Any]:
    """Run quick LCA analysis with default settings"""
    system = LCASystem()
    
    input_data = {
        "metal_type": metal_type,
        "production_kg": production_kg,
        "recycled_fraction": recycled_fraction,
        "region": "US_average",
        "study_type": "internal_decision_support",
        "report_type": "technical",
        "format_type": "pdf"
    }
    
    return system.run_complete_analysis(input_data)

def run_compliance_focused_analysis(metal_type: str, production_kg: float,
                                   study_type: str = "comparative_assertion") -> Dict[str, Any]:
    """Run analysis focused on compliance requirements"""
    system = LCASystem()
    
    input_data = {
        "metal_type": metal_type,
        "production_kg": production_kg,
        "recycled_fraction": 0.25,
        "region": "US_average",
        "study_type": study_type,
        "report_type": "regulatory_submission",
        "format_type": "all"
    }
    
    return system.run_complete_analysis(input_data)

def run_file_analysis(file_path: str, file_type: str = "excel") -> Dict[str, Any]:
    """Run analysis from uploaded file"""
    system = LCASystem()
    return system.run_file_based_analysis(file_path, file_type)

if __name__ == "__main__":
    # Example usage
    print("LCA Analysis System with LangGraph Workflow")
    print("=" * 50)
    
    # Quick test run
    test_results = run_quick_lca_analysis(
        metal_type="aluminum",
        production_kg=1000,
        recycled_fraction=0.4
    )
    
    if test_results.get("success"):
        print("✅ Analysis completed successfully!")
        summary = test_results["summary"]
        print(f"🌍 Carbon Footprint: {summary['lca_summary']['total_carbon_footprint_kg_co2_eq']:.1f} kg CO2-eq")
        print(f"📊 Compliance Grade: {summary['compliance_summary']['compliance_grade']}")
        print(f"🔄 Circularity Index: {summary['lca_summary']['circularity_index']:.2f}")
        print(f"📄 Reports Generated: {summary['report_summary']['formats_generated']}")
    else:
        print("❌ Analysis failed:", test_results.get("error"))