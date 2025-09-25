"""
Reporting Agent - Generates comprehensive LCA reports and visualizations
Enhanced with Cerebras AI for intelligent insights
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from langchain_cerebras import ChatCerebras
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Image as RLImage

logger = logging.getLogger(__name__)

class ReportingAgent:
    """Enhanced Reporting Agent with AI insights and visualizations"""
    
    def __init__(self, cerebras_api_key: str = None, output_dir: str = None):
        self.cerebras_api_key = cerebras_api_key or os.getenv("CEREBRAS_API_KEY")
        self.llm = ChatCerebras(api_key=self.cerebras_api_key, model="qwen-3-32b") if self.cerebras_api_key else None
        self.output_dir = Path(output_dir) if output_dir else Path("./reports")
        self.output_dir.mkdir(exist_ok=True)
        self.styles = getSampleStyleSheet()
        plt.style.use('default')
        sns.set_palette("husl")
    
    def generate_report(self, lca_results: Dict[str, Any], compliance_results: Dict[str, Any] = None,
                       report_type: str = "technical", format_type: str = "pdf") -> Dict[str, Any]:
        """Generate comprehensive LCA report"""
        try:
            if not lca_results or not lca_results.get("success"):
                return {"error": "Invalid LCA results", "success": False}
            
            # Generate AI insights
            ai_insights = self._generate_ai_insights(lca_results, compliance_results) if self.llm else {}
            
            # Create visualizations
            visualizations = self._create_visualizations(lca_results)
            
            # Generate report content
            content = self._generate_content(lca_results, compliance_results, ai_insights, report_type)
            
            # Generate output files
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_files = {}
            
            if format_type in ["pdf", "all"]:
                output_files["pdf"] = self._generate_pdf(content, visualizations, timestamp)
            if format_type in ["html", "all"]:
                output_files["html"] = self._generate_html(content, visualizations, timestamp)
            if format_type in ["json", "all"]:
                output_files["json"] = self._generate_json(content, lca_results, timestamp)
            
            return {
                "success": True,
                "report_type": report_type,
                "output_files": output_files,
                "visualizations_created": len(visualizations),
                "timestamp": timestamp
            }
            
        except Exception as e:
            logger.error(f"Report generation error: {e}")
            return {"error": str(e), "success": False}
    
    def _generate_ai_insights(self, lca_results: Dict[str, Any], compliance_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI insights for report"""
        try:
            lca_data = lca_results.get("lca_results", {})
            params = lca_data.get("input_parameters", {})
            gwp = lca_data.get("gwp_impact", {})
            
            summary = {
                "metal_type": params.get("metal_type"),
                "production_kg": params.get("production_kg"),
                "recycled_fraction": params.get("recycled_fraction"),
                "total_gwp": gwp.get("total_kg_co2_eq"),
                "gwp_per_kg": gwp.get("kg_co2_eq_per_kg_metal"),
                "compliance_score": compliance_results.get("overall_compliance_score", {}).get("overall_score") if compliance_results else None
            }
            
            system_prompt = """You are an expert LCA consultant. Analyze the LCA results and provide:
            1. Executive summary (2-3 sentences)
            2. Key environmental findings (3-4 points)
            3. Strategic recommendations (3-4 actionable items)
            4. Risk assessment and opportunities
            
            Keep responses concise and professional."""
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Analyze this LCA study: {json.dumps(summary, indent=2)}")
            ]
            
            response = self.llm.invoke(messages)
            analysis = response.content
            
            return {
                "executive_summary": self._extract_section(analysis, "executive summary"),
                "key_findings": self._extract_list_items(analysis, ["finding", "result", "shows"]),
                "recommendations": self._extract_list_items(analysis, ["recommend", "should", "consider"]),
                "full_analysis": analysis
            }
            
        except Exception as e:
            logger.error(f"AI insights error: {e}")
            return {"error": str(e)}
    
    def _extract_section(self, text: str, section_name: str) -> str:
        """Extract specific section from AI response"""
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if section_name.lower() in line.lower():
                # Get next few lines
                return ' '.join(lines[i+1:i+4]).strip()
        return "Analysis summary not available"
    
    def _extract_list_items(self, text: str, keywords: List[str]) -> List[str]:
        """Extract list items containing keywords"""
        items = []
        for line in text.split('\n'):
            line = line.strip()
            if any(keyword in line.lower() for keyword in keywords) and len(line) > 20:
                items.append(line)
        return items[:4]  # Top 4 items
    
    def _create_visualizations(self, lca_results: Dict[str, Any]) -> Dict[str, str]:
        """Create key visualizations"""
        visualizations = {}
        
        try:
            # 1. GWP Breakdown Pie Chart
            visualizations["gwp_breakdown"] = self._create_gwp_chart(lca_results)
            
            # 2. Production Mix Bar Chart
            visualizations["production_mix"] = self._create_production_chart(lca_results)
            
            # 3. Sustainability Score Gauge
            visualizations["sustainability"] = self._create_sustainability_chart(lca_results)
            
        except Exception as e:
            logger.error(f"Visualization error: {e}")
        
        return visualizations
    
    def _create_gwp_chart(self, lca_results: Dict[str, Any]) -> str:
        """Create GWP breakdown pie chart"""
        try:
            emissions = lca_results.get("lca_results", {}).get("total_emissions", {})
            gwp_values = {"CO2": 1.0, "CH4": 25.0, "N2O": 298.0, "CF4": 7390.0}
            
            gwp_data = {}
            for gas, amount in emissions.items():
                if gas in gwp_values and amount > 0:
                    gwp_data[gas] = amount * gwp_values[gas]
            
            if not gwp_data:
                return ""
            
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.pie(gwp_data.values(), labels=gwp_data.keys(), autopct='%1.1f%%', startangle=90)
            ax.set_title('GWP Impact Breakdown', fontsize=14, fontweight='bold')
            
            chart_path = self.output_dir / f"gwp_breakdown_{datetime.now().strftime('%Y%m%d_%H%M')}.png"
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            return str(chart_path)
            
        except Exception:
            return ""
    
    def _create_production_chart(self, lca_results: Dict[str, Any]) -> str:
        """Create production mix bar chart"""
        try:
            breakdown = lca_results.get("lca_results", {}).get("production_breakdown", {})
            primary = breakdown.get("primary_percentage", 0)
            secondary = breakdown.get("secondary_percentage", 0)
            
            fig, ax = plt.subplots(figsize=(8, 6))
            categories = ['Primary', 'Secondary\n(Recycled)']
            values = [primary, secondary]
            colors = ['#FF6B6B', '#4ECDC4']
            
            bars = ax.bar(categories, values, color=colors, alpha=0.8)
            ax.set_ylabel('Percentage (%)')
            ax.set_title('Production Mix', fontsize=14, fontweight='bold')
            ax.set_ylim(0, 110)
            
            for bar, value in zip(bars, values):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
                       f'{value:.1f}%', ha='center', fontweight='bold')
            
            chart_path = self.output_dir / f"production_mix_{datetime.now().strftime('%Y%m%d_%H%M')}.png"
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            return str(chart_path)
            
        except Exception:
            return ""
    
    def _create_sustainability_chart(self, lca_results: Dict[str, Any]) -> str:
        """Create sustainability score gauge"""
        try:
            sustainability = lca_results.get("ai_insights", {}).get("sustainability_score", {})
            score = sustainability.get("overall_score", 0)
            grade = sustainability.get("grade", "N/A")
            
            fig, ax = plt.subplots(figsize=(8, 6))
            
            # Create gauge-like visualization
            sizes = [score, 100-score]
            colors = ['#4ECDC4', '#E8E8E8']
            wedges, _ = ax.pie(sizes, startangle=90, colors=colors, wedgeprops={'width': 0.4})
            
            ax.text(0, 0, f'{score:.1f}', ha='center', va='center', fontsize=24, fontweight='bold')
            ax.text(0, -0.3, f'Grade: {grade}', ha='center', va='center', fontsize=16)
            ax.text(0, 0.3, 'Sustainability Score', ha='center', va='center', fontsize=12)
            
            chart_path = self.output_dir / f"sustainability_{datetime.now().strftime('%Y%m%d_%H%M')}.png"
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            return str(chart_path)
            
        except Exception:
            return ""
    
    def _generate_content(self, lca_results: Dict[str, Any], compliance_results: Dict[str, Any],
                         ai_insights: Dict[str, Any], report_type: str) -> Dict[str, Any]:
        """Generate structured report content"""
        lca_data = lca_results.get("lca_results", {})
        params = lca_data.get("input_parameters", {})
        gwp = lca_data.get("gwp_impact", {})
        
        return {
            "title": f"LCA Report - {params.get('metal_type', 'Metal').title()} Production",
            "date": datetime.now().strftime("%B %d, %Y"),
            "executive_summary": ai_insights.get("executive_summary", "Environmental impact assessment completed."),
            "key_results": [
                f"Production analyzed: {params.get('production_kg', 0):,.0f} kg",
                f"Recycled content: {params.get('recycled_fraction', 0)*100:.1f}%",
                f"Total carbon footprint: {gwp.get('total_kg_co2_eq', 0):,.1f} kg CO2-eq",
                f"Carbon intensity: {gwp.get('kg_co2_eq_per_kg_metal', 0):.2f} kg CO2-eq/kg"
            ],
            "findings": ai_insights.get("key_findings", []),
            "recommendations": ai_insights.get("recommendations", []),
            "compliance_status": compliance_results.get("overall_compliance_score", {}).get("status", "Not assessed") if compliance_results else "Not assessed",
            "sustainability_score": lca_results.get("ai_insights", {}).get("sustainability_score", {}).get("overall_score", 0)
        }
    
    def _generate_pdf(self, content: Dict[str, Any], visualizations: Dict[str, str], timestamp: str) -> str:
        """Generate PDF report"""
        try:
            pdf_path = self.output_dir / f"lca_report_{timestamp}.pdf"
            doc = SimpleDocTemplate(str(pdf_path), pagesize=A4)
            story = []
            
            # Title and date
            story.append(Paragraph(content["title"], self.styles['Title']))
            story.append(Paragraph(f"Generated: {content['date']}", self.styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Executive Summary
            story.append(Paragraph("Executive Summary", self.styles['Heading1']))
            story.append(Paragraph(content["executive_summary"], self.styles['Normal']))
            story.append(Spacer(1, 12))
            
            # Key Results
            story.append(Paragraph("Key Results", self.styles['Heading2']))
            for result in content["key_results"]:
                story.append(Paragraph(f"• {result}", self.styles['Normal']))
            story.append(Spacer(1, 12))
            
            # Findings
            if content["findings"]:
                story.append(Paragraph("Key Findings", self.styles['Heading2']))
                for finding in content["findings"]:
                    story.append(Paragraph(f"• {finding}", self.styles['Normal']))
                story.append(Spacer(1, 12))
            
            # Recommendations
            if content["recommendations"]:
                story.append(Paragraph("Recommendations", self.styles['Heading2']))
                for rec in content["recommendations"]:
                    story.append(Paragraph(f"• {rec}", self.styles['Normal']))
                story.append(Spacer(1, 12))
            
            # Add visualizations
            for viz_name, viz_path in visualizations.items():
                if viz_path and Path(viz_path).exists():
                    try:
                        img = RLImage(viz_path, width=400, height=300)
                        story.append(img)
                        story.append(Spacer(1, 12))
                    except Exception:
                        continue
            
            doc.build(story)
            return str(pdf_path)
            
        except Exception as e:
            logger.error(f"PDF generation error: {e}")
            return ""
    
    def _generate_html(self, content: Dict[str, Any], visualizations: Dict[str, str], timestamp: str) -> str:
        """Generate HTML report"""
        try:
            html_path = self.output_dir / f"lca_report_{timestamp}.html"
            
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{content['title']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
        h1 {{ color: #2E8B57; }}
        h2 {{ color: #4169E1; }}
        .chart {{ text-align: center; margin: 20px 0; }}
        .chart img {{ max-width: 100%; }}
    </style>
</head>
<body>
    <h1>{content['title']}</h1>
    <p><strong>Generated:</strong> {content['date']}</p>
    
    <h2>Executive Summary</h2>
    <p>{content['executive_summary']}</p>
    
    <h2>Key Results</h2>
    <ul>{''.join(f'<li>{result}</li>' for result in content['key_results'])}</ul>
    
    <h2>Visualizations</h2>
"""
            
            for viz_name, viz_path in visualizations.items():
                if viz_path and Path(viz_path).exists():
                    html_content += f'<div class="chart"><img src="{Path(viz_path).name}" alt="{viz_name}"></div>'
            
            html_content += "</body></html>"
            
            with open(html_path, 'w') as f:
                f.write(html_content)
            
            return str(html_path)
            
        except Exception as e:
            logger.error(f"HTML generation error: {e}")
            return ""
    
    def _generate_json(self, content: Dict[str, Any], lca_results: Dict[str, Any], timestamp: str) -> str:
        """Generate JSON data export"""
        try:
            json_path = self.output_dir / f"lca_data_{timestamp}.json"
            
            json_data = {
                "report_metadata": {"timestamp": timestamp, "title": content["title"]},
                "report_content": content,
                "lca_results": lca_results
            }
            
            with open(json_path, 'w') as f:
                json.dump(json_data, f, indent=2, default=str)
            
            return str(json_path)
            
        except Exception as e:
            logger.error(f"JSON generation error: {e}")
            return ""

# Tools
@tool
def generate_lca_report(lca_results: Dict[str, Any], compliance_results: Dict[str, Any] = None,
                       report_type: str = "technical", format_type: str = "pdf") -> Dict[str, Any]:
    """Generate comprehensive LCA report"""
    agent = ReportingAgent()
    return agent.generate_report(lca_results, compliance_results, report_type, format_type)

@tool
def create_lca_visualizations(lca_results: Dict[str, Any]) -> Dict[str, Any]:
    """Create LCA visualizations"""
    agent = ReportingAgent()
    try:
        visualizations = agent._create_visualizations(lca_results)
        return {"success": True, "visualizations": visualizations}
    except Exception as e:
        return {"error": str(e), "success": False}

@tool
def export_lca_data(lca_results: Dict[str, Any], format_type: str = "json") -> Dict[str, Any]:
    """Export LCA data in specified format"""
    agent = ReportingAgent()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if format_type == "json":
        json_path = agent._generate_json({}, lca_results, timestamp)
        return {"success": True, "export_file": json_path}
    elif format_type == "csv":
        try:
            csv_path = agent.output_dir / f"lca_results_{timestamp}.csv"
            lca_data = lca_results.get("lca_results", {})
            
            data = [{
                "metal_type": lca_data.get("input_parameters", {}).get("metal_type"),
                "production_kg": lca_data.get("input_parameters", {}).get("production_kg"),
                "total_gwp": lca_data.get("gwp_impact", {}).get("total_kg_co2_eq"),
                "gwp_per_kg": lca_data.get("gwp_impact", {}).get("kg_co2_eq_per_kg_metal")
            }]
            
            pd.DataFrame(data).to_csv(csv_path, index=False)
            return {"success": True, "export_file": str(csv_path)}
        except Exception as e:
            return {"error": str(e), "success": False}
    else:
        return {"error": f"Unsupported format: {format_type}", "success": False}