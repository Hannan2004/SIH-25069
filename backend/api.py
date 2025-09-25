"""
FastAPI REST API for LCA Analysis System
Provides endpoints for all LCA analysis functions including file upload
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import uvicorn
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path

from main import LCASystem, run_quick_lca_analysis, run_compliance_focused_analysis, run_file_analysis

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="LCA Analysis System API",
    description="Comprehensive Life Cycle Assessment API with AI-enhanced analysis and LangGraph workflow",
    version="1.0.0"
)

# CORS middleware - configured for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js default
        "http://127.0.0.1:3000",
        "https://your-nextjs-domain.com"  # Replace with your production domain
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Initialize LCA System
lca_system = LCASystem()

# Create upload directory
UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

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

class FileAnalysisRequest(BaseModel):
    file_type: str = Field("excel", description="Type of uploaded file")
    study_type: str = Field("internal_decision_support")
    report_type: str = Field("technical")
    format_type: str = Field("all")

# API Endpoints
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "LCA Analysis System API with LangGraph Workflow",
        "version": "1.0.0",
        "status": "active",
        "timestamp": datetime.now().isoformat(),
        "features": [
            "Complete LCA Analysis with LangGraph workflow",
            "File upload support (Excel/CSV)",
            "ISO compliance checking",
            "AI-enhanced insights",
            "Multiple report formats",
            "Circularity metrics",
            "Sankey diagrams and visualizations"
        ],
        "endpoints": {
            "complete_analysis": "/api/v1/lca/complete",
            "quick_analysis": "/api/v1/lca/quick",
            "compliance_analysis": "/api/v1/lca/compliance",
            "file_analysis": "/api/v1/lca/file-upload",
            "health_check": "/health",
            "supported_metals": "/api/v1/lca/supported-metals"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "system_status": {
            "data_ingestion_agent": "active",
            "lca_agent": "active",
            "compliance_agent": "active",
            "reporting_agent": "active",
            "langgraph_workflow": "active"
        },
        "workflow_nodes": [
            "data_ingestion",
            "lca_analysis", 
            "compliance_check",
            "report_generation"
        ]
    }

@app.post("/api/v1/lca/complete")
async def complete_lca_analysis(request: LCARequest):
    """Run complete LCA analysis with LangGraph workflow"""
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
            "analysis_id": results["analysis_id"],
            "workflow_status": "completed",
            "results": results,
            "summary": results["summary"],
            "visualizations": results.get("report_generation", {}).get("output_files", {}),
            "timestamp": results["workflow_timestamp"]
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
            "circularity_index": summary["lca_summary"]["circularity_index"],
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

@app.post("/api/v1/lca/file-upload")
async def file_based_analysis(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    file_type: str = Form("excel"),
    study_type: str = Form("internal_decision_support"),
    report_type: str = Form("technical"),
    format_type: str = Form("all")
):
    """Upload file and run LCA analysis using LangGraph workflow"""
    try:
        # Validate file type
        allowed_types = [
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # xlsx
            "application/vnd.ms-excel",  # xls
            "text/csv",  # csv
            "application/csv"
        ]
        
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type: {file.content_type}. Supported: Excel (.xlsx, .xls) and CSV (.csv)"
            )
        
        # Save uploaded file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = Path(file.filename).suffix
        saved_filename = f"lca_data_{timestamp}{file_extension}"
        file_path = UPLOAD_DIR / saved_filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"File uploaded successfully: {saved_filename}")
        
        # Run analysis using LangGraph workflow
        results = run_file_analysis(str(file_path), file_type)
        
        # Clean up uploaded file after processing
        background_tasks.add_task(os.remove, file_path)
        
        if not results.get("success"):
            raise HTTPException(status_code=400, detail=results.get("error", "File analysis failed"))
        
        return {
            "status": "success",
            "message": "File-based LCA analysis completed successfully",
            "analysis_id": results["analysis_id"],
            "uploaded_file": saved_filename,
            "workflow_status": "completed",
            "ingested_data_summary": {
                "records_processed": results.get("ingested_data", {}).get("records_count", 0),
                "data_quality_score": results.get("ingested_data", {}).get("data_quality", {}).get("completeness", 0)
            },
            "results_summary": results["summary"],
            "report_files": results["summary"]["report_summary"]["report_files"],
            "visualizations": results.get("report_generation", {}).get("output_files", {}),
            "timestamp": results["workflow_timestamp"]
        }
        
    except Exception as e:
        logger.error(f"Error in file-based analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/lca/supported-metals")
async def get_supported_metals():
    """Get list of supported metal types and configuration options"""
    return {
        "supported_metals": [
            {"id": "steel", "name": "Steel", "description": "Carbon and stainless steel"},
            {"id": "aluminum", "name": "Aluminum", "description": "Primary and secondary aluminum"},
            {"id": "copper", "name": "Copper", "description": "Refined copper and alloys"},
            {"id": "zinc", "name": "Zinc", "description": "Primary zinc production"},
            {"id": "lead", "name": "Lead", "description": "Primary and secondary lead"},
            {"id": "nickel", "name": "Nickel", "description": "Class I nickel"},
            {"id": "tin", "name": "Tin", "description": "Primary tin smelting"},
            {"id": "magnesium", "name": "Magnesium", "description": "Primary magnesium"},
            {"id": "titanium", "name": "Titanium", "description": "Titanium metal production"}
        ],
        "regions": [
            {"id": "US_average", "name": "United States (Average)"},
            {"id": "EU_average", "name": "European Union (Average)"},
            {"id": "China", "name": "China"},
            {"id": "Global_average", "name": "Global Average"}
        ],
        "study_types": [
            {
                "id": "internal_decision_support",
                "name": "Internal Decision Support",
                "description": "For internal business decisions",
                "critical_review_required": False
            },
            {
                "id": "comparative_assertion",
                "name": "Comparative Assertion",
                "description": "Public comparative claims",
                "critical_review_required": True
            },
            {
                "id": "public_communication",
                "name": "Public Communication",
                "description": "Public disclosure of results",
                "critical_review_required": True
            }
        ],
        "report_formats": [
            {"id": "pdf", "name": "PDF Report"},
            {"id": "html", "name": "HTML Report"},
            {"id": "json", "name": "JSON Data"},
            {"id": "all", "name": "All Formats"}
        ],
        "file_formats": [
            {"extension": ".xlsx", "description": "Excel 2007+ format"},
            {"extension": ".xls", "description": "Excel 97-2003 format"},
            {"extension": ".csv", "description": "Comma-separated values"}
        ]
    }

@app.get("/api/v1/reports/{analysis_id}")
async def get_analysis_report(analysis_id: str):
    """Retrieve specific analysis report"""
    try:
        results_dir = Path("./results")
        report_file = results_dir / f"{analysis_id}_complete_results.json"
        
        if not report_file.exists():
            raise HTTPException(status_code=404, detail="Analysis report not found")
        
        import json
        with open(report_file, 'r') as f:
            report_data = json.load(f)
        
        return {
            "status": "success",
            "analysis_id": analysis_id,
            "report_data": report_data,
            "retrieved_at": datetime.now().isoformat()
        }
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Report not found: {analysis_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving report: {str(e)}")

@app.get("/api/v1/reports/{analysis_id}/download/{file_type}")
async def download_report_file(analysis_id: str, file_type: str):
    """Download specific report file"""
    try:
        # This would implement file download logic
        # You'd need to track where files are saved and provide download links
        reports_dir = Path("./reports")
        
        # Look for the file
        pattern = f"*{analysis_id}*.{file_type}"
        matching_files = list(reports_dir.glob(pattern))
        
        if not matching_files:
            raise HTTPException(status_code=404, detail=f"Report file not found: {file_type}")
        
        file_path = matching_files[0]
        return FileResponse(
            path=file_path,
            filename=f"lca_report_{analysis_id}.{file_type}",
            media_type='application/octet-stream'
        )
        
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"File not found: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "api:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )