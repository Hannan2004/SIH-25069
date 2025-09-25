"""
Simple Streamlit App to test LCA Analysis System
Tests all agents: Data Ingestion, LCA, Compliance, and Reporting with LangGraph workflow
"""

import streamlit as st
import json
import os
import sys
from datetime import datetime
from pathlib import Path
import pandas as pd
import tempfile

# Add current directory to path for imports
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

# Import your agents
try:
    from lca_agent import LCAAgent
    from data_ingestion_agent import DataIngestionAgent
    from compliance_agent import ComplianceAgent
    from reporting_agent import ReportingAgent
    from main import LCASystem, run_quick_lca_analysis, run_file_analysis
    agents_available = True
except ImportError as e:
    st.error(f"Error importing agents: {e}")
    agents_available = False

# Streamlit page config
st.set_page_config(
    page_title="LCA Analysis System Test",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .success-card {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
    }
    .error-card {
        background-color: #f8d7da;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #dc3545;
    }
</style>
""", unsafe_allow_html=True)

# Title and description
st.title("🌍 LCA Analysis System Test App")
st.markdown("Test your LCA agents individually or run complete LangGraph workflow analysis")

# Sidebar for navigation
st.sidebar.title("🧪 Test Options")
test_mode = st.sidebar.selectbox(
    "Select Test Mode:",
    ["Complete LangGraph Workflow", "Individual Agents", "File Upload Test", "Agent Status Check"]
)

# Check if agents are available
if not agents_available:
    st.error("❌ Agents not available. Please check your imports and dependencies.")
    st.stop()

# Agent Status Check
if test_mode == "Agent Status Check":
    st.header("🔍 Agent Status Check")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Test each agent
    agents_status = {}
    
    with col1:
        st.subheader("LCA Agent")
        try:
            lca_agent = LCAAgent()
            agents_status["LCA Agent"] = "✅ Ready"
            st.success("✅ Ready")
            st.write("Methods available:")
            st.write("• `perform_lca_analysis()`")
        except Exception as e:
            agents_status["LCA Agent"] = f"❌ Error: {str(e)[:50]}..."
            st.error(f"❌ Error: {str(e)[:50]}...")
    
    with col2:
        st.subheader("Data Ingestion Agent")
        try:
            di_agent = DataIngestionAgent()
            agents_status["Data Ingestion Agent"] = "✅ Ready"
            st.success("✅ Ready")
            st.write("Methods available:")
            st.write("• `ingest_data()`")
            st.write("• `preprocess_data()`")
        except Exception as e:
            agents_status["Data Ingestion Agent"] = f"❌ Error: {str(e)[:50]}..."
            st.error(f"❌ Error: {str(e)[:50]}...")
    
    with col3:
        st.subheader("Compliance Agent")
        try:
            compliance_agent = ComplianceAgent()
            agents_status["Compliance Agent"] = "✅ Ready"
            st.success("✅ Ready")
            st.write("Methods available:")
            st.write("• `check_lca_compliance()`")
        except Exception as e:
            agents_status["Compliance Agent"] = f"❌ Error: {str(e)[:50]}..."
            st.error(f"❌ Error: {str(e)[:50]}...")
    
    with col4:
        st.subheader("Reporting Agent")
        try:
            reporting_agent = ReportingAgent()
            agents_status["Reporting Agent"] = "✅ Ready"
            st.success("✅ Ready")
            st.write("Methods available:")
            st.write("• `generate_report()`")
        except Exception as e:
            agents_status["Reporting Agent"] = f"❌ Error: {str(e)[:50]}..."
            st.error(f"❌ Error: {str(e)[:50]}...")
    
    # LangGraph Workflow Test
    st.header("🔄 LangGraph Workflow Status")
    try:
        lca_system = LCASystem()
        st.success("✅ LangGraph workflow initialized successfully")
        st.write("Workflow nodes:")
        st.write("• Data Ingestion → LCA Analysis → Compliance Check → Report Generation")
    except Exception as e:
        st.error(f"❌ LangGraph workflow error: {str(e)}")
    
    # Environment check
    st.header("🔧 Environment Check")
    env_status = {}
    
    env_vars = ["CEREBRAS_API_KEY", "PINECONE_API_KEY", "PINECONE_ENVIRONMENT"]
    cols = st.columns(len(env_vars))
    
    for i, var in enumerate(env_vars):
        with cols[i]:
            value = os.getenv(var)
            if value:
                env_status[var] = "✅ Set"
                st.success(f"✅ {var}")
                st.write("Set")
            else:
                env_status[var] = "⚠️ Not set"
                st.warning(f"⚠️ {var}")
                st.write("Not set")
    
    # Summary
    st.header("📊 Status Summary")
    with st.expander("View Detailed Status"):
        st.json({**agents_status, **env_status})

# Individual Agent Testing
elif test_mode == "Individual Agents":
    st.header("🧪 Individual Agent Testing")
    
    agent_choice = st.selectbox(
        "Select Agent to Test:",
        ["LCA Agent", "Data Ingestion Agent", "Compliance Agent", "Reporting Agent"]
    )
    
    if agent_choice == "LCA Agent":
        st.subheader("🏭 LCA Agent Test")
        
        col1, col2 = st.columns(2)
        
        with col1:
            metal_type = st.selectbox("Metal Type:", ["steel", "aluminum", "copper", "zinc"])
            production_kg = st.number_input("Production (kg):", min_value=1.0, value=1000.0)
        
        with col2:
            recycled_fraction = st.slider("Recycled Fraction:", 0.0, 1.0, 0.3)
            region = st.selectbox("Region:", ["US_average", "EU_average", "China", "Global_average"])
        
        if st.button("🚀 Test LCA Agent"):
            with st.spinner("Running LCA calculation..."):
                try:
                    lca_agent = LCAAgent()
                    result = lca_agent.perform_lca_analysis(  # Fixed method name
                        metal_type=metal_type,
                        production_kg=production_kg,
                        recycled_fraction=recycled_fraction,
                        region=region
                    )
                    
                    if result.get("success"):
                        st.success("✅ LCA Agent working correctly!")
                        
                        # Display key results
                        lca_data = result.get("lca_results", {})
                        gwp_impact = lca_data.get("gwp_impact", {})
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total GWP", f"{gwp_impact.get('total_kg_co2_eq', 0):,.1f} kg CO₂-eq")
                        with col2:
                            st.metric("GWP per kg", f"{gwp_impact.get('kg_co2_eq_per_kg_metal', 0):.2f} kg CO₂-eq/kg")
                        with col3:
                            sustainability = result.get("ai_insights", {}).get("sustainability_score", {})
                            st.metric("Sustainability Score", f"{sustainability.get('overall_score', 0):.1f}/100")
                        
                        # Show detailed results
                        with st.expander("📋 Detailed Results"):
                            st.json(result)
                    else:
                        st.error(f"❌ LCA Agent failed: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    st.error(f"❌ Error testing LCA Agent: {str(e)}")
    
    elif agent_choice == "Data Ingestion Agent":
        st.subheader("📊 Data Ingestion Agent Test")
        
        # Create sample CSV data for testing
        st.write("**Test with sample data:**")
        
        sample_data = {
            "Metal_Type": ["aluminum", "steel", "copper"],
            "Production_kg": [1000, 2000, 500],
            "Recycled_Fraction": [0.3, 0.25, 0.4],
            "Region": ["US_average", "EU_average", "China"]
        }
        
        # Show sample data
        df = pd.DataFrame(sample_data)
        st.dataframe(df)
        
        if st.button("🔍 Test Data Ingestion Agent"):
            with st.spinner("Testing data ingestion..."):
                try:
                    # Save sample data to temporary file
                    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
                        df.to_csv(f.name, index=False)
                        temp_file_path = f.name
                    
                    di_agent = DataIngestionAgent()
                    result = di_agent.ingest_data(
                        file_path=temp_file_path,
                        file_type="csv"
                    )
                    
                    # Clean up temp file
                    os.unlink(temp_file_path)
                    
                    if result.get("success"):
                        st.success("✅ Data Ingestion Agent working correctly!")
                        
                        # Display key metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Records Processed", result.get("records_count", 0))
                        with col2:
                            data_quality = result.get("data_quality", {})
                            st.metric("Data Quality", f"{data_quality.get('completeness', 0):.1%}")
                        with col3:
                            st.metric("Processing Status", "✅ Success")
                        
                        # Show processed data
                        processed_data = result.get("processed_data", {})
                        if processed_data:
                            with st.expander("📋 Processed Data"):
                                st.json(processed_data)
                    else:
                        st.error(f"❌ Data Ingestion Agent failed: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    st.error(f"❌ Error testing Data Ingestion Agent: {str(e)}")
    
    elif agent_choice == "Compliance Agent":
        st.subheader("📋 Compliance Agent Test")
        
        study_type = st.selectbox(
            "Study Type:",
            ["internal_decision_support", "comparative_assertion", "public_communication"]
        )
        
        # Create sample LCA data for testing
        sample_data = {
            "functional_unit": "1 kg of aluminum",
            "system_boundaries": "cradle-to-gate",
            "goal": "Environmental impact assessment",
            "scope": "Primary aluminum production",
            "lca_results": {
                "input_parameters": {
                    "metal_type": "aluminum",
                    "production_kg": 1000
                },
                "gwp_impact": {
                    "total_kg_co2_eq": 15000
                }
            },
            "impact_categories": ["climate_change", "acidification"],
            "methodology": "ISO 14040/14044",
            "data_sources": ["EcoInvent"]
        }
        
        # Show sample data
        with st.expander("📋 Sample LCA Study Data"):
            st.json(sample_data)
        
        if st.button("✅ Test Compliance Agent"):
            with st.spinner("Checking ISO compliance..."):
                try:
                    compliance_agent = ComplianceAgent()
                    result = compliance_agent.check_lca_compliance(sample_data, study_type)
                    
                    if result.get("success"):
                        st.success("✅ Compliance Agent working correctly!")
                        
                        # Display compliance score
                        overall_score = result.get("overall_compliance_score", {})
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Compliance Grade", overall_score.get("grade", "N/A"))
                        with col2:
                            st.metric("Overall Score", f"{overall_score.get('overall_score', 0):.1%}")
                        with col3:
                            st.metric("Status", overall_score.get("status", "Unknown"))
                        
                        # Show compliance report
                        compliance_report = result.get("compliance_report", "")
                        if compliance_report:
                            with st.expander("📄 Compliance Report"):
                                st.text(compliance_report)
                        
                        with st.expander("📋 Detailed Compliance Results"):
                            st.json(result)
                    else:
                        st.error(f"❌ Compliance Agent failed: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    st.error(f"❌ Error testing Compliance Agent: {str(e)}")
    
    elif agent_choice == "Reporting Agent":
        st.subheader("📄 Reporting Agent Test")
        
        col1, col2 = st.columns(2)
        
        with col1:
            report_type = st.selectbox("Report Type:", ["technical", "executive", "regulatory"])
        with col2:
            format_type = st.selectbox("Format:", ["pdf", "html", "json", "all"])
        
        # Create sample data for testing
        sample_lca_results = {
            "success": True,
            "lca_results": {
                "input_parameters": {
                    "metal_type": "aluminum",
                    "production_kg": 1000,
                    "recycled_fraction": 0.3
                },
                "gwp_impact": {
                    "total_kg_co2_eq": 15000,
                    "kg_co2_eq_per_kg_metal": 15.0
                },
                "total_emissions": {
                    "CO2": 12000,
                    "CH4": 100,
                    "N2O": 50
                },
                "production_breakdown": {
                    "primary_percentage": 70,
                    "secondary_percentage": 30
                }
            },
            "ai_insights": {
                "sustainability_score": {
                    "overall_score": 75,
                    "grade": "B"
                }
            }
        }
        
        sample_compliance_results = {
            "overall_compliance_score": {
                "overall_score": 0.85,
                "grade": "B",
                "status": "Largely Compliant"
            }
        }
        
        if st.button("📊 Test Reporting Agent"):
            with st.spinner("Generating report..."):
                try:
                    reporting_agent = ReportingAgent()
                    result = reporting_agent.generate_report(
                        lca_results=sample_lca_results,
                        compliance_results=sample_compliance_results,
                        report_type=report_type,
                        format_type=format_type
                    )
                    
                    if result.get("success"):
                        st.success("✅ Reporting Agent working correctly!")
                        
                        # Display generation info
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Files Generated", len(result.get("output_files", {})))
                        with col2:
                            st.metric("Visualizations", result.get("visualizations_created", 0))
                        
                        # Show generated files
                        output_files = result.get("output_files", {})
                        if output_files:
                            st.write("📁 Generated Files:")
                            for format_name, file_path in output_files.items():
                                if file_path and Path(file_path).exists():
                                    st.write(f"• {format_name.upper()}: ✅ {Path(file_path).name}")
                                elif file_path:
                                    st.write(f"• {format_name.upper()}: ⚠️ {Path(file_path).name} (file not found)")
                        
                        with st.expander("📋 Report Generation Details"):
                            st.json(result)
                    else:
                        st.error(f"❌ Reporting Agent failed: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    st.error(f"❌ Error testing Reporting Agent: {str(e)}")

# File Upload Test
elif test_mode == "File Upload Test":
    st.header("📁 File Upload Test")
    
    st.markdown("Test the file upload functionality with your data ingestion agent")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a CSV or Excel file",
        type=['csv', 'xlsx', 'xls'],
        help="Upload a file with columns: Metal_Type, Production_kg, Recycled_Fraction, Region"
    )
    
    if uploaded_file is not None:
        # Show file details
        st.write(f"**File:** {uploaded_file.name}")
        st.write(f"**Size:** {uploaded_file.size} bytes")
        st.write(f"**Type:** {uploaded_file.type}")
        
        # Preview the data
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            st.write("**Data Preview:**")
            st.dataframe(df.head())
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Rows", len(df))
            with col2:
                st.metric("Columns", len(df.columns))
                
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")
            
        # Test file analysis
        if st.button("🔍 Test File Analysis"):
            with st.spinner("Processing uploaded file..."):
                try:
                    # Save uploaded file temporarily
                    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        temp_path = tmp_file.name
                    
                    # Run file analysis
                    result = run_file_analysis(temp_path, "excel" if uploaded_file.name.endswith(('.xlsx', '.xls')) else "csv")
                    
                    # Clean up
                    os.unlink(temp_path)
                    
                    if result.get("success"):
                        st.success("✅ File analysis completed successfully!")
                        
                        # Show results summary
                        summary = result.get("summary", {})
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            lca_summary = summary.get("lca_summary", {})
                            st.metric("Carbon Footprint", f"{lca_summary.get('total_carbon_footprint_kg_co2_eq', 0):,.1f} kg CO₂-eq")
                        
                        with col2:
                            compliance_summary = summary.get("compliance_summary", {})
                            st.metric("Compliance Grade", compliance_summary.get('compliance_grade', 'N/A'))
                        
                        with col3:
                            report_summary = summary.get("report_summary", {})
                            st.metric("Reports Generated", report_summary.get('formats_generated', 0))
                        
                        with st.expander("📊 Complete Analysis Results"):
                            st.json(result)
                            
                    else:
                        st.error(f"❌ File analysis failed: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    st.error(f"❌ Error in file analysis: {str(e)}")
    else:
        # Show sample file format
        st.info("💡 **Sample file format:**")
        sample_df = pd.DataFrame({
            'Metal_Type': ['aluminum', 'steel', 'copper'],
            'Production_kg': [1000, 2000, 500],
            'Recycled_Fraction': [0.3, 0.25, 0.4],
            'Region': ['US_average', 'EU_average', 'China']
        })
        st.dataframe(sample_df)

# Complete LangGraph Workflow Testing
elif test_mode == "Complete LangGraph Workflow":
    st.header("🔄 Complete LCA Analysis with LangGraph Workflow")
    
    st.markdown("Test the entire LangGraph workflow: **Data Ingestion → LCA Analysis → Compliance Check → Report Generation**")
    
    # Input parameters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        metal_type = st.selectbox("Metal Type:", ["steel", "aluminum", "copper", "zinc"])
        production_kg = st.number_input("Production (kg):", min_value=1.0, value=1000.0)
    
    with col2:
        recycled_fraction = st.slider("Recycled Fraction:", 0.0, 1.0, 0.3)
        region = st.selectbox("Region:", ["US_average", "EU_average", "China"])
    
    with col3:
        study_type = st.selectbox("Study Type:", ["internal_decision_support", "comparative_assertion"])
        report_format = st.selectbox("Report Format:", ["pdf", "html", "json", "all"])
    
    if st.button("🚀 Run Complete LangGraph Workflow", type="primary"):
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Results containers
        results_container = st.container()
        
        try:
            # Initialize LCA System with LangGraph
            status_text.text("Initializing LangGraph workflow...")
            progress_bar.progress(10)
            
            lca_system = LCASystem()
            
            # Prepare input data
            input_data = {
                "metal_type": metal_type,
                "production_kg": production_kg,
                "recycled_fraction": recycled_fraction,
                "region": region,
                "study_type": study_type,
                "report_type": "technical",
                "format_type": report_format
            }
            
            # Execute LangGraph workflow
            status_text.text("Executing LangGraph workflow...")
            progress_bar.progress(25)
            
            result = lca_system.run_complete_analysis(input_data)
            
            if not result.get("success"):
                st.error(f"❌ LangGraph workflow failed: {result.get('error')}")
                if result.get("errors"):
                    st.error(f"Errors: {result.get('errors')}")
                st.stop()
            
            progress_bar.progress(100)
            status_text.text("✅ Complete LangGraph workflow executed successfully!")
            
            # Display results
            with results_container:
                st.success("🎉 Complete LCA Analysis with LangGraph Workflow Completed Successfully!")
                
                # Show workflow messages
                workflow_messages = result.get("workflow_messages", [])
                if workflow_messages:
                    with st.expander("📝 Workflow Execution Log"):
                        for msg in workflow_messages:
                            st.write(f"• {msg.get('content', 'No content')}")
                
                # Key metrics
                summary = result.get("summary", {})
                lca_summary = summary.get("lca_summary", {})
                compliance_summary = summary.get("compliance_summary", {})
                report_summary = summary.get("report_summary", {})
                
                # Display key metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "Carbon Footprint", 
                        f"{lca_summary.get('total_carbon_footprint_kg_co2_eq', 0):,.1f} kg CO₂-eq"
                    )
                
                with col2:
                    st.metric(
                        "Compliance Grade", 
                        compliance_summary.get('compliance_grade', 'N/A')
                    )
                
                with col3:
                    st.metric(
                        "Sustainability Score", 
                        f"{lca_summary.get('sustainability_score', 0):.1f}/100"
                    )
                
                with col4:
                    st.metric(
                        "Reports Generated", 
                        report_summary.get('formats_generated', 0)
                    )
                
                # Detailed results
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("🏭 LCA Results")
                    st.write(f"**Carbon Intensity:** {lca_summary.get('carbon_intensity_per_kg', 0):.2f} kg CO₂-eq/kg")
                    st.write(f"**Circularity Index:** {lca_summary.get('circularity_index', 0):.3f}")
                
                with col2:
                    st.subheader("📋 Compliance Status")
                    st.write(f"**Status:** {compliance_summary.get('status', 'Unknown')}")
                    st.write(f"**Score:** {compliance_summary.get('compliance_score', 0):.1%}")
                
                # Generated files
                report_files = report_summary.get('report_files', [])
                if report_files:
                    st.subheader("📁 Generated Reports")
                    for file_path in report_files:
                        if file_path:
                            file_name = Path(file_path).name
                            if Path(file_path).exists():
                                st.write(f"• ✅ {file_name}")
                            else:
                                st.write(f"• ⚠️ {file_name} (path: {file_path})")
                
                # Workflow details
                with st.expander("🔄 LangGraph Workflow Details"):
                    workflow_details = {
                        "Analysis ID": result.get("analysis_id"),
                        "Workflow Status": "Completed Successfully",
                        "Nodes Executed": ["Data Ingestion", "LCA Analysis", "Compliance Check", "Report Generation"],
                        "Total Execution Time": "N/A",
                        "Input Parameters": input_data
                    }
                    st.json(workflow_details)
                
                # Full results (expandable)
                with st.expander("📊 Complete Analysis Results"):
                    st.json(result)
                
        except Exception as e:
            st.error(f"❌ Error in complete LangGraph workflow: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
            progress_bar.progress(0)
            status_text.text("❌ Workflow failed")

# Footer
st.markdown("---")
st.markdown(
    """
    💡 **Tips:** 
    - Make sure your environment variables (CEREBRAS_API_KEY, PINECONE_API_KEY) are set correctly
    - Check the 'Agent Status Check' if you encounter issues
    - Use 'Individual Agents' to test each component separately
    - Try 'File Upload Test' to test with your own data
    - Use 'Complete LangGraph Workflow' to test the full system integration
    """
)

# Add some debug info in sidebar
with st.sidebar:
    st.markdown("---")
    st.subheader("🐛 Debug Info")
    st.write(f"**Python Path:** {sys.path[0]}")
    st.write(f"**Current Dir:** {current_dir}")
    st.write(f"**Agents Available:** {agents_available}")
    
    if st.button("🔄 Refresh Page"):
        st.experimental_rerun()