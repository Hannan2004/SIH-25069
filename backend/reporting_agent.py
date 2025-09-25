"""
Reporting Agent - Enhanced for comprehensive LCA reports
Works with comprehensive LCA input data format
"""

import logging
import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import io
import base64

# Optional imports with fallbacks
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

logger = logging.getLogger(__name__)

class ReportingAgent:
    """Enhanced Reporting Agent for comprehensive LCA analysis results"""
    
    def __init__(self):
        # Create output directories
        self.output_dir = Path("./output")
        self.reports_dir = self.output_dir / "reports"
        self.charts_dir = self.output_dir / "charts"
        
        for dir_path in [self.output_dir, self.reports_dir, self.charts_dir]:
            dir_path.mkdir(exist_ok=True)
        
        # Configure plot styling if available
        if MATPLOTLIB_AVAILABLE:
            try:
                plt.style.use('seaborn-v0_8')
            except:
                plt.style.use('default')
        
        if MATPLOTLIB_AVAILABLE and 'sns' in globals():
            sns.set_palette("husl")
        
        # Report templates
        self.report_templates = {
            "technical": self._generate_technical_report,
            "executive": self._generate_executive_report,
            "regulatory": self._generate_regulatory_report
        }
    
    def generate_report(self, lca_results: Dict[str, Any], 
                       compliance_results: Dict[str, Any] = None,
                       report_type: str = "technical", 
                       format_type: str = "pdf") -> Dict[str, Any]:
        """Generate comprehensive LCA report"""
        try:
            logger.info(f"Generating {report_type} report in {format_type} format")
            
            # Extract data from results
            report_data = self._extract_report_data(lca_results, compliance_results)
            
            # Generate visualizations
            charts = self._create_visualizations(report_data)
            
            # Generate report content
            report_generator = self.report_templates.get(report_type, self._generate_technical_report)
            report_content = report_generator(report_data, charts)
            
            # Create output files
            output_files = {}
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if format_type in ["pdf", "all"]:
                pdf_path = self._create_pdf_report(report_content, report_type, timestamp)
                if pdf_path:
                    output_files["pdf"] = pdf_path
            
            if format_type in ["html", "all"]:
                html_path = self._create_html_report(report_content, charts, report_type, timestamp)
                output_files["html"] = html_path
            
            if format_type in ["json", "all"]:
                json_path = self._create_json_report(report_data, report_type, timestamp)
                output_files["json"] = json_path
            
            return {
                "success": True,
                "report_type": report_type,
                "format_type": format_type,
                "output_files": output_files,
                "charts_created": list(charts.keys()),
                "visualizations_created": len(charts),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Report generation error: {e}")
            return {"error": str(e), "success": False}
    
    def _extract_report_data(self, lca_results: Dict[str, Any], 
                           compliance_results: Dict[str, Any] = None) -> Dict[str, Any]:
        """Extract and structure data for reporting"""
        
        # Handle different LCA result structures
        lca_data = lca_results.get("lca_results", lca_results)
        scenarios = lca_results.get("scenario_results", [])
        input_params = lca_results.get("input_parameters", {})
        
        # Extract key metrics
        gwp_impact = lca_data.get("gwp_impact", {})
        emissions_breakdown = lca_data.get("emissions_breakdown", {})
        circularity = lca_data.get("circularity_metrics", {})
        
        # Extract material information
        materials_info = []
        if scenarios:
            for scenario in scenarios:
                materials_info.append({
                    "material": scenario.get("material_type", "unknown"),
                    "mass_kg": scenario.get("mass_kg", 0),
                    "emissions_kg_co2e": scenario.get("total_emissions", {}).get("total_kg_co2e", 0),
                    "circularity_index": scenario.get("circularity_metrics", {}).get("circularity_index", 0)
                })
        elif input_params.get("scenarios"):
            for scenario in input_params["scenarios"]:
                materials_info.append({
                    "material": scenario.get("material_type", "unknown"),
                    "mass_kg": scenario.get("mass_kg", 0),
                    "emissions_kg_co2e": 0,  # Will be calculated
                    "circularity_index": scenario.get("recycling", {}).get("secondary_content_existing_pct", 0) / 100
                })
        
        return {
            "analysis_info": {
                "timestamp": lca_results.get("timestamp", datetime.now().isoformat()),
                "analysis_type": lca_results.get("analysis_type", "cradle_to_gate"),
                "study_type": input_params.get("study_type", "internal_decision_support"),
                "scenarios_count": len(scenarios) or len(input_params.get("scenarios", []))
            },
            "materials_info": materials_info,
            "carbon_footprint": {
                "total_kg_co2e": gwp_impact.get("total_kg_co2_eq", 0),
                "per_kg_material": gwp_impact.get("kg_co2_eq_per_kg_material", 0)
            },
            "emissions_breakdown": emissions_breakdown,
            "circularity_metrics": circularity,
            "sustainability_score": lca_results.get("ai_insights", {}).get("sustainability_score", {}),
            "compliance_summary": self._extract_compliance_summary(compliance_results) if compliance_results else None,
            "recommendations": lca_results.get("ai_insights", {}).get("key_recommendations", [])
        }
    
    def _extract_compliance_summary(self, compliance_results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract compliance summary for reporting"""
        if not compliance_results or not compliance_results.get("success"):
            return None
        
        overall_score = compliance_results.get("overall_compliance_score", {})
        return {
            "overall_score": overall_score.get("overall_score", 0),
            "grade": overall_score.get("grade", "N/A"),
            "status": overall_score.get("status", "Unknown"),
            "study_type": compliance_results.get("study_type", "unknown")
        }
    
    def _create_visualizations(self, report_data: Dict[str, Any]) -> Dict[str, str]:
        """Create visualizations for the report"""
        charts = {}
        
        try:
            # 1. Emissions Breakdown Pie Chart
            emissions = report_data["emissions_breakdown"]
            if emissions and any(emissions.values()) and MATPLOTLIB_AVAILABLE:
                charts["emissions_pie"] = self._create_emissions_pie_chart(emissions)
            
            # 2. Carbon Footprint Bar Chart (if multiple materials)
            materials = report_data["materials_info"]
            if len(materials) > 1 and MATPLOTLIB_AVAILABLE:
                charts["materials_bar"] = self._create_materials_comparison_chart(materials)
            
            # 3. Circularity Index Chart
            circularity = report_data["circularity_metrics"]
            if circularity and PLOTLY_AVAILABLE:
                charts["circularity_gauge"] = self._create_circularity_gauge(circularity)
            
            # 4. Sustainability Score Chart
            sustainability = report_data["sustainability_score"]
            if sustainability and PLOTLY_AVAILABLE:
                charts["sustainability_radar"] = self._create_sustainability_radar(sustainability)
            
        except Exception as e:
            logger.error(f"Visualization creation error: {e}")
        
        return charts
    
    def _create_emissions_pie_chart(self, emissions: Dict[str, float]) -> str:
        """Create emissions breakdown pie chart"""
        if not MATPLOTLIB_AVAILABLE:
            return None
            
        # Filter out zero values
        filtered_emissions = {k: v for k, v in emissions.items() if v > 0 and k != "total_kg_co2e"}
        
        if not filtered_emissions:
            return None
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        labels = [k.replace("_kg_co2e", "").replace("_", " ").title() for k in filtered_emissions.keys()]
        values = list(filtered_emissions.values())
        colors = plt.cm.Set3(range(len(labels)))
        
        wedges, texts, autotexts = ax.pie(values, labels=labels, autopct='%1.1f%%', 
                                         colors=colors, startangle=90)
        
        ax.set_title("Emissions Breakdown by Category", fontsize=16, fontweight='bold')
        
        # Save chart
        chart_path = self.charts_dir / f"emissions_breakdown_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(chart_path)
    
    def _create_materials_comparison_chart(self, materials: List[Dict[str, Any]]) -> str:
        """Create materials comparison bar chart"""
        if not MATPLOTLIB_AVAILABLE or len(materials) < 2:
            return None
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Emissions comparison
        materials_names = [m["material"].title() for m in materials]
        emissions = [m["emissions_kg_co2e"] for m in materials]
        
        bars1 = ax1.bar(materials_names, emissions, color='steelblue', alpha=0.7)
        ax1.set_title("Carbon Footprint by Material", fontweight='bold')
        ax1.set_ylabel("kg CO₂-eq")
        ax1.tick_params(axis='x', rotation=45)
        
        # Add value labels on bars
        for bar, value in zip(bars1, emissions):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(emissions)*0.01,
                    f'{value:.1f}', ha='center', va='bottom')
        
        # Circularity comparison
        circularity = [m["circularity_index"] for m in materials]
        bars2 = ax2.bar(materials_names, circularity, color='green', alpha=0.7)
        ax2.set_title("Circularity Index by Material", fontweight='bold')
        ax2.set_ylabel("Circularity Index")
        ax2.set_ylim(0, 1)
        ax2.tick_params(axis='x', rotation=45)
        
        # Add value labels on bars
        for bar, value in zip(bars2, circularity):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                    f'{value:.2f}', ha='center', va='bottom')
        
        plt.tight_layout()
        
        # Save chart
        chart_path = self.charts_dir / f"materials_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(chart_path)
    
    def _create_circularity_gauge(self, circularity: Dict[str, Any]) -> str:
        """Create circularity gauge chart"""
        if not PLOTLY_AVAILABLE:
            return None
            
        index = circularity.get("circularity_index", circularity.get("weighted_circularity_index", 0))
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = index,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Circularity Index"},
            delta = {'reference': 0.5},
            gauge = {
                'axis': {'range': [None, 1]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 0.25], 'color': "lightgray"},
                    {'range': [0.25, 0.5], 'color': "yellow"},
                    {'range': [0.5, 0.75], 'color': "orange"},
                    {'range': [0.75, 1], 'color': "green"}],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 0.8}}))
        
        # Save chart
        chart_path = self.charts_dir / f"circularity_gauge_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        try:
            fig.write_image(chart_path, width=800, height=600)
            return str(chart_path)
        except:
            # Fallback if image export fails
            return None
    
    def _create_sustainability_radar(self, sustainability: Dict[str, Any]) -> str:
        """Create sustainability radar chart"""
        if not PLOTLY_AVAILABLE:
            return None
            
        categories = ['Overall Score', 'Emission Score', 'Circularity Score']
        values = [
            sustainability.get("overall_score", 0),
            sustainability.get("emission_score", 0),
            sustainability.get("circularity_score", 0)
        ]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='Sustainability Metrics'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )),
            showlegend=True,
            title="Sustainability Assessment"
        )
        
        # Save chart
        chart_path = self.charts_dir / f"sustainability_radar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        try:
            fig.write_image(chart_path, width=800, height=600)
            return str(chart_path)
        except:
            # Fallback if image export fails
            return None
    
    def _generate_technical_report(self, report_data: Dict[str, Any], 
                                 charts: Dict[str, str]) -> Dict[str, Any]:
        """Generate technical report content"""
        analysis_info = report_data["analysis_info"]
        carbon_footprint = report_data["carbon_footprint"]
        materials = report_data["materials_info"]
        
        return {
            "title": "Technical Life Cycle Assessment Report",
            "sections": [
                {
                    "title": "Executive Summary",
                    "content": f"""
                    This technical LCA report presents a comprehensive analysis of {len(materials)} material scenario(s) 
                    using {analysis_info['analysis_type']} methodology. The total carbon footprint is 
                    {carbon_footprint['total_kg_co2e']:.1f} kg CO₂-eq with an intensity of 
                    {carbon_footprint['per_kg_material']:.2f} kg CO₂-eq per kg of material.
                    """
                },
                {
                    "title": "Methodology",
                    "content": f"""
                    Analysis Type: {analysis_info['analysis_type'].replace('_', ' ').title()}
                    Study Type: {analysis_info['study_type'].replace('_', ' ').title()}
                    Standards: ISO 14040/14044
                    Scenarios Analyzed: {analysis_info['scenarios_count']}
                    """
                },
                {
                    "title": "Results",
                    "content": self._format_technical_results(report_data)
                },
                {
                    "title": "Environmental Impact Assessment",
                    "content": self._format_environmental_impacts(report_data)
                },
                {
                    "title": "Recommendations",
                    "content": "\n".join([f"• {rec}" for rec in report_data.get("recommendations", [])])
                }
            ],
            "charts": charts
        }
    
    def _generate_executive_report(self, report_data: Dict[str, Any], 
                                 charts: Dict[str, str]) -> Dict[str, Any]:
        """Generate executive summary report"""
        carbon_footprint = report_data["carbon_footprint"]
        sustainability = report_data["sustainability_score"]
        
        return {
            "title": "Executive Summary - LCA Analysis",
            "sections": [
                {
                    "title": "Key Findings",
                    "content": f"""
                    • Total Carbon Footprint: {carbon_footprint['total_kg_co2e']:.1f} kg CO₂-eq
                    • Carbon Intensity: {carbon_footprint['per_kg_material']:.2f} kg CO₂-eq/kg
                    • Sustainability Grade: {sustainability.get('grade', 'N/A')}
                    • Overall Score: {sustainability.get('overall_score', 0):.1f}/100
                    """
                },
                {
                    "title": "Business Impact",
                    "content": "Environmental performance assessment with actionable insights for sustainability improvement."
                },
                {
                    "title": "Strategic Recommendations",
                    "content": "\n".join([f"• {rec}" for rec in report_data.get("recommendations", [])[:3]])
                }
            ],
            "charts": {k: v for k, v in charts.items() if k in ["emissions_pie", "sustainability_radar"]}
        }
    
    def _generate_regulatory_report(self, report_data: Dict[str, Any], 
                                  charts: Dict[str, str]) -> Dict[str, Any]:
        """Generate regulatory compliance report"""
        compliance = report_data["compliance_summary"]
        
        compliance_content = "Compliance assessment not available"
        if compliance:
            compliance_content = f"""
            ISO 14040/14044 Compliance: {compliance.get('status', 'Unknown')}
            Compliance Score: {compliance.get('overall_score', 0):.1%}
            Grade: {compliance.get('grade', 'N/A')}
            """
        
        return {
            "title": "Regulatory Compliance Report",
            "sections": [
                {
                    "title": "Compliance Status",
                    "content": compliance_content
                },
                {
                    "title": "Technical Specifications",
                    "content": self._format_technical_results(report_data)
                },
                {
                    "title": "Quality Assurance",
                    "content": "Analysis conducted following ISO 14040/14044 methodology and standards."
                }
            ],
            "charts": charts
        }
    
    def _format_technical_results(self, report_data: Dict[str, Any]) -> str:
        """Format technical results section"""
        emissions = report_data["emissions_breakdown"]
        circularity = report_data["circularity_metrics"]
        
        result_text = f"""
        Carbon Footprint Breakdown:
        • Production: {emissions.get('production_kg_co2e', 0):.1f} kg CO₂-eq
        • Energy: {emissions.get('energy_kg_co2e', 0):.1f} kg CO₂-eq
        • Transport: {emissions.get('transport_kg_co2e', 0):.1f} kg CO₂-eq
        • End-of-Life: {emissions.get('end_of_life_kg_co2e', 0):.1f} kg CO₂-eq
        
        Circularity Metrics:
        • Circularity Index: {circularity.get('circularity_index', circularity.get('weighted_circularity_index', 0)):.3f}
        • Grade: {circularity.get('circularity_grade', 'N/A')}
        """
        
        return result_text.strip()
    
    def _format_environmental_impacts(self, report_data: Dict[str, Any]) -> str:
        """Format environmental impacts section"""
        materials = report_data["materials_info"]
        total_mass = sum(m["mass_kg"] for m in materials)
        
        return f"""
        Materials Analyzed: {', '.join(set(m['material'].title() for m in materials))}
        Total Mass: {total_mass:.1f} kg
        Average Carbon Intensity: {report_data['carbon_footprint']['per_kg_material']:.2f} kg CO₂-eq/kg
        Environmental Category: Climate Change (GWP 100-year)
        """
    
    def _create_pdf_report(self, report_content: Dict[str, Any], 
                          report_type: str, timestamp: str) -> str:
        """Create PDF report"""
        if not REPORTLAB_AVAILABLE:
            logger.warning("ReportLab not available, skipping PDF generation")
            return None
            
        filename = f"{report_type}_report_{timestamp}.pdf"
        filepath = self.reports_dir / filename
        
        try:
            doc = SimpleDocTemplate(str(filepath), pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            story.append(Paragraph(report_content["title"], styles['Title']))
            story.append(Spacer(1, 12))
            
            # Sections
            for section in report_content["sections"]:
                story.append(Paragraph(section["title"], styles['Heading2']))
                story.append(Spacer(1, 6))
                story.append(Paragraph(section["content"], styles['Normal']))
                story.append(Spacer(1, 12))
            
            doc.build(story)
            return str(filepath)
        except Exception as e:
            logger.error(f"PDF generation error: {e}")
            return None
    
    def _create_html_report(self, report_content: Dict[str, Any], 
                           charts: Dict[str, str], report_type: str, timestamp: str) -> str:
        """Create HTML report"""
        filename = f"{report_type}_report_{timestamp}.html"
        filepath = self.reports_dir / filename
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{report_content['title']}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1 {{ color: #2c3e50; }}
                h2 {{ color: #34495e; }}
                .chart {{ margin: 20px 0; }}
            </style>
        </head>
        <body>
            <h1>{report_content['title']}</h1>
        """
        
        for section in report_content["sections"]:
            html_content += f"""
            <h2>{section['title']}</h2>
            <p>{section['content'].replace(chr(10), '<br>')}</p>
            """
        
        # Add charts
        for chart_name, chart_path in charts.items():
            if chart_path and Path(chart_path).exists():
                html_content += f'<div class="chart"><img src="{chart_path}" alt="{chart_name}" style="max-width: 100%;"></div>'
        
        html_content += "</body></html>"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(filepath)
    
    def _create_json_report(self, report_data: Dict[str, Any], 
                           report_type: str, timestamp: str) -> str:
        """Create JSON report"""
        filename = f"{report_type}_report_{timestamp}.json"
        filepath = self.reports_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        return str(filepath)