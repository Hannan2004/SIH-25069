"""
LCA Analysis System - Main Orchestrator
Coordinates all agents: LCA, Data Quality, Compliance, and Reporting
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

# Import all agents
from lca_agent import LCAAgent, calculate_lca_impact
from data_ingestion_agent import DataIngestionAgent, assess_data_quality
from compliance_agent import ComplianceAgent, check_iso_compliance
from reporting_agent import ReportingAgent, generate_lca_report

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LCASystem:
    """Main LCA Analysis System orchestrating all agents"""
    
    def __init__(self):
        # Initialize all agents
        self.lca_agent = LCAAgent()
        self.data_quality_agent = DataQualityAgent()
        self.compliance_agent = ComplianceAgent()
        self.reporting_agent = ReportingAgent()
        
        # Create results directory
        self.results_dir = Path("./results")
        self.results_dir.mkdir(exist_ok=True)
        
    def run_complete_analysis(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run complete LCA analysis workflow"""
        
        try:
            logger.info("Starting complete LCA analysis workflow")
            
            # Step 1: LCA Calculation
            logger.info("Step 1: Running LCA calculations...")
            lca_results = self.lca_agent.calculate_metal_lca(
                metal_type=input_data.get("metal_type", "steel"),
                production_kg=input_data.get("production_kg", 1000),
                recycled_fraction=input_data.get("recycled_fraction", 0.3),
                region=input_data.get("region", "US_average")
            )
            
            if not lca_results.get("success"):
                return {"error": "LCA calculation failed", "details": lca_results}
            
            # Step 2: Data Quality Assessment
            logger.info("Step 2: Assessing data quality...")
            data_quality_results = self.data_quality_agent.assess_data_quality(lca_results)
            
            # Step 3: Compliance Check
            logger.info("Step 3: Checking ISO compliance...")
            compliance_results = self.compliance_agent.check_lca_compliance(
                lca_results, 
                study_type=input_data.get("study_type", "internal_decision_support")
            )
            
            # Step 4: Generate Reports
            logger.info("Step 4: Generating comprehensive reports...")
            report_results = self.reporting_agent.generate_report(
                lca_results=lca_results,
                compliance_results=compliance_results,
                report_type=input_data.get("report_type", "technical"),
                format_type=input_data.get("format_type", "pdf")
            )
            
            # Compile final results
            final_results = {
                "success": True,
                "analysis_id": f"LCA_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "input_parameters": input_data,
                "lca_results": lca_results,
                "data_quality_assessment": data_quality_results,
                "compliance_assessment": compliance_results,
                "report_generation": report_results,
                "workflow_timestamp": datetime.now().isoformat(),
                "summary": self._generate_workflow_summary(
                    lca_results, data_quality_results, compliance_results, report_results
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
    
    def _generate_workflow_summary(self, lca_results: Dict[str, Any], 
                                 data_quality_results: Dict[str, Any],
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
                "sustainability_score": lca_results.get("ai_insights", {}).get("sustainability_score", {}).get("overall_score", 0)
            },
            "data_quality_summary": {
                "overall_score": data_quality_results.get("overall_quality_score", 0),
                "completeness": data_quality_results.get("completeness_score", 0),
                "major_issues": len(data_quality_results.get("issues", []))
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
            
            import json
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

if __name__ == "__main__":
    # Example usage
    print("LCA Analysis System")
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
        print(f"📈 Data Quality Score: {summary['data_quality_summary']['overall_score']:.1%}")
        print(f"📄 Reports Generated: {summary['report_summary']['formats_generated']}")
    else:
        print("❌ Analysis failed:", test_results.get("error"))