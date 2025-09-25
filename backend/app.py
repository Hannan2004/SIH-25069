"""
Simple Streamlit App to test LCA Analysis System
Tests all 4 agents: LCA, Data Quality, Compliance, and Reporting
"""

import streamlit as st
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add current directory to path for imports
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

# Import your agents
try:
    from lca_agent import LCAAgent
    from data_quality_agent import DataQualityAgent
    from compliance_agent import ComplianceAgent
    from reporting_agent import ReportingAgent
    from main import LCASystem, run_quick_lca_analysis
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

# Title and description
st.title("🌍 LCA Analysis System Test App")
st.markdown("Test your LCA agents individually or run complete analysis workflow")

# Sidebar for navigation
st.sidebar.title("🧪 Test Options")
test_mode = st.sidebar.selectbox(
    "Select Test Mode:",
    ["Complete Workflow", "Individual Agents", "Agent Status Check"]
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
        except Exception as e:
            agents_status["LCA Agent"] = f"❌ Error: {str(e)[:50]}..."
            st.error(f"❌ Error: {str(e)[:50]}...")
    
    with col2:
        st.subheader("Data Quality Agent")
        try:
            dq_agent = DataQualityAgent()
            agents_status["Data Quality Agent"] = "✅ Ready"
            st.success("✅ Ready")
        except Exception as e:
            agents_status["Data Quality Agent"] = f"❌ Error: {str(e)[:50]}..."
            st.error(f"❌ Error: {str(e)[:50]}...")
    
    with col3:
        st.subheader("Compliance Agent")
        try:
            compliance_agent = ComplianceAgent()
            agents_status["Compliance Agent"] = "✅ Ready"
            st.success("✅ Ready")
        except Exception as e:
            agents_status["Compliance Agent"] = f"❌ Error: {str(e)[:50]}..."
            st.error(f"❌ Error: {str(e)[:50]}...")
    
    with col4:
        st.subheader("Reporting Agent")
        try:
            reporting_agent = ReportingAgent()
            agents_status["Reporting Agent"] = "✅ Ready"
            st.success("✅ Ready")
        except Exception as e:
            agents_status["Reporting Agent"] = f"❌ Error: {str(e)[:50]}..."
            st.error(f"❌ Error: {str(e)[:50]}...")
    
    # Environment check
    st.header("🔧 Environment Check")
    env_status = {}
    
    env_vars = ["CEREBRAS_API_KEY", "PINECONE_API_KEY", "PINECONE_ENVIRONMENT"]
    for var in env_vars:
        value = os.getenv(var)
        if value:
            env_status[var] = "✅ Set"
            st.success(f"✅ {var}: Set")
        else:
            env_status[var] = "⚠️ Not set"
            st.warning(f"⚠️ {var}: Not set")
    
    # Summary
    st.header("📊 Status Summary")
    st.json({**agents_status, **env_status})

# Individual Agent Testing
elif test_mode == "Individual Agents":
    st.header("🧪 Individual Agent Testing")
    
    agent_choice = st.selectbox(
        "Select Agent to Test:",
        ["LCA Agent", "Data Quality Agent", "Compliance Agent", "Reporting Agent"]
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
                    result = lca_agent.calculate_metal_lca(
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
    
    elif agent_choice == "Data Quality Agent":
        st.subheader("📊 Data Quality Agent Test")
        
        # Create sample LCA data for testing
        sample_data = {
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
                }
            },
            "data_sources": ["EcoInvent", "GREET"],
            "temporal_coverage": "2020-2023",
            "geographical_coverage": "Global"
        }
        
        if st.button("🔍 Test Data Quality Agent"):
            with st.spinner("Assessing data quality..."):
                try:
                    dq_agent = DataQualityAgent()
                    result = dq_agent.assess_data_quality(sample_data)
                    
                    if result.get("success"):
                        st.success("✅ Data Quality Agent working correctly!")
                        
                        # Display key metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Overall Score", f"{result.get('overall_quality_score', 0):.1%}")
                        with col2:
                            st.metric("Completeness", f"{result.get('completeness_score', 0):.1%}")
                        with col3:
                            st.metric("Issues Found", len(result.get('issues', [])))
                        
                        # Show issues if any
                        issues = result.get('issues', [])
                        if issues:
                            st.warning("⚠️ Data Quality Issues Found:")
                            for issue in issues[:5]:  # Show first 5 issues
                                st.write(f"• {issue}")
                        
                        with st.expander("📋 Detailed Assessment"):
                            st.json(result)
                    else:
                        st.error(f"❌ Data Quality Agent failed: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    st.error(f"❌ Error testing Data Quality Agent: {str(e)}")
    
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
                            st.text_area("📄 Compliance Report", compliance_report, height=300)
                        
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
                                if file_path:
                                    st.write(f"• {format_name.upper()}: {Path(file_path).name}")
                        
                        with st.expander("📋 Report Generation Details"):
                            st.json(result)
                    else:
                        st.error(f"❌ Reporting Agent failed: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    st.error(f"❌ Error testing Reporting Agent: {str(e)}")

# Complete Workflow Testing
elif test_mode == "Complete Workflow":
    st.header("🔄 Complete LCA Analysis Workflow Test")
    
    st.markdown("Test the entire workflow: LCA → Data Quality → Compliance → Reporting")
    
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
    
    if st.button("🚀 Run Complete Analysis", type="primary"):
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Results containers
        results_container = st.container()
        
        try:
            # Step 1: LCA Calculation
            status_text.text("Step 1/4: Running LCA calculations...")
            progress_bar.progress(25)
            
            result = run_quick_lca_analysis(
                metal_type=metal_type,
                production_kg=production_kg,
                recycled_fraction=recycled_fraction
            )
            
            if not result.get("success"):
                st.error(f"❌ Workflow failed at LCA step: {result.get('error')}")
                st.stop()
            
            status_text.text("Step 2/4: Assessing data quality...")
            progress_bar.progress(50)
            
            status_text.text("Step 3/4: Checking compliance...")
            progress_bar.progress(75)
            
            status_text.text("Step 4/4: Generating reports...")
            progress_bar.progress(100)
            
            # Success!
            status_text.text("✅ Complete workflow executed successfully!")
            
            # Display results
            with results_container:
                st.success("🎉 Complete LCA Analysis Workflow Completed Successfully!")
                
                # Key metrics
                summary = result.get("summary", {})
                lca_summary = summary.get("lca_summary", {})
                compliance_summary = summary.get("compliance_summary", {})
                data_quality_summary = summary.get("data_quality_summary", {})
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
                        "Data Quality", 
                        f"{data_quality_summary.get('overall_score', 0):.1%}"
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
                    st.write(f"**Sustainability Score:** {lca_summary.get('sustainability_score', 0):.1f}/100")
                
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
                            st.write(f"• {Path(file_path).name}")
                
                # Full results (expandable)
                with st.expander("📊 Complete Analysis Results"):
                    st.json(result)
                
        except Exception as e:
            st.error(f"❌ Error in complete workflow: {str(e)}")
            progress_bar.progress(0)
            status_text.text("❌ Workflow failed")

# Footer
st.markdown("---")
st.markdown(
    "💡 **Tips:** Make sure your environment variables are set correctly. "
    "Check the 'Agent Status Check' if you encounter issues."
)