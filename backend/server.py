"""
LCA Analysis Backend Server
Streamlined for Frontend Integration
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import uvicorn
import logging
import json
from datetime import datetime
import tempfile
import os
import pandas as pd

from main import LCASystem

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="LCA Analysis Backend Server",
    description="Backend server for Life Cycle Assessment with frontend integration",
    version="1.0.0"
)

# CORS middleware - Configure for your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "*"  # Remove this in production and specify your frontend domain
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Initialize LCA System
lca_system = LCASystem()

# Pydantic Models for Frontend Communication
class MaterialInput(BaseModel):
    material_type: str = Field(..., description="Type of material (aluminum, steel, copper, etc.)")
    mass_kg: float = Field(..., gt=0, description="Mass of material in kg")

class EnergyInput(BaseModel):
    virgin_energy_kwh_per_kg: float = Field(..., description="Energy for virgin material (kWh/kg)")
    recycled_energy_kwh_per_kg: float = Field(..., description="Energy for recycled material (kWh/kg)")

class EmissionInput(BaseModel):
    virgin_direct_emissions: float = Field(..., description="Direct emissions for virgin material (kg CO2e/kg)")
    recycled_direct_emissions: float = Field(..., description="Direct emissions for recycled material (kg CO2e/kg)")

class GridInput(BaseModel):
    coal_percent: float = Field(0, ge=0, le=100, description="Coal percentage in grid")
    gas_percent: float = Field(0, ge=0, le=100, description="Gas percentage in grid")
    oil_percent: float = Field(0, ge=0, le=100, description="Oil percentage in grid")
    nuclear_percent: float = Field(0, ge=0, le=100, description="Nuclear percentage in grid")
    hydro_percent: float = Field(0, ge=0, le=100, description="Hydro percentage in grid")
    wind_percent: float = Field(0, ge=0, le=100, description="Wind percentage in grid")
    solar_percent: float = Field(0, ge=0, le=100, description="Solar percentage in grid")
    other_renewable_percent: float = Field(0, ge=0, le=100, description="Other renewable percentage")

class TransportInput(BaseModel):
    transport_mode: str = Field(..., description="Transport mode (truck, ship, rail, air)")
    distance_km: float = Field(..., ge=0, description="Transport distance in km")
    weight_tonnes: float = Field(..., ge=0, description="Transport weight in tonnes")

class RecyclingInput(BaseModel):
    recycled_content_percent: float = Field(0, ge=0, le=100, description="Current recycled content %")
    collection_rate_percent: float = Field(75, ge=0, le=100, description="Collection rate for recycling %")
    recycling_efficiency_percent: float = Field(90, ge=0, le=100, description="Recycling efficiency %")

class LCAAnalysisRequest(BaseModel):
    # Core inputs from frontend
    material: MaterialInput
    energy: EnergyInput
    emissions: EmissionInput
    grid_composition: GridInput
    transport: TransportInput
    recycling: RecyclingInput
    
    # Analysis configuration
    analysis_type: str = Field("cradle_to_gate", description="Analysis scope")
    report_format: str = Field("json", description="Output format")

class QuickAnalysisRequest(BaseModel):
    material_type: str = Field(..., description="Material type")
    mass_kg: float = Field(..., gt=0, description="Mass in kg")
    recycled_content_percent: float = Field(30, ge=0, le=100, description="Recycled content %")
    transport_distance_km: float = Field(100, ge=0, description="Transport distance")
    renewable_energy_percent: float = Field(30, ge=0, le=100, description="Renewable energy %")

# API Endpoints
@app.get("/")
async def root():
    """Health check and API info"""
    return {
        "status": "active",
        "message": "LCA Analysis Backend Server",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "health": "/health",
            "quick_analysis": "/analyze/quick",
            "comprehensive_analysis": "/analyze/comprehensive",
            "file_analysis": "/analyze/file",
            "material_options": "/options/materials",
            "transport_options": "/options/transport"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "lca_system": "initialized"
    }

@app.post("/analyze/quick")
async def quick_analysis(request: QuickAnalysisRequest):
    """
    Quick LCA analysis with simplified inputs
    Frontend sends: material type, mass, recycled content %, transport distance, renewable %
    Backend returns: carbon footprint, sustainability metrics
    """
    try:
        logger.info(f"Quick analysis for {request.material_type} - {request.mass_kg}kg")
        
        # Map transport mode based on distance (simple logic)
        transport_mode = "truck" if request.transport_distance_km <= 500 else "ship"
        
        # Create analysis scenario with defaults
        scenario_data = {
            "material_type": request.material_type.lower(),
            "mass_kg": request.mass_kg,
            "energy_intensity": {
                "virgin_process_kwh_per_kg": get_default_energy(request.material_type, "virgin"),
                "recycled_process_kwh_per_kg": get_default_energy(request.material_type, "recycled")
            },
            "direct_emissions": {
                "virgin_kg_co2e_per_kg": get_default_emissions(request.material_type, "virgin"),
                "recycled_kg_co2e_per_kg": get_default_emissions(request.material_type, "recycled")
            },
            "grid_composition": create_grid_from_renewable_percent(request.renewable_energy_percent),
            "transport": {
                "mode": transport_mode,
                "distance_km": request.transport_distance_km,
                "weight_t": request.mass_kg / 1000,
                "emission_factor_kg_co2e_per_tkm": get_transport_ef(transport_mode)
            },
            "material_emission_factors": {
                "virgin_kg_co2e_per_kg": get_material_ef(request.material_type, "virgin"),
                "secondary_kg_co2e_per_kg": get_material_ef(request.material_type, "secondary")
            },
            "recycling": {
                "collection_rate_pct": 75,
                "recycling_efficiency_pct": 90,
                "secondary_content_existing_pct": request.recycled_content_percent
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
        
        # Extract key metrics for frontend
        summary = results.get("summary", {})
        lca_summary = summary.get("lca_summary", {})
        
        return {
            "success": True,
            "analysis_id": results.get("analysis_id"),
            "results": {
                "carbon_footprint_kg_co2e": round(lca_summary.get("total_carbon_footprint_kg_co2_eq", 0), 3),
                "carbon_intensity_per_kg": round(lca_summary.get("carbon_intensity_per_kg", 0), 3),
                "circularity_index": round(lca_summary.get("circularity_index", 0), 2),
                "sustainability_score": round(lca_summary.get("sustainability_score", 0), 1),
                "energy_consumption_kwh": round(lca_summary.get("total_energy_consumption_kwh", 0), 2),
                "recycling_benefit_kg_co2e": round(lca_summary.get("recycling_benefit", 0), 3)
            },
            "breakdown": {
                "material_emissions": round(lca_summary.get("material_emissions", 0), 3),
                "energy_emissions": round(lca_summary.get("energy_emissions", 0), 3),
                "transport_emissions": round(lca_summary.get("transport_emissions", 0), 3),
                "process_emissions": round(lca_summary.get("process_emissions", 0), 3)
            },
            "recommendations": summary.get("recommendations", []),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in quick analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/analyze/comprehensive")
async def comprehensive_analysis(request: LCAAnalysisRequest):
    """
    Comprehensive LCA analysis with all user inputs
    Frontend sends: detailed material, energy, emissions, grid, transport, recycling data
    Backend returns: complete analysis results
    """
    try:
        logger.info(f"Comprehensive analysis for {request.material.material_type}")
        
        # Build scenario from frontend inputs
        scenario_data = {
            "material_type": request.material.material_type.lower(),
            "mass_kg": request.material.mass_kg,
            "energy_intensity": {
                "virgin_process_kwh_per_kg": request.energy.virgin_energy_kwh_per_kg,
                "recycled_process_kwh_per_kg": request.energy.recycled_energy_kwh_per_kg
            },
            "direct_emissions": {
                "virgin_kg_co2e_per_kg": request.emissions.virgin_direct_emissions,
                "recycled_kg_co2e_per_kg": request.emissions.recycled_direct_emissions
            },
            "grid_composition": {
                "coal_pct": request.grid_composition.coal_percent,
                "gas_pct": request.grid_composition.gas_percent,
                "oil_pct": request.grid_composition.oil_percent,
                "nuclear_pct": request.grid_composition.nuclear_percent,
                "hydro_pct": request.grid_composition.hydro_percent,
                "wind_pct": request.grid_composition.wind_percent,
                "solar_pct": request.grid_composition.solar_percent,
                "other_pct": request.grid_composition.other_renewable_percent
            },
            "transport": {
                "mode": request.transport.transport_mode.lower(),
                "distance_km": request.transport.distance_km,
                "weight_t": request.transport.weight_tonnes,
                "emission_factor_kg_co2e_per_tkm": get_transport_ef(request.transport.transport_mode)
            },
            "material_emission_factors": {
                "virgin_kg_co2e_per_kg": get_material_ef(request.material.material_type, "virgin"),
                "secondary_kg_co2e_per_kg": get_material_ef(request.material.material_type, "secondary")
            },
            "recycling": {
                "collection_rate_pct": request.recycling.collection_rate_percent,
                "recycling_efficiency_pct": request.recycling.recycling_efficiency_percent,
                "secondary_content_existing_pct": request.recycling.recycled_content_percent
            },
            "functional_unit": f"1 kg of {request.material.material_type}",
            "scenario_id": "comprehensive_analysis"
        }
        
        input_data = {
            "scenarios": [scenario_data],
            "study_type": "internal_decision_support",
            "report_type": "technical",
            "format_type": request.report_format,
            "analysis_type": request.analysis_type
        }
        
        results = lca_system.run_complete_analysis(input_data)
        
        if not results.get("success"):
            raise HTTPException(status_code=400, detail=results.get("error", "Analysis failed"))
        
        # Return comprehensive results
        return {
            "success": True,
            "analysis_id": results.get("analysis_id"),
            "results": results.get("summary", {}),
            "detailed_results": results.get("lca_results", {}),
            "compliance_check": results.get("compliance_summary", {}),
            "recommendations": results.get("summary", {}).get("recommendations", []),
            "charts_available": bool(results.get("chart_paths")),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in comprehensive analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/analyze/file")
async def file_analysis(
    file: UploadFile = File(...),
    analysis_type: str = Form("cradle_to_gate")
):
    """
    File-based analysis for bulk data
    Frontend sends: Excel/CSV file with LCA data
    Backend returns: batch analysis results
    """
    try:
        # Validate file
        if not file.filename.lower().endswith(('.xlsx', '.xls', '.csv')):
            raise HTTPException(status_code=400, detail="Only Excel (.xlsx, .xls) and CSV files are supported")
        
        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Prepare input data
            input_data = {
                "file_path": temp_file_path,
                "file_type": "excel" if file.filename.lower().endswith(('.xlsx', '.xls')) else "csv",
                "analysis_type": analysis_type,
                "study_type": "internal_decision_support",
                "report_type": "technical",
                "format_type": "json"
            }
            
            results = lca_system.run_complete_analysis(input_data)
            
            if not results.get("success"):
                raise HTTPException(status_code=400, detail=results.get("error", "File analysis failed"))
            
            return {
                "success": True,
                "analysis_id": results.get("analysis_id"),
                "file_processed": file.filename,
                "scenarios_analyzed": len(results.get("lca_results", {}).get("scenarios", [])),
                "results": results.get("summary", {}),
                "timestamp": datetime.now().isoformat()
            }
            
        finally:
            # Clean up temp file
            os.unlink(temp_file_path)
            
    except Exception as e:
        logger.error(f"Error in file analysis: {e}")
        raise HTTPException(status_code=500, detail=f"File analysis failed: {str(e)}")

@app.get("/options/materials")
async def get_material_options():
    """Get available material types and their default values"""
    return {
        "materials": [
            {
                "id": "aluminum",
                "name": "Aluminum",
                "default_virgin_energy": 15.0,
                "default_recycled_energy": 3.0,
                "default_virgin_emissions": 11.5,
                "default_recycled_emissions": 0.64
            },
            {
                "id": "steel",
                "name": "Steel",
                "default_virgin_energy": 6.0,
                "default_recycled_energy": 2.5,
                "default_virgin_emissions": 2.3,
                "default_recycled_emissions": 0.5
            },
            {
                "id": "copper",
                "name": "Copper",
                "default_virgin_energy": 8.0,
                "default_recycled_energy": 2.0,
                "default_virgin_emissions": 3.2,
                "default_recycled_emissions": 0.8
            },
            {
                "id": "zinc",
                "name": "Zinc",
                "default_virgin_energy": 7.5,
                "default_recycled_energy": 2.2,
                "default_virgin_emissions": 3.5,
                "default_recycled_emissions": 0.9
            }
        ]
    }

@app.get("/options/transport")
async def get_transport_options():
    """Get available transport modes and their emission factors"""
    return {
        "transport_modes": [
            {
                "id": "truck",
                "name": "Truck",
                "emission_factor": 0.062,
                "unit": "kg CO2e/tonne-km"
            },
            {
                "id": "ship",
                "name": "Ship",
                "emission_factor": 0.015,
                "unit": "kg CO2e/tonne-km"
            },
            {
                "id": "rail",
                "name": "Rail",
                "emission_factor": 0.022,
                "unit": "kg CO2e/tonne-km"
            },
            {
                "id": "air",
                "name": "Air Freight",
                "emission_factor": 0.602,
                "unit": "kg CO2e/tonne-km"
            }
        ]
    }

# Helper functions
def get_default_energy(material_type: str, process_type: str) -> float:
    """Get default energy values based on material and process type"""
    defaults = {
        "aluminum": {"virgin": 15.0, "recycled": 3.0},
        "steel": {"virgin": 6.0, "recycled": 2.5},
        "copper": {"virgin": 8.0, "recycled": 2.0},
        "zinc": {"virgin": 7.5, "recycled": 2.2}
    }
    return defaults.get(material_type.lower(), {"virgin": 10.0, "recycled": 3.0})[process_type]

def get_default_emissions(material_type: str, process_type: str) -> float:
    """Get default emission values based on material and process type"""
    defaults = {
        "aluminum": {"virgin": 2.0, "recycled": 0.5},
        "steel": {"virgin": 1.5, "recycled": 0.3},
        "copper": {"virgin": 1.8, "recycled": 0.4},
        "zinc": {"virgin": 2.2, "recycled": 0.6}
    }
    return defaults.get(material_type.lower(), {"virgin": 2.0, "recycled": 0.5})[process_type]

def get_material_ef(material_type: str, ef_type: str) -> float:
    """Get material emission factors"""
    defaults = {
        "aluminum": {"virgin": 11.5, "secondary": 0.64},
        "steel": {"virgin": 2.3, "secondary": 0.5},
        "copper": {"virgin": 3.2, "secondary": 0.8},
        "zinc": {"virgin": 3.5, "secondary": 0.9}
    }
    return defaults.get(material_type.lower(), {"virgin": 5.0, "secondary": 1.0})[ef_type]

def get_transport_ef(transport_mode: str) -> float:
    """Get transport emission factors"""
    efs = {
        "truck": 0.062,
        "ship": 0.015,
        "rail": 0.022,
        "air": 0.602
    }
    return efs.get(transport_mode.lower(), 0.062)

def create_grid_from_renewable_percent(renewable_percent: float) -> Dict[str, float]:
    """Create grid composition from renewable percentage"""
    remaining = 100 - renewable_percent
    return {
        "coal_pct": remaining * 0.4,
        "gas_pct": remaining * 0.5,
        "oil_pct": remaining * 0.1,
        "nuclear_pct": 0,
        "hydro_pct": renewable_percent * 0.3,
        "wind_pct": renewable_percent * 0.4,
        "solar_pct": renewable_percent * 0.2,
        "other_pct": renewable_percent * 0.1
    }

if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
