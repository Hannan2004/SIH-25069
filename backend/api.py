"""
FastAPI REST API for LCA Analysis System
Enhanced for comprehensive LCA input parameters
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

from main import LCASystem, run_quick_lca_analysis, run_file_analysis

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Comprehensive LCA Analysis System API",
    description="Enhanced Life Cycle Assessment API with comprehensive material, energy, transport, and recycling parameters",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://your-nextjs-domain.com"
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

# Enhanced Pydantic models for comprehensive LCA data
class EnergyIntensity(BaseModel):
    virgin_process_kwh_per_kg: float = Field(..., description="Energy intensity of virgin process (kWh/kg)")
    recycled_process_kwh_per_kg: float = Field(..., description="Energy intensity of recycled process (kWh/kg)")

class DirectEmissions(BaseModel):
    virgin_kg_co2e_per_kg: float = Field(..., description="Direct process emissions for virgin material (kg CO2e/kg)")
    recycled_kg_co2e_per_kg: float = Field(..., description="Direct process emissions for recycled material (kg CO2e/kg)")

class GridComposition(BaseModel):
    coal_pct: float = Field(0, ge=0, le=100, description="% share of coal in grid")
    gas_pct: float = Field(0, ge=0, le=100, description="% share of gas in grid")
    oil_pct: float = Field(0, ge=0, le=100, description="% share of oil in grid")
    nuclear_pct: float = Field(0, ge=0, le=100, description="% share of nuclear in grid")
    hydro_pct: float = Field(0, ge=0, le=100, description="% share of hydro in grid")
    wind_pct: float = Field(0, ge=0, le=100, description="% share of wind in grid")
    solar_pct: float = Field(0, ge=0, le=100, description="% share of solar in grid")
    other_pct: float = Field(0, ge=0, le=100, description="% share of other renewables in grid")

class Transport(BaseModel):
    mode: str = Field(..., description="Mode of transport (truck, ship, rail, air)")
    distance_km: float = Field(..., ge=0, description="Distance transported (km)")
    weight_t: float = Field(..., ge=0, description="Shipment weight (tonne)")
    emission_factor_kg_co2e_per_tkm: float = Field(..., description="EF of transport mode (kg CO2e/tkm)")

class MaterialEmissionFactors(BaseModel):
    virgin_kg_co2e_per_kg: float = Field(..., description="Virgin material EF (kg CO2e/kg)")
    secondary_kg_co2e_per_kg: float = Field(..., description="Secondary material EF (kg CO2e/kg)")

class RecyclingParameters(BaseModel):
    collection_rate_pct: float = Field(..., ge=0, le=100, description="Collection rate for recycling (%)")
    recycling_efficiency_pct: float = Field(..., ge=0, le=100, description="Efficiency of recycling process (%)")
    secondary_content_existing_pct: float = Field(..., ge=0, le=100, description="Already recycled content in product (%)")

class ComprehensiveLCARequest(BaseModel):
    material_type: str = Field(..., description="Type of material")
    mass_kg: float = Field(..., gt=0, description="Mass of product being studied (kg)")
    energy_intensity: EnergyIntensity
    direct_emissions: DirectEmissions
    grid_composition: GridComposition
    transport: Transport
    material_emission_factors: MaterialEmissionFactors
    recycling: RecyclingParameters
    analysis_type: str = Field("cradle_to_gate", description="Analysis type")
    study_type: str = Field("internal_decision_support", description="Study type for compliance")
    report_format: str = Field("pdf", description="Report format")

class QuickLCARequest(BaseModel):
    material_type: str
    mass_kg: float = Field(..., gt=0)
    recycled_content_pct: float = Field(30, ge=0, le=100)
    transport_distance_km: float = Field(100, ge=0)
    grid_renewable_pct: float = Field(30, ge=0, le=100)

# API Endpoints
@app.get("/")
async def root():
    """Root endpoint with enhanced API information"""
    return {
        "message": "Comprehensive LCA Analysis System API v2.0",
        "version": "2.0.0",
        "status": "active",
        "timestamp": datetime.now().isoformat(),
        "features": [
            "Comprehensive LCA analysis with energy, emissions, transport, and recycling parameters",
            "File upload support (Excel/CSV)",
            "ISO compliance checking",
            "AI-enhanced insights and recommendations",
            "Circularity metrics and circular economy assessment",
            "Multiple report formats with visualizations",
            "LangGraph workflow orchestration"
        ],
        "data_requirements": {
            "required_columns": [
                "Material", "Mass_kg", "EI_process", "EI_recycled",
                "EF_direct", "EF_direct_recycled", "Transport_mode",
                "Transport_distance_km", "Transport_weight_t", "Transport_EF",
                "Virgin_EF", "Secondary_EF", "Collection_rate",
                "Recycling_efficiency", "Secondary_content_existing"
            ],
            "grid_composition_columns": [
                "Coal_pct", "Gas_pct", "Oil_pct", "Nuclear_pct",
                "Hydro_pct", "Wind_pct", "Solar_pct", "Other_pct"
            ]
        },
        "endpoints": {
            "comprehensive_analysis": "/api/v2/lca/comprehensive",
            "file_analysis": "/api/v2/lca/file-upload",
            "quick_analysis": "/api/v2/lca/quick",
            "supported_parameters": "/api/v2/lca/parameters"
        }
    }

@app.post("/api/v2/lca/comprehensive")
async def comprehensive_lca_analysis(request: ComprehensiveLCARequest):
    """Run comprehensive LCA analysis with all parameters"""
    try:
        logger.info(f"Starting comprehensive LCA analysis for {request.material_type}")
        
        # Convert request to internal format
        scenario_data = {
            "material_type": request.material_type.lower(),
            "mass_kg": request.mass_kg,
            "energy_intensity": {
                "virgin_process_kwh_per_kg": request.energy_intensity.virgin_process_kwh_per_kg,
                "recycled_process_kwh_per_kg": request.energy_intensity.recycled_process_kwh_per_kg
            },
            "direct_emissions": {
                "virgin_kg_co2e_per_kg": request.direct_emissions.virgin_kg_co2e_per_kg,
                "recycled_kg_co2e_per_kg": request.direct_emissions.recycled_kg_co2e_per_kg
            },
            "grid_composition": {
                "coal_pct": request.grid_composition.coal_pct,
                "gas_pct": request.grid_composition.gas_pct,
                "oil_pct": request.grid_composition.oil_pct,
                "nuclear_pct": request.grid_composition.nuclear_pct,
                "hydro_pct": request.grid_composition.hydro_pct,
                "wind_pct": request.grid_composition.wind_pct,
                "solar_pct": request.grid_composition.solar_pct,
                "other_pct": request.grid_composition.other_pct
            },
            "transport": {
                "mode": request.transport.mode.lower(),
                "distance_km": request.transport.distance_km,
                "weight_t": request.transport.weight_t,
                "emission_factor_kg_co2e_per_tkm": request.transport.emission_factor_kg_co2e_per_tkm
            },
            "material_emission_factors": {
                "virgin_kg_co2e_per_kg": request.material_emission_factors.virgin_kg_co2e_per_kg,
                "secondary_kg_co2e_per_kg": request.material_emission_factors.secondary_kg_co2e_per_kg
            },
            "recycling": {
                "collection_rate_pct": request.recycling.collection_rate_pct,
                "recycling_efficiency_pct": request.recycling.recycling_efficiency_pct,
                "secondary_content_existing_pct": request.recycling.secondary_content_existing_pct
            },
            "functional_unit": f"1 kg of {request.material_type}",
            "scenario_id": "api_request"
        }
        
        input_data = {
            "scenarios": [scenario_data],
            "study_type": request.study_type,
            "report_type": "technical",
            "format_type": request.report_format,
            "analysis_type": request.analysis_type
        }
        
        results = lca_system.run_complete_analysis(input_data)
        
        if not results.get("success"):
            raise HTTPException(status_code=400, detail=results.get("error", "Analysis failed"))
        
        return {
            "status": "success",
            "message": "Comprehensive LCA analysis completed successfully",
            "analysis_id": results["analysis_id"],
            "results": results,
            "summary": results.get("summary", {}),
            "timestamp": results["workflow_timestamp"]
        }
        
    except Exception as e:
        logger.error(f"Error in comprehensive LCA analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v2/lca/quick")
async def quick_lca_analysis(request: QuickLCARequest):
    """Run quick LCA analysis with simplified parameters"""
    try:
        logger.info(f"Starting quick LCA analysis for {request.material_type}")
        
        # Create simplified scenario with default values
        scenario_data = {
            "material_type": request.material_type.lower(),
            "mass_kg": request.mass_kg,
            "energy_intensity": {
                "virgin_process_kwh_per_kg": 15.0,  # Default for aluminum
                "recycled_process_kwh_per_kg": 3.0   # Default for recycled aluminum
            },
            "direct_emissions": {
                "virgin_kg_co2e_per_kg": 2.0,
                "recycled_kg_co2e_per_kg": 0.5
            },
            "grid_composition": {
                "coal_pct": 30,
                "gas_pct": 40,
                "oil_pct": 5,
                "nuclear_pct": 10,
                "hydro_pct": 5,
                "wind_pct": request.grid_renewable_pct * 0.5,
                "solar_pct": request.grid_renewable_pct * 0.3,
                "other_pct": request.grid_renewable_pct * 0.2
            },
            "transport": {
                "mode": "truck",
                "distance_km": request.transport_distance_km,
                "weight_t": request.mass_kg / 1000,
                "emission_factor_kg_co2e_per_tkm": 0.062
            },
            "material_emission_factors": {
                "virgin_kg_co2e_per_kg": 11.5,  # Default for aluminum
                "secondary_kg_co2e_per_kg": 0.64
            },
            "recycling": {
                "collection_rate_pct": 75,
                "recycling_efficiency_pct": 90,
                "secondary_content_existing_pct": request.recycled_content_pct
            },
            "functional_unit": f"1 kg of {request.material_type}",
            "scenario_id": "quick_analysis"
        }
        
        input_data = {
            "scenarios": [scenario_data],
            "study_type": "internal_decision_support",
            "report_type": "technical",
            "format_type": "json",
            "analysis_type": "cradle_to_gate"
        }
        
        results = lca_system.run_complete_analysis(input_data)
        
        if not results.get("success"):
            raise HTTPException(status_code=400, detail=results.get("error", "Analysis failed"))
        
        # Return simplified response
        summary = results.get("summary", {})
        lca_summary = summary.get("lca_summary", {})
        
        return {
            "status": "success",
            "message": "Quick LCA analysis completed",
            "analysis_id": results["analysis_id"],
            "carbon_footprint_kg_co2e": lca_summary.get("total_carbon_footprint_kg_co2_eq", 0),
            "carbon_intensity_per_kg": lca_summary.get("carbon_intensity_per_kg", 0),
            "circularity_index": lca_summary.get("circularity_index", 0),
            "sustainability_score": lca_summary.get("sustainability_score", 0),
            "timestamp": results["workflow_timestamp"]
        }
        
    except Exception as e:
        logger.error(f"Error in quick LCA analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v2/lca/file-upload")
async def file_based_analysis(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    analysis_type: str = Form("cradle_to_gate"),
    study_type: str = Form("internal_decision_support"),
    report_format: str = Form("all")
):
    """Upload comprehensive LCA data file and run analysis"""
    try:
        # Validate file type
        allowed_types = [
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-excel",
            "text/csv",
            "application/csv"
        ]
        
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file.content_type}"
            )
        
        # Save uploaded file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = Path(file.filename).suffix
        saved_filename = f"lca_data_{timestamp}{file_extension}"
        file_path = UPLOAD_DIR / saved_filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"File uploaded successfully: {saved_filename}")
        
        # Prepare input data for analysis
        input_data = {
            "file_path": str(file_path),
            "file_type": "excel" if file_extension in [".xlsx", ".xls"] else "csv",
            "analysis_type": analysis_type,
            "study_type": study_type,
            "report_type": "technical",
            "format_type": report_format
        }
        
        # Run analysis
        results = lca_system.run_complete_analysis(input_data)
        
        # Clean up uploaded file
        background_tasks.add_task(os.remove, file_path)
        
        if not results.get("success"):
            raise HTTPException(status_code=400, detail=results.get("error", "File analysis failed"))
        
        return {
            "status": "success",
            "message": "File-based LCA analysis completed successfully",
            "analysis_id": results["analysis_id"],
            "uploaded_file": saved_filename,
            "results_summary": results.get("summary", {}),
            "timestamp": results["workflow_timestamp"]
        }
        
    except Exception as e:
        logger.error(f"Error in file-based analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v2/lca/parameters")
async def get_supported_parameters():
    """Get comprehensive list of supported parameters and options"""
    return {
        "materials": [
            {"id": "aluminum", "name": "Aluminum", "typical_virgin_ef": 11.5},
            {"id": "steel", "name": "Steel", "typical_virgin_ef": 2.3},
            {"id": "copper", "name": "Copper", "typical_virgin_ef": 3.2},
            {"id": "zinc", "name": "Zinc", "typical_virgin_ef": 3.5},
            {"id": "lead", "name": "Lead", "typical_virgin_ef": 1.3},
            {"id": "nickel", "name": "Nickel", "typical_virgin_ef": 12.8},
            {"id": "tin", "name": "Tin", "typical_virgin_ef": 7.1},
            {"id": "magnesium", "name": "Magnesium", "typical_virgin_ef": 24.7},
            {"id": "titanium", "name": "Titanium", "typical_virgin_ef": 45.2}
        ],
        "transport_modes": [
            {"id": "truck", "name": "Truck", "typical_ef_kg_co2e_per_tkm": 0.062},
            {"id": "ship", "name": "Ship", "typical_ef_kg_co2e_per_tkm": 0.015},
            {"id": "rail", "name": "Rail", "typical_ef_kg_co2e_per_tkm": 0.022},
            {"id": "air", "name": "Air", "typical_ef_kg_co2e_per_tkm": 0.602}
        ],
        "grid_emission_factors": {
            "coal": 0.820,
            "gas": 0.490,
            "oil": 0.750,
            "nuclear": 0.012,
            "hydro": 0.024,
            "wind": 0.011,
            "solar": 0.041,
            "other": 0.200
        },
        "analysis_types": [
            {"id": "cradle_to_gate", "name": "Cradle-to-Gate", "description": "Production to factory gate"},
            {"id": "cradle_to_grave", "name": "Cradle-to-Grave", "description": "Full life cycle including EOL"},
            {"id": "gate_to_gate", "name": "Gate-to-Gate", "description": "Manufacturing process only"}
        ],
        "study_types": [
            {"id": "internal_decision_support", "name": "Internal Decision Support"},
            {"id": "comparative_assertion", "name": "Comparative Assertion"},
            {"id": "public_communication", "name": "Public Communication"}
        ],
        "required_csv_columns": [
            "Material", "Mass_kg", "EI_process", "EI_recycled",
            "EF_direct", "EF_direct_recycled", "Coal_pct", "Gas_pct", "Oil_pct",
            "Nuclear_pct", "Hydro_pct", "Wind_pct", "Solar_pct", "Other_pct",
            "Transport_mode", "Transport_distance_km", "Transport_weight_t", "Transport_EF",
            "Virgin_EF", "Secondary_EF", "Collection_rate", "Recycling_efficiency",
            "Secondary_content_existing"
        ]
    }

if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )