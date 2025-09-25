"""
FastAPI REST API for LCA Analysis System
Provides endpoints for all LCA analysis functions
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import uvicorn
import logging
from datetime import datetime

from main import LCASystem, run_quick_lca_analysis, run_compliance_focused_analysis

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="LCA Analysis System API",
    description="Comprehensive Life Cycle Assessment API with AI-enhanced analysis",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize LCA System
lca_system = LCASystem()

# Pydantic models
class LCARequest(BaseModel):
    metal_type: str = Field(..., description="Type of metal (steel, aluminum, copper, etc.)")
    production_kg: float = Field(..., gt=0, description="Production amount in kg")
    recycled_fraction: float = Field(0.3, ge=0, le=1, description="Fraction of recycled content")
    region: str = Field("US_average", description="Production region")
    study_type: str = Field("internal_decision_support", description="Type of LCA study")
    report_type: str = Field("technical", description="Type of report to generate")
    format_type: str = Field("pdf", description="Output format (pdf, html, json, all)")

class QuickLCARequest(BaseModel):
    metal_type: str
    production_kg: float = Field(..., gt=0)
    recycled_fraction: float = Field(0.3, ge=0, le=1)

class ComplianceRequest(BaseModel):
    metal_type: str
    production_kg: float = Field(..., gt=0)
    study_type: str = Field("comparative_assertion")

# API Endpoints
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "LCA Analysis System API",
        "version": "1.0.0",
        "status": "active",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "complete_analysis": "/api/v1/lca/complete",
            "quick_analysis": "/api/v1/lca/quick",
            "compliance_analysis": "/api/v1/lca/compliance",
            "health_check": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "system_status": {
            "lca_agent": "active",
            "data_quality_agent": "active", 
            "compliance_agent": "active",
            "reporting_agent": "active"
        }
    }

@app.post("/api/v1/lca/complete")
async def complete_lca_analysis(request: LCARequest):
    """Run complete LCA analysis with all agents"""
    try:
        logger.info(f"Starting complete LCA analysis for {request.metal_type}")
        
        input_data = {
            "metal_type": request.metal_type,
            "production_kg": request.production_kg,
            "recycled_fraction": request.recycled_fraction,
            "region": request.region,
            "study_type": request.study_type,
            "report_type": request.report_type,
            "format_type": request.format_type
        }
        
        results = lca_system.run_complete_analysis(input_data)
        
        if not results.get("success"):
            raise HTTPException(status_code=400, detail=results.get("error", "Analysis failed"))
        
        return {
            "status": "success",
            "message": "Complete LCA analysis completed successfully",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error in complete LCA analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/lca/quick")
async def quick_lca_analysis(request: QuickLCARequest):
    """Run quick LCA analysis with default settings"""
    try:
        logger.info(f"Starting quick LCA analysis for {request.metal_type}")
        
        results = run_quick_lca_analysis(
            metal_type=request.metal_type,
            production_kg=request.production_kg,
            recycled_fraction=request.recycled_fraction
        )
        
        if not results.get("success"):
            raise HTTPException(status_code=400, detail=results.get("error", "Analysis failed"))
        
        # Return simplified response for quick analysis
        summary = results["summary"]
        return {
            "status": "success",
            "message": "Quick LCA analysis completed",
            "analysis_id": results["analysis_id"],
            "carbon_footprint_kg_co2_eq": summary["lca_summary"]["total_carbon_footprint_kg_co2_eq"],
            "carbon_intensity_per_kg": summary["lca_summary"]["carbon_intensity_per_kg"],
            "sustainability_score": summary["lca_summary"]["sustainability_score"],
            "data_quality_score": summary["data_quality_summary"]["overall_score"],
            "compliance_grade": summary["compliance_summary"]["compliance_grade"],
            "report_files": summary["report_summary"]["report_files"],
            "timestamp": results["workflow_timestamp"]
        }
        
    except Exception as e:
        logger.error(f"Error in quick LCA analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/lca/compliance")
async def compliance_focused_analysis(request: ComplianceRequest):
    """Run compliance-focused LCA analysis"""
    try:
        logger.info(f"Starting compliance-focused analysis for {request.metal_type}")
        
        results = run_compliance_focused_analysis(
            metal_type=request.metal_type,
            production_kg=request.production_kg,
            study_type=request.study_type
        )
        
        if not results.get("success"):
            raise HTTPException(status_code=400, detail=results.get("error", "Analysis failed"))
        
        # Return compliance-focused response
        compliance_data = results["compliance_assessment"]
        return {
            "status": "success",
            "message": "Compliance-focused analysis completed",
            "analysis_id": results["analysis_id"],
            "compliance_results": {
                "overall_score": compliance_data.get("overall_compliance_score", {}).get("overall_score", 0),
                "grade": compliance_data.get("overall_compliance_score", {}).get("grade", "N/A"),
                "status": compliance_data.get("overall_compliance_score", {}).get("status", "Unknown"),
                "basic_compliance": compliance_data.get("basic_compliance", {}),
                "phase_compliance": compliance_data.get("phase_compliance", {}),
                "recommendations": compliance_data.get("ai_insights", {}).get("compliance_recommendations", [])
            },
            "report_files": results["summary"]["report_summary"]["report_files"],
            "timestamp": results["workflow_timestamp"]
        }
        
    except Exception as e:
        logger.error(f"Error in compliance analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/lca/supported-metals")
async def get_supported_metals():
    """Get list of supported metal types"""
    return {
        "supported_metals": [
            "steel", "aluminum", "copper", "zinc", "lead", 
            "nickel", "tin", "magnesium", "titanium"
        ],
        "regions": [
            "US_average", "EU_average", "China", "Global_average"
        ],
        "study_types": [
            "internal_decision_support", 
            "comparative_assertion", 
            "public_communication"
        ]
    }

@app.get("/api/v1/reports/{analysis_id}")
async def get_analysis_report(analysis_id: str):
    """Retrieve specific analysis report"""
    try:
        # This would implement report retrieval logic
        # For now, return placeholder
        return {
            "message": f"Report retrieval for {analysis_id}",
            "status": "feature_pending"
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Report not found: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "api:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )