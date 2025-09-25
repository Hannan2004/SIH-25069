"""
Streamlit MVP Dashboard for LCA Analysis System
Professional dashboard to trigger agentic workflow with comprehensive input handling
"""

import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
from pathlib import Path
from datetime import datetime
import time
import os

# Add current directory to path for imports
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

# Import your main system
try:
    from main import LCASystem, run_quick_lca_analysis, run_file_analysis
    SYSTEM_AVAILABLE = True
except ImportError as e:
    st.error(f"System import error: {e}")
    SYSTEM_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="LCA Analysis Dashboard",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #2E8B57, #3CB371);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #2E8B57;
    }
    .status-success { color: #28a745; font-weight: bold; }
    .status-error { color: #dc3545; font-weight: bold; }
    .status-warning { color: #ffc107; font-weight: bold; }
    .workflow-step {
        padding: 0.5rem;
        margin: 0.25rem;
        border-radius: 5px;
        border-left: 3px solid #2E8B57;
        background: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None
if 'analysis_history' not in st.session_state:
    st.session_state.analysis_history = []

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🌍 LCA Analysis Dashboard</h1>
        <p>Comprehensive Life Cycle Assessment with AI-Powered Insights</p>
    </div>
    """, unsafe_allow_html=True)
    
    if not SYSTEM_AVAILABLE:
        st.error("❌ LCA System not available. Please check the backend setup.")
        return
    
    # Sidebar for navigation
    st.sidebar.title("📊 Navigation")
    tab_selection = st.sidebar.radio(
        "Select Analysis Mode:",
        ["🚀 Quick Analysis", "📁 File Upload", "📈 Advanced Setup", "📋 Results Dashboard"]
    )
    
    # Main content based on selection
    if tab_selection == "🚀 Quick Analysis":
        quick_analysis_tab()
    elif tab_selection == "📁 File Upload":
        file_upload_tab()
    elif tab_selection == "📈 Advanced Setup":
        advanced_setup_tab()
    elif tab_selection == "📋 Results Dashboard":
        results_dashboard_tab()

def quick_analysis_tab():
    st.header("🚀 Quick LCA Analysis")
    st.markdown("Get rapid insights with default parameters for common materials")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Input Parameters")
        
        # Basic parameters
        material_type = st.selectbox(
            "Material Type",
            ["aluminum", "steel", "copper", "zinc", "lead", "nickel", "tin", "magnesium", "titanium"],
            help="Select the primary material for analysis"
        )
        
        mass_kg = st.number_input(
            "Mass (kg)",
            min_value=0.1,
            max_value=10000.0,
            value=1000.0,
            step=10.0,
            help="Total mass of material to analyze"
        )
        
        recycled_content = st.slider(
            "Recycled Content (%)",
            min_value=0,
            max_value=100,
            value=30,
            help="Percentage of recycled content in the material"
        )
        
        transport_distance = st.number_input(
            "Transport Distance (km)",
            min_value=0,
            max_value=5000,
            value=100,
            help="Distance for material transport"
        )
        
        renewable_energy = st.slider(
            "Grid Renewable Energy (%)",
            min_value=0,
            max_value=100,
            value=30,
            help="Percentage of renewable energy in the grid"
        )
    
    with col2:
        st.subheader("Analysis Settings")
        
        analysis_type = st.selectbox(
            "Analysis Scope",
            ["cradle_to_gate", "cradle_to_grave", "gate_to_gate"],
            help="Define the system boundaries for analysis"
        )
        
        study_type = st.selectbox(
            "Study Type",
            ["internal_decision_support", "comparative_assertion", "public_communication"],
            help="Purpose of the LCA study"
        )
    
    # Analysis button
    if st.button("🔍 Run Quick Analysis", type="primary", use_container_width=True):
        run_quick_analysis(material_type, mass_kg, recycled_content, transport_distance, renewable_energy, analysis_type, study_type)

def file_upload_tab():
    st.header("📁 File Upload Analysis")
    st.markdown("Upload your comprehensive LCA data file (CSV or Excel)")
    
    # File upload section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Choose LCA Data File",
            type=['csv', 'xlsx', 'xls'],
            help="Upload CSV or Excel file with comprehensive LCA parameters"
        )
        
        if uploaded_file is not None:
            # Preview the uploaded file
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                
                st.subheader("📋 Data Preview")
                st.dataframe(df.head())
                
                st.subheader("📊 Data Summary")
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.metric("Rows", len(df))
                with col_b:
                    st.metric("Columns", len(df.columns))
                with col_c:
                    st.metric("Materials", df['Material'].nunique() if 'Material' in df.columns else 'N/A')
                
            except Exception as e:
                st.error(f"Error reading file: {e}")
                return
    
    with col2:
        st.subheader("Analysis Settings")
        
        analysis_type = st.selectbox(
            "Analysis Scope",
            ["cradle_to_gate", "cradle_to_grave", "gate_to_gate"],
            key="file_analysis_type"
        )
        
        study_type = st.selectbox(
            "Study Type",
            ["internal_decision_support", "comparative_assertion", "public_communication"],
            key="file_study_type"
        )
        
        report_format = st.multiselect(
            "Report Formats",
            ["pdf", "html", "json"],
            default=["pdf", "json"],
            help="Select output formats for the report"
        )
    
    # Analysis button
    if uploaded_file is not None:
        if st.button("📊 Analyze File Data", type="primary", use_container_width=True):
            run_file_analysis_workflow(uploaded_file, analysis_type, study_type, report_format)

def advanced_setup_tab():
    st.header("📈 Advanced LCA Setup")
    st.markdown("Configure detailed parameters for comprehensive analysis")
    
    # Material Configuration
    st.subheader("🏭 Material Configuration")
    col1, col2 = st.columns(2)
    
    with col1:
        material_type = st.selectbox(
            "Material Type",
            ["aluminum", "steel", "copper", "zinc", "lead", "nickel", "tin", "magnesium", "titanium"],
            key="adv_material"
        )
        mass_kg = st.number_input("Mass (kg)", value=1000.0, key="adv_mass")
    
    with col2:
        ei_process = st.number_input("Energy Intensity - Virgin (kWh/kg)", value=15.0, key="adv_ei_virgin")
        ei_recycled = st.number_input("Energy Intensity - Recycled (kWh/kg)", value=3.0, key="adv_ei_recycled")
    
    # Energy and Emissions
    st.subheader("⚡ Energy & Emissions")
    col1, col2 = st.columns(2)
    
    with col1:
        ef_direct = st.number_input("Direct Emissions - Virgin (kg CO2e/kg)", value=2.0)
        ef_direct_recycled = st.number_input("Direct Emissions - Recycled (kg CO2e/kg)", value=0.5)
    
    with col2:
        virgin_ef = st.number_input("Virgin Material EF (kg CO2e/kg)", value=11.5)
        secondary_ef = st.number_input("Secondary Material EF (kg CO2e/kg)", value=0.64)
    
    # Grid Composition
    st.subheader("🔌 Grid Composition (%)")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        coal_pct = st.number_input("Coal", value=30.0, min_value=0.0, max_value=100.0)
        gas_pct = st.number_input("Gas", value=40.0, min_value=0.0, max_value=100.0)
    
    with col2:
        oil_pct = st.number_input("Oil", value=5.0, min_value=0.0, max_value=100.0)
        nuclear_pct = st.number_input("Nuclear", value=10.0, min_value=0.0, max_value=100.0)
    
    with col3:
        hydro_pct = st.number_input("Hydro", value=5.0, min_value=0.0, max_value=100.0)
        wind_pct = st.number_input("Wind", value=5.0, min_value=0.0, max_value=100.0)
    
    with col4:
        solar_pct = st.number_input("Solar", value=3.0, min_value=0.0, max_value=100.0)
        other_pct = st.number_input("Other", value=2.0, min_value=0.0, max_value=100.0)
    
    # Transport Parameters
    st.subheader("🚚 Transport Parameters")
    col1, col2 = st.columns(2)
    
    with col1:
        transport_mode = st.selectbox("Transport Mode", ["truck", "ship", "rail", "air"])
        transport_distance = st.number_input("Distance (km)", value=100.0)
    
    with col2:
        transport_weight = st.number_input("Weight (tonne)", value=1.0)
        transport_ef = st.number_input("Transport EF (kg CO2e/tkm)", value=0.062)
    
    # Recycling Parameters
    st.subheader("♻️ Recycling Parameters")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        collection_rate = st.slider("Collection Rate (%)", 0, 100, 75)
    
    with col2:
        recycling_efficiency = st.slider("Recycling Efficiency (%)", 0, 100, 90)
    
    with col3:
        secondary_content = st.slider("Existing Secondary Content (%)", 0, 100, 30)
    
    # Analysis Settings
    st.subheader("⚙️ Analysis Settings")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        analysis_type = st.selectbox("Analysis Type", ["cradle_to_gate", "cradle_to_grave"], key="adv_analysis_type")
    
    with col2:
        study_type = st.selectbox("Study Type", ["internal_decision_support", "comparative_assertion", "public_communication"], key="adv_study_type")
    
    with col3:
        report_type = st.selectbox("Report Type", ["technical", "executive", "regulatory"])
    
    # Run Analysis
    if st.button("🔬 Run Advanced Analysis", type="primary", use_container_width=True):
        
        # Validate grid composition
        total_grid = coal_pct + gas_pct + oil_pct + nuclear_pct + hydro_pct + wind_pct + solar_pct + other_pct
        if abs(total_grid - 100) > 5:
            st.warning(f"⚠️ Grid composition sums to {total_grid:.1f}%. Should be close to 100%.")
        
        # Create comprehensive input data
        input_data = {
            "scenarios": [{
                "material_type": material_type,
                "mass_kg": mass_kg,
                "energy_intensity": {
                    "virgin_process_kwh_per_kg": ei_process,
                    "recycled_process_kwh_per_kg": ei_recycled
                },
                "direct_emissions": {
                    "virgin_kg_co2e_per_kg": ef_direct,
                    "recycled_kg_co2e_per_kg": ef_direct_recycled
                },
                "grid_composition": {
                    "coal_pct": coal_pct, "gas_pct": gas_pct, "oil_pct": oil_pct,
                    "nuclear_pct": nuclear_pct, "hydro_pct": hydro_pct,
                    "wind_pct": wind_pct, "solar_pct": solar_pct, "other_pct": other_pct
                },
                "transport": {
                    "mode": transport_mode,
                    "distance_km": transport_distance,
                    "weight_t": transport_weight,
                    "emission_factor_kg_co2e_per_tkm": transport_ef
                },
                "material_emission_factors": {
                    "virgin_kg_co2e_per_kg": virgin_ef,
                    "secondary_kg_co2e_per_kg": secondary_ef
                },
                "recycling": {
                    "collection_rate_pct": collection_rate,
                    "recycling_efficiency_pct": recycling_efficiency,
                    "secondary_content_existing_pct": secondary_content
                }
            }],
            "analysis_type": analysis_type,
            "study_type": study_type,
            "report_type": report_type,
            "format_type": "all"
        }
        
        run_advanced_analysis(input_data)

def run_quick_analysis(material_type, mass_kg, recycled_content, transport_distance, renewable_energy, analysis_type, study_type):
    """Run quick analysis and display results"""
    
    with st.spinner("🔄 Running LCA Analysis Workflow..."):
        # Create progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Simulate workflow steps
        steps = [
            "Initializing system...",
            "Processing input data...",
            "Running LCA calculations...",
            "Checking compliance...",
            "Generating reports..."
        ]
        
        for i, step in enumerate(steps):
            status_text.text(step)
            progress_bar.progress((i + 1) / len(steps))
            time.sleep(0.5)  # Simulate processing time
        
        try:
            # Run analysis using the imported function
            system = LCASystem()
            
            # Create input data for quick analysis
            input_data = {
                "scenarios": [{
                    "material_type": material_type.lower(),
                    "mass_kg": mass_kg,
                    "energy_intensity": {"virgin_process_kwh_per_kg": 15.0, "recycled_process_kwh_per_kg": 3.0},
                    "direct_emissions": {"virgin_kg_co2e_per_kg": 2.0, "recycled_kg_co2e_per_kg": 0.5},
                    "grid_composition": {
                        "coal_pct": 50 - renewable_energy/2, "gas_pct": 30, "oil_pct": 5,
                        "nuclear_pct": 10, "hydro_pct": renewable_energy*0.3,
                        "wind_pct": renewable_energy*0.4, "solar_pct": renewable_energy*0.3, "other_pct": 5
                    },
                    "transport": {"mode": "truck", "distance_km": transport_distance, "weight_t": mass_kg/1000, "emission_factor_kg_co2e_per_tkm": 0.062},
                    "material_emission_factors": {"virgin_kg_co2e_per_kg": 11.5, "secondary_kg_co2e_per_kg": 0.64},
                    "recycling": {"collection_rate_pct": 75, "recycling_efficiency_pct": 90, "secondary_content_existing_pct": recycled_content}
                }],
                "analysis_type": analysis_type,
                "study_type": study_type,
                "report_type": "technical",
                "format_type": "json"
            }
            
            result = system.run_complete_analysis(input_data)
            
            # Store results in session state
            st.session_state.analysis_results = result
            st.session_state.analysis_history.append({
                "timestamp": datetime.now(),
                "type": "Quick Analysis",
                "material": material_type,
                "mass": mass_kg,
                "result": result
            })
            
            status_text.text("✅ Analysis completed successfully!")
            progress_bar.progress(1.0)
            
            # Display results
            if result.get("success"):
                display_analysis_results(result)
            else:
                st.error(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            st.error(f"❌ Error during analysis: {e}")

def run_file_analysis_workflow(uploaded_file, analysis_type, study_type, report_format):
    """Run file-based analysis workflow"""
    
    with st.spinner("🔄 Processing file and running analysis..."):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Save uploaded file temporarily
            temp_file_path = f"./temp_{uploaded_file.name}"
            with open(temp_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            status_text.text("📁 File uploaded successfully")
            progress_bar.progress(0.2)
            
            # Determine file type
            file_type = "excel" if uploaded_file.name.endswith(('.xlsx', '.xls')) else "csv"
            
            status_text.text("🔄 Running LCA analysis workflow...")
            progress_bar.progress(0.4)
            
            # Run analysis
            result = run_file_analysis(temp_file_path, file_type)
            
            progress_bar.progress(0.8)
            
            # Clean up temp file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            
            # Store results
            st.session_state.analysis_results = result
            st.session_state.analysis_history.append({
                "timestamp": datetime.now(),
                "type": "File Analysis",
                "filename": uploaded_file.name,
                "result": result
            })
            
            status_text.text("✅ File analysis completed!")
            progress_bar.progress(1.0)
            
            # Display results
            if result.get("success"):
                display_analysis_results(result)
            else:
                st.error(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            st.error(f"❌ Error during file analysis: {e}")
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

def run_advanced_analysis(input_data):
    """Run advanced analysis with comprehensive parameters"""
    
    with st.spinner("🔄 Running comprehensive LCA analysis..."):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            system = LCASystem()
            
            status_text.text("🔄 Executing agentic workflow...")
            progress_bar.progress(0.3)
            
            result = system.run_complete_analysis(input_data)
            
            progress_bar.progress(0.8)
            
            # Store results
            st.session_state.analysis_results = result
            st.session_state.analysis_history.append({
                "timestamp": datetime.now(),
                "type": "Advanced Analysis",
                "material": input_data["scenarios"][0]["material_type"],
                "result": result
            })
            
            status_text.text("✅ Advanced analysis completed!")
            progress_bar.progress(1.0)
            
            # Display results
            if result.get("success"):
                display_analysis_results(result)
            else:
                st.error(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            st.error(f"❌ Error during advanced analysis: {e}")

def display_analysis_results(result):
    """Display comprehensive analysis results"""
    
    st.success("✅ Analysis completed successfully!")
    
    # Extract key metrics
    summary = result.get("summary", {})
    lca_summary = summary.get("lca_summary", {})
    compliance_summary = summary.get("compliance_summary", {})
    
    # Key Metrics Cards
    st.subheader("📊 Key Results")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Carbon Footprint",
            f"{lca_summary.get('total_carbon_footprint_kg_co2_eq', 0):.1f}",
            help="Total kg CO₂-equivalent emissions"
        )
    
    with col2:
        st.metric(
            "Carbon Intensity",
            f"{lca_summary.get('carbon_intensity_per_kg', 0):.2f}",
            help="kg CO₂-eq per kg of material"
        )
    
    with col3:
        st.metric(
            "Circularity Index",
            f"{lca_summary.get('circularity_index', 0):.3f}",
            help="Circular economy performance (0-1)"
        )
    
    with col4:
        st.metric(
            "Compliance Grade",
            compliance_summary.get('compliance_grade', 'N/A'),
            help="ISO 14040/14044 compliance grade"
        )
    
    # Detailed Results Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📈 LCA Results", "✅ Compliance", "📋 Workflow", "📁 Files"])
    
    with tab1:
        display_lca_results_tab(result)
    
    with tab2:
        display_compliance_tab(result)
    
    with tab3:
        display_workflow_tab(result)
    
    with tab4:
        display_files_tab(result)

def display_lca_results_tab(result):
    """Display LCA results with visualizations"""
    
    detailed_results = result.get("detailed_results", {})
    lca_results = detailed_results.get("lca", {}).get("lca_results", {})
    
    # Emissions breakdown
    emissions_breakdown = lca_results.get("emissions_breakdown", {})
    if emissions_breakdown:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Emissions Breakdown")
            # Create pie chart
            labels = []
            values = []
            for key, value in emissions_breakdown.items():
                if key != "total_kg_co2e" and value > 0:
                    labels.append(key.replace("_kg_co2e", "").replace("_", " ").title())
                    values.append(value)
            
            if values:
                fig_pie = px.pie(values=values, names=labels, title="Emissions by Category")
                st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            st.subheader("Emissions Data")
            emissions_df = pd.DataFrame([
                {"Category": k.replace("_kg_co2e", "").replace("_", " ").title(), 
                 "Emissions (kg CO₂-eq)": v} 
                for k, v in emissions_breakdown.items() if v > 0
            ])
            st.dataframe(emissions_df, use_container_width=True)

def display_compliance_tab(result):
    """Display compliance results"""
    
    detailed_results = result.get("detailed_results", {})
    compliance_results = detailed_results.get("compliance", {})
    
    if compliance_results.get("success"):
        overall_score = compliance_results.get("overall_compliance_score", {})
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Overall Compliance")
            st.metric("Score", f"{overall_score.get('overall_score', 0):.1%}")
            st.metric("Grade", overall_score.get('grade', 'N/A'))
            st.info(f"Status: {overall_score.get('status', 'Unknown')}")
        
        with col2:
            st.subheader("Category Scores")
            categories = compliance_results.get("compliance_categories", {})
            for category, details in categories.items():
                if isinstance(details, dict):
                    score = details.get('score', 0)
                    st.write(f"**{category.replace('_', ' ').title()}:** {score:.1%}")
    else:
        st.warning("Compliance check not completed successfully")

def display_workflow_tab(result):
    """Display workflow execution details"""
    
    st.subheader("🔄 Workflow Execution")
    
    # Workflow messages
    messages = result.get("workflow_messages", [])
    for i, message in enumerate(messages):
        if isinstance(message, dict):
            content = message.get("content", "")
            st.markdown(f"""
            <div class="workflow-step">
                <strong>Step {i+1}:</strong> {content}
            </div>
            """, unsafe_allow_html=True)
    
    # Analysis metadata
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Analysis Info")
        st.write(f"**Analysis ID:** {result.get('analysis_id', 'N/A')}")
        st.write(f"**Status:** {result.get('workflow_status', 'N/A')}")
        st.write(f"**Timestamp:** {result.get('workflow_timestamp', 'N/A')}")
    
    with col2:
        st.subheader("Performance")
        if messages:
            st.write(f"**Workflow Steps:** {len(messages)}")
            st.write(f"**Success Rate:** {'100%' if result.get('success') else 'Failed'}")

def display_files_tab(result):
    """Display generated files and reports"""
    
    detailed_results = result.get("detailed_results", {})
    report_results = detailed_results.get("reporting", {})
    
    if report_results.get("success"):
        st.subheader("📁 Generated Reports")
        
        output_files = report_results.get("output_files", {})
        for format_type, file_path in output_files.items():
            st.write(f"**{format_type.upper()} Report:** `{file_path}`")
        
        charts_created = report_results.get("visualizations_created", 0)
        st.write(f"**Charts Generated:** {charts_created}")
        
        # Show sample data if available
        summary = result.get("summary", {})
        if summary:
            st.subheader("📊 Summary Data")
            st.json(summary)
    else:
        st.warning("Report generation not completed successfully")

def results_dashboard_tab():
    """Display results dashboard with history"""
    
    st.header("📋 Results Dashboard")
    
    if not st.session_state.analysis_history:
        st.info("No analysis history available. Run an analysis first!")
        return
    
    # Analysis history
    st.subheader("📈 Analysis History")
    
    history_data = []
    for analysis in st.session_state.analysis_history:
        result = analysis["result"]
        summary = result.get("summary", {}) if result.get("success") else {}
        lca_summary = summary.get("lca_summary", {})
        
        history_data.append({
            "Timestamp": analysis["timestamp"].strftime("%Y-%m-%d %H:%M"),
            "Type": analysis["type"],
            "Material": analysis.get("material", analysis.get("filename", "N/A")),
            "Carbon Footprint (kg CO₂-eq)": lca_summary.get("total_carbon_footprint_kg_co2_eq", 0),
            "Status": "✅ Success" if result.get("success") else "❌ Failed"
        })
    
    history_df = pd.DataFrame(history_data)
    st.dataframe(history_df, use_container_width=True)
    
    # Current results
    if st.session_state.analysis_results:
        st.subheader("📊 Latest Analysis Results")
        display_analysis_results(st.session_state.analysis_results)

if __name__ == "__main__":
    main()