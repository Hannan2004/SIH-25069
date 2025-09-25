# LCA Backend API Documentation for Frontend Integration

## Server Details
- **Base URL**: `http://localhost:8000`
- **Protocol**: HTTP/HTTPS
- **Format**: JSON
- **CORS**: Enabled for localhost:3000, localhost:3001

## Available Endpoints

### 1. Health Check
```
GET /health
```
**Response:**
```json
{
    "status": "healthy",
    "timestamp": "2025-09-26T10:30:00",
    "lca_system": "initialized"
}
```

---

### 2. Quick Analysis (Recommended for simple UI)
```
POST /analyze/quick
```

**Input JSON:**
```json
{
    "material_type": "aluminum",
    "mass_kg": 100,
    "recycled_content_percent": 30,
    "transport_distance_km": 500,
    "renewable_energy_percent": 40
}
```

**Input Fields:**
- `material_type`: String - "aluminum", "steel", "copper", "zinc"
- `mass_kg`: Number (positive) - Mass of material in kilograms
- `recycled_content_percent`: Number (0-100) - Current recycled content percentage
- `transport_distance_km`: Number (positive) - Transport distance in kilometers
- `renewable_energy_percent`: Number (0-100) - Renewable energy percentage in grid

**Output JSON:**
```json
{
    "success": true,
    "analysis_id": "quick_20250926_103000",
    "results": {
        "carbon_footprint_kg_co2e": 156.789,
        "carbon_intensity_per_kg": 1.568,
        "circularity_index": 0.75,
        "sustainability_score": 7.2,
        "energy_consumption_kwh": 1250.50,
        "recycling_benefit_kg_co2e": 45.123
    },
    "breakdown": {
        "material_emissions": 89.456,
        "energy_emissions": 45.123,
        "transport_emissions": 12.890,
        "process_emissions": 9.320
    },
    "recommendations": [
        "Increase recycled content to 50% to reduce emissions by 15%",
        "Consider rail transport for distances > 300km"
    ],
    "timestamp": "2025-09-26T10:30:00"
}
```

---

### 3. Comprehensive Analysis (For advanced users)
```
POST /analyze/comprehensive
```

**Input JSON:**
```json
{
    "material": {
        "material_type": "aluminum",
        "mass_kg": 100
    },
    "energy": {
        "virgin_energy_kwh_per_kg": 15.0,
        "recycled_energy_kwh_per_kg": 3.0
    },
    "emissions": {
        "virgin_direct_emissions": 2.0,
        "recycled_direct_emissions": 0.5
    },
    "grid_composition": {
        "coal_percent": 30,
        "gas_percent": 40,
        "oil_percent": 5,
        "nuclear_percent": 10,
        "hydro_percent": 5,
        "wind_percent": 7,
        "solar_percent": 3,
        "other_renewable_percent": 0
    },
    "transport": {
        "transport_mode": "truck",
        "distance_km": 500,
        "weight_tonnes": 0.1
    },
    "recycling": {
        "recycled_content_percent": 30,
        "collection_rate_percent": 75,
        "recycling_efficiency_percent": 90
    },
    "analysis_type": "cradle_to_gate",
    "report_format": "json"
}
```

**Input Validation:**
- All percentages: 0-100
- All masses/distances: positive numbers
- Transport modes: "truck", "ship", "rail", "air"
- Analysis types: "cradle_to_gate", "cradle_to_grave", "gate_to_gate"
- Grid composition should sum to ~100%

**Output:** Similar to quick analysis but with more detailed breakdown

---

### 4. File Upload Analysis
```
POST /analyze/file
```

**Input:** Form data
- `file`: Excel (.xlsx, .xls) or CSV file
- `analysis_type`: String (optional, default: "cradle_to_gate")

**Required CSV/Excel Columns:**
```
Material, Mass_kg, EI_process, EI_recycled, EF_direct, EF_direct_recycled,
Coal_pct, Gas_pct, Oil_pct, Nuclear_pct, Hydro_pct, Wind_pct, Solar_pct, Other_pct,
Transport_mode, Transport_distance_km, Transport_weight_t, Transport_EF,
Virgin_EF, Secondary_EF, Collection_rate, Recycling_efficiency, Secondary_content_existing
```

---

### 5. Get Available Options
```
GET /options/materials
```
**Response:** List of supported materials with default values

```
GET /options/transport
```
**Response:** List of transport modes with emission factors

---

## Frontend Integration Guidelines

### 1. Form Input Fields Needed

**Quick Analysis Form:**
```javascript
const quickAnalysisForm = {
    materialType: 'select', // dropdown with options from /options/materials
    massKg: 'number', // input field, min: 0.1, max: 10000
    recycledContentPercent: 'range', // slider, 0-100, default: 30
    transportDistanceKm: 'number', // input field, min: 1, max: 50000
    renewableEnergyPercent: 'range' // slider, 0-100, default: 30
};
```

**Comprehensive Analysis Form:** (For advanced mode)
```javascript
const comprehensiveForm = {
    // Material Section
    materialType: 'select',
    massKg: 'number',
    
    // Energy Section
    virginEnergyKwhPerKg: 'number',
    recycledEnergyKwhPerKg: 'number',
    
    // Emissions Section
    virginDirectEmissions: 'number',
    recycledDirectEmissions: 'number',
    
    // Grid Composition (percentages that sum to 100)
    coalPercent: 'range',
    gasPercent: 'range',
    oilPercent: 'range',
    nuclearPercent: 'range',
    hydroPercent: 'range',
    windPercent: 'range',
    solarPercent: 'range',
    otherRenewablePercent: 'range',
    
    // Transport
    transportMode: 'select', // truck, ship, rail, air
    distanceKm: 'number',
    weightTonnes: 'number', // auto-calculate from mass
    
    // Recycling
    recycledContentPercent: 'range',
    collectionRatePercent: 'range',
    recyclingEfficiencyPercent: 'range'
};
```

### 2. Results Display Components

**Key Metrics Card:**
```javascript
const keyMetrics = {
    carbonFootprint: 'number with unit (kg CO2e)',
    carbonIntensity: 'number with unit (kg CO2e/kg)',
    circularityIndex: 'progress bar (0-1)',
    sustainabilityScore: 'rating stars (0-10)',
    energyConsumption: 'number with unit (kWh)',
    recyclingBenefit: 'number with unit (kg CO2e saved)'
};
```

**Emissions Breakdown Chart:**
```javascript
const emissionsBreakdown = {
    materialEmissions: 'number',
    energyEmissions: 'number',
    transportEmissions: 'number',
    processEmissions: 'number'
    // Display as pie chart or bar chart
};
```

### 3. Error Handling

**HTTP Status Codes:**
- 200: Success
- 400: Bad request (validation errors)
- 500: Server error

**Error Response Format:**
```json
{
    "detail": "Error message description"
}
```

### 4. Loading States

**Recommended UX:**
- Quick Analysis: ~2-5 seconds
- Comprehensive Analysis: ~5-10 seconds
- File Analysis: ~10-30 seconds (depending on file size)

### 5. Example Frontend Code

**React/JavaScript Example:**
```javascript
// Quick Analysis API Call
const performQuickAnalysis = async (formData) => {
    try {
        const response = await fetch('http://localhost:8000/analyze/quick', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                material_type: formData.materialType,
                mass_kg: parseFloat(formData.massKg),
                recycled_content_percent: parseFloat(formData.recycledContentPercent),
                transport_distance_km: parseFloat(formData.transportDistanceKm),
                renewable_energy_percent: parseFloat(formData.renewableEnergyPercent)
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        // Handle success
        displayResults(result.results);
        showRecommendations(result.recommendations);
        
    } catch (error) {
        console.error('Analysis failed:', error);
        showError('Analysis failed. Please try again.');
    }
};

// Get material options for dropdown
const getMaterialOptions = async () => {
    const response = await fetch('http://localhost:8000/options/materials');
    const data = await response.json();
    return data.materials; // Use for populating dropdown
};
```

### 6. File Upload Component

```javascript
const handleFileUpload = async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('analysis_type', 'cradle_to_gate');
    
    const response = await fetch('http://localhost:8000/analyze/file', {
        method: 'POST',
        body: formData
    });
    
    const result = await response.json();
    // Handle batch results
};
```

### 7. Recommended UI Flow

1. **Landing Page**: Choose Quick vs Comprehensive Analysis
2. **Quick Mode**: Simple form → Submit → Results with recommendations
3. **Advanced Mode**: Tabbed form (Material → Energy → Grid → Transport → Recycling) → Results
4. **File Mode**: Upload area → Processing → Batch results

### 8. Data Validation on Frontend

```javascript
const validateQuickForm = (data) => {
    const errors = {};
    
    if (!data.materialType) errors.materialType = 'Material type is required';
    if (data.massKg <= 0) errors.massKg = 'Mass must be positive';
    if (data.recycledContentPercent < 0 || data.recycledContentPercent > 100) {
        errors.recycledContentPercent = 'Must be between 0-100%';
    }
    if (data.transportDistanceKm < 0) errors.transportDistanceKm = 'Distance must be positive';
    if (data.renewableEnergyPercent < 0 || data.renewableEnergyPercent > 100) {
        errors.renewableEnergyPercent = 'Must be between 0-100%';
    }
    
    return Object.keys(errors).length === 0 ? null : errors;
};
```

## Summary for Your Frontend Team

**What they need to build:**

1. **Forms**: Quick analysis (5 fields) and Comprehensive analysis (20+ fields)
2. **Results Display**: Metrics cards, charts, recommendations list
3. **File Upload**: Drag-and-drop with progress indication
4. **Navigation**: Toggle between analysis modes
5. **Error Handling**: User-friendly error messages
6. **Loading States**: Progress indicators during analysis

**Key API endpoints to integrate:**
- `POST /analyze/quick` - Main analysis endpoint
- `GET /options/materials` - Populate dropdowns
- `GET /options/transport` - Transport mode options
- `POST /analyze/file` - File upload analysis

**Data flow:**
Frontend Form → Validation → API Call → Display Results → Show Recommendations