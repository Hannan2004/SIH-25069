"""
Data Ingestion Agent
Handles CSV/Excel input data, missing value imputation, and preprocessing
"""

from typing import Dict, List, Optional, Any, Union
import pandas as pd
import numpy as np
import logging
import os
from pathlib import Path
import json
from datetime import datetime

from langchain_core.tools import tool
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import PromptTemplate

# Import for Cerebras
from langchain_cerebras import ChatCerebras

logger = logging.getLogger(__name__)

class DataIngestionAgent:
    """Agent responsible for data ingestion, cleaning, and preprocessing"""
    
    def __init__(self, cerebras_api_key: str = None):
        # Initialize ChatCerebras
        self.cerebras_api_key = cerebras_api_key or os.getenv("CEREBRAS_API_KEY")
        self.llm = ChatCerebras(
            api_key=self.cerebras_api_key,
            model="qwen-3-32b",
        ) if self.cerebras_api_key else None
        
        self.supported_formats = ['.csv', '.xlsx', '.xls']
        self.required_columns = {
            'metal_type': ['metal_type', 'metal', 'material_type', 'material'],
            'production_kg': ['production_kg', 'quantity_kg', 'mass_kg', 'weight_kg', 'production_quantity', 'quantity'],
            'recycled_fraction': ['recycled_fraction', 'recycled_content', 'secondary_content', 'recycling_rate'],
            'region': ['region', 'location', 'state', 'area', 'geographic_region'],
            'product_type': ['product_type', 'product', 'application', 'end_use']
        }
        
    def ingest_data(self, file_path: str, sheet_name: str = None) -> Dict[str, Any]:
        """
        Ingest data from CSV/Excel file with AI insights
        
        Args:
            file_path (str): Path to the data file
            sheet_name (str): Excel sheet name (if applicable)
            
        Returns:
            Dict: Ingestion results with data and AI insights
        """
        
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return {"error": f"File not found: {file_path}", "success": False}
            
            if file_path.suffix not in self.supported_formats:
                return {"error": f"Unsupported file format: {file_path.suffix}", "success": False}
            
            # Read data based on file type
            if file_path.suffix == '.csv':
                raw_data = pd.read_csv(file_path, encoding='utf-8')
            else:  # Excel files
                raw_data = pd.read_excel(file_path, sheet_name=sheet_name)
            
            logger.info(f"Successfully loaded {len(raw_data)} rows from {file_path}")
            
            # Initial data assessment
            data_assessment = self._assess_data_quality(raw_data)
            
            # Generate AI insights if LLM is available
            ai_insights = self._generate_ai_insights(raw_data, data_assessment) if self.llm else {}
            
            return {
                "success": True,
                "raw_data": raw_data,
                "data_assessment": data_assessment,
                "ai_insights": ai_insights,
                "file_info": {
                    "file_path": str(file_path),
                    "file_name": file_path.name,
                    "file_size_mb": round(file_path.stat().st_size / (1024 * 1024), 2),
                    "rows": len(raw_data),
                    "columns": len(raw_data.columns),
                    "ingestion_timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error ingesting data from {file_path}: {e}")
            return {"error": str(e), "success": False}
    
    def _assess_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Assess data quality and identify issues"""
        
        assessment = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "missing_values": {},
            "column_mapping": {},
            "data_types": {},
            "quality_score": 0.0,
            "issues": [],
            "column_statistics": {}
        }
        
        # Check missing values
        for col in df.columns:
            missing_count = df[col].isnull().sum()
            missing_pct = (missing_count / len(df)) * 100
            assessment["missing_values"][col] = {
                "count": int(missing_count),
                "percentage": round(missing_pct, 2)
            }
            
            if missing_pct > 50:
                assessment["issues"].append(f"Column '{col}' has {missing_pct:.1f}% missing values")
            elif missing_pct > 20:
                assessment["issues"].append(f"Column '{col}' has moderate missing values ({missing_pct:.1f}%)")
        
        # Check data types and basic statistics
        for col in df.columns:
            dtype = str(df[col].dtype)
            assessment["data_types"][col] = dtype
            
            # Basic statistics for numeric columns
            if df[col].dtype in ['int64', 'float64']:
                assessment["column_statistics"][col] = {
                    "mean": float(df[col].mean()) if not df[col].empty else 0,
                    "std": float(df[col].std()) if not df[col].empty else 0,
                    "min": float(df[col].min()) if not df[col].empty else 0,
                    "max": float(df[col].max()) if not df[col].empty else 0,
                    "unique_values": int(df[col].nunique())
                }
            else:
                assessment["column_statistics"][col] = {
                    "unique_values": int(df[col].nunique()),
                    "most_common": str(df[col].mode().iloc[0]) if not df[col].mode().empty else "N/A"
                }
        
        # Map columns to required fields
        assessment["column_mapping"] = self._map_columns(df.columns.tolist())
        
        # Calculate quality score
        mapped_required = sum(1 for v in assessment["column_mapping"].values() if v is not None)
        total_required = len(self.required_columns)
        missing_pct_avg = np.mean([v["percentage"] for v in assessment["missing_values"].values()])
        
        assessment["quality_score"] = (mapped_required / total_required) * (1 - missing_pct_avg / 100)
        
        # Additional quality checks
        self._additional_quality_checks(df, assessment)
        
        return assessment
    
    def _map_columns(self, columns: List[str]) -> Dict[str, Optional[str]]:
        """Map input columns to required fields with AI assistance"""
        
        # First try rule-based mapping
        column_mapping = {}
        columns_lower = [col.lower().replace(' ', '_').replace('-', '_') for col in columns]
        
        for required_field, possible_names in self.required_columns.items():
            mapped_column = None
            
            for possible_name in possible_names:
                possible_name_normalized = possible_name.lower().replace(' ', '_').replace('-', '_')
                if possible_name_normalized in columns_lower:
                    idx = columns_lower.index(possible_name_normalized)
                    mapped_column = columns[idx]
                    break
                
                # Partial matching
                for i, col_norm in enumerate(columns_lower):
                    if possible_name_normalized in col_norm or col_norm in possible_name_normalized:
                        mapped_column = columns[i]
                        break
                
                if mapped_column:
                    break
            
            column_mapping[required_field] = mapped_column
        
        # AI-enhanced mapping for unmapped fields
        if self.llm:
            unmapped_fields = [field for field, mapped_col in column_mapping.items() if mapped_col is None]
            
            if unmapped_fields:
                try:
                    system_prompt = """You are a data mapping expert for LCA analysis. 
                    Map column names to required LCA fields. Return only JSON format:
                    {"required_field": "column_name" or null}
                    
                    Required fields:
                    - metal_type: Type of metal (aluminum, copper, etc.)
                    - production_kg: Production quantity in kg
                    - recycled_fraction: Fraction of recycled content (0-1)
                    - region: Geographic region
                    - product_type: Type of product being produced
                    
                    Be conservative - only map if confident about the match."""
                    
                    user_message = f"Available columns: {columns}\nUnmapped fields: {unmapped_fields}"
                    
                    messages = [
                        SystemMessage(content=system_prompt),
                        HumanMessage(content=user_message)
                    ]
                    
                    response = self.llm.invoke(messages)
                    ai_mapping = json.loads(response.content)
                    
                    # Update mapping with AI suggestions
                    for field, suggested_column in ai_mapping.items():
                        if field in unmapped_fields and suggested_column in columns:
                            column_mapping[field] = suggested_column
                            logger.info(f"AI mapped '{field}' to '{suggested_column}'")
                            
                except Exception as e:
                    logger.warning(f"AI column mapping failed: {e}")
        
        return column_mapping
    
    def _additional_quality_checks(self, df: pd.DataFrame, assessment: Dict[str, Any]):
        """Additional data quality checks"""
        
        # Check for duplicate rows
        duplicate_count = df.duplicated().sum()
        if duplicate_count > 0:
            assessment["issues"].append(f"Found {duplicate_count} duplicate rows")
        
        # Check for outliers in numeric columns
        for col in df.select_dtypes(include=[np.number]).columns:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            outliers = df[(df[col] < (Q1 - 1.5 * IQR)) | (df[col] > (Q3 + 1.5 * IQR))]
            
            if len(outliers) > len(df) * 0.05:  # More than 5% outliers
                assessment["issues"].append(f"Column '{col}' has {len(outliers)} potential outliers")
    
    def _generate_ai_insights(self, df: pd.DataFrame, assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI-powered data quality insights"""
        
        if not self.llm:
            return {"error": "AI insights not available - LLM not configured"}
        
        try:
            # Prepare data summary for AI
            data_summary = {
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": df.columns.tolist()[:10],  # First 10 columns
                "missing_data_percentage": np.mean([v["percentage"] for v in assessment["missing_values"].values()]),
                "quality_score": assessment["quality_score"],
                "top_issues": assessment["issues"][:5],  # Top 5 issues
                "mapped_fields": {k: v for k, v in assessment["column_mapping"].items() if v is not None}
            }
            
            system_prompt = """You are an expert data analyst specializing in LCA (Life Cycle Assessment) data quality.
            Analyze the provided data summary and provide insights on:
            
            1. Overall data quality assessment
            2. Potential data preprocessing challenges
            3. Recommendations for handling missing values
            4. Suggestions for data validation and cleaning
            5. Assessment of data completeness for LCA analysis
            
            Focus on practical, actionable recommendations for improving data quality for carbon footprint calculations.
            Keep response concise and structured."""
            
            user_message = f"Analyze this LCA dataset summary: {json.dumps(data_summary, indent=2)}"
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_message)
            ]
            
            response = self.llm.invoke(messages)
            ai_analysis = response.content
            
            # Generate specific recommendations
            recommendations = self._generate_preprocessing_recommendations(df, assessment)
            
            return {
                "ai_analysis": ai_analysis,
                "preprocessing_recommendations": recommendations,
                "data_readiness_score": self._calculate_data_readiness_score(assessment),
                "critical_issues": [issue for issue in assessment["issues"] if "missing" in issue.lower()],
                "suggested_actions": self._extract_ai_recommendations(ai_analysis)
            }
            
        except Exception as e:
            logger.error(f"Error generating AI insights: {e}")
            return {"error": f"Failed to generate AI insights: {str(e)}"}
    
    def _calculate_data_readiness_score(self, assessment: Dict[str, Any]) -> float:
        """Calculate data readiness score for LCA analysis"""
        quality_score = assessment.get("quality_score", 0)
        issue_penalty = len(assessment.get("issues", [])) * 0.05
        return max(0, min(1, quality_score - issue_penalty))
    
    def _extract_ai_recommendations(self, ai_response: str) -> List[str]:
        """Extract actionable recommendations from AI response"""
        recommendations = []
        lines = ai_response.split('\n')
        for line in lines:
            line = line.strip()
            if line and any(keyword in line.lower() for keyword in ['recommend', 'suggest', 'should', 'consider']):
                recommendations.append(line)
        return recommendations[:5]  # Top 5 recommendations
    
    def _generate_preprocessing_recommendations(self, df: pd.DataFrame, assessment: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate specific preprocessing recommendations"""
        
        recommendations = []
        
        # Missing value recommendations
        for col, missing_info in assessment["missing_values"].items():
            if missing_info["percentage"] > 20:
                if col in ['metal_type', 'product_type']:
                    recommendations.append({
                        "type": "missing_values",
                        "column": col,
                        "action": "Use mode imputation or categorical inference",
                        "priority": "high"
                    })
                elif col in ['production_kg', 'recycled_fraction']:
                    recommendations.append({
                        "type": "missing_values",
                        "column": col,
                        "action": "Use median imputation by metal type or industry averages",
                        "priority": "high"
                    })
        
        # Data type recommendations
        for col, dtype in assessment["data_types"].items():
            if col in ['production_kg', 'recycled_fraction'] and dtype not in ['int64', 'float64']:
                recommendations.append({
                    "type": "data_types",
                    "column": col,
                    "action": "Convert to numeric type",
                    "priority": "medium"
                })
        
        return recommendations
        
    def preprocess_data(self, raw_data: pd.DataFrame, 
                       column_mapping: Dict[str, str],
                       missing_value_strategy: str = "intelligent") -> Dict[str, Any]:
        """
        Preprocess data with missing value handling
        
        Args:
            raw_data (pd.DataFrame): Raw input data
            column_mapping (Dict): Mapping of required fields to actual columns
            missing_value_strategy (str): Strategy for handling missing values
            
        Returns:
            Dict: Preprocessed data and processing log
        """
        
        try:
            processed_data = raw_data.copy()
            processing_log = []
            
            # Rename columns according to mapping
            rename_dict = {v: k for k, v in column_mapping.items() if v is not None}
            processed_data = processed_data.rename(columns=rename_dict)
            processing_log.append(f"Renamed columns: {rename_dict}")
            
            # Handle missing values
            if missing_value_strategy == "intelligent":
                processed_data, missing_log = self._intelligent_missing_value_handling(processed_data)
                processing_log.extend(missing_log)
            elif missing_value_strategy == "drop":
                initial_rows = len(processed_data)
                processed_data = processed_data.dropna()
                processing_log.append(f"Dropped {initial_rows - len(processed_data)} rows with missing values")
            elif missing_value_strategy == "ai_assisted" and self.llm:
                processed_data, ai_log = self._ai_assisted_missing_value_handling(processed_data)
                processing_log.extend(ai_log)
            
            # Data type conversions and validation
            processed_data, validation_log = self._validate_and_convert_data(processed_data)
            processing_log.extend(validation_log)
            
            # Add derived columns
            processed_data = self._add_derived_columns(processed_data)
            processing_log.append("Added derived columns")
            
            return {
                "success": True,
                "processed_data": processed_data,
                "processing_log": processing_log,
                "data_summary": {
                    "rows_processed": len(processed_data),
                    "columns_final": len(processed_data.columns),
                    "processing_timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error in data preprocessing: {e}")
            return {"error": str(e), "success": False}
    
    def _intelligent_missing_value_handling(self, df: pd.DataFrame) -> tuple:
        """Handle missing values using intelligent strategies"""
        
        processing_log = []
        
        # Handle metal_type
        if 'metal_type' in df.columns and df['metal_type'].isnull().any():
            # Try to infer from product_type or other context
            if 'product_type' in df.columns:
                aluminum_products = ['beverage_cans', 'foil', 'automotive_parts', 'packaging', 'construction']
                copper_products = ['electrical_wiring', 'plumbing_tubes', 'electronics', 'electrical', 'wiring']
                
                for idx, row in df.iterrows():
                    if pd.isnull(row['metal_type']) and pd.notnull(row['product_type']):
                        product = str(row['product_type']).lower()
                        if any(al_prod in product for al_prod in aluminum_products):
                            df.at[idx, 'metal_type'] = 'aluminum'
                        elif any(cu_prod in product for cu_prod in copper_products):
                            df.at[idx, 'metal_type'] = 'copper'
            
            # Fill remaining with mode
            mode_metal = df['metal_type'].mode().iloc[0] if not df['metal_type'].mode().empty else 'aluminum'
            df['metal_type'].fillna(mode_metal, inplace=True)
            processing_log.append(f"Filled missing metal_type with inferred/mode values")
        
        # Handle production_kg
        if 'production_kg' in df.columns and df['production_kg'].isnull().any():
            # Use median by metal type if available
            if 'metal_type' in df.columns:
                df['production_kg'] = df.groupby('metal_type')['production_kg'].transform(
                    lambda x: x.fillna(x.median())
                )
            else:
                df['production_kg'].fillna(df['production_kg'].median(), inplace=True)
            processing_log.append("Filled missing production_kg with median values")
        
        # Handle recycled_fraction
        if 'recycled_fraction' in df.columns and df['recycled_fraction'].isnull().any():
            # Use industry averages by metal type
            defaults = {'aluminum': 0.35, 'copper': 0.42}
            
            for metal_type, default_fraction in defaults.items():
                mask = (df['metal_type'] == metal_type) & df['recycled_fraction'].isnull()
                df.loc[mask, 'recycled_fraction'] = default_fraction
            
            # Fill any remaining with overall average
            df['recycled_fraction'].fillna(0.3, inplace=True)
            processing_log.append("Filled missing recycled_fraction with industry averages")
        
        # Handle region
        if 'region' in df.columns and df['region'].isnull().any():
            df['region'].fillna('national_average', inplace=True)
            processing_log.append("Filled missing region with 'national_average'")
        
        # Handle product_type
        if 'product_type' in df.columns and df['product_type'].isnull().any():
            df['product_type'].fillna('generic', inplace=True)
            processing_log.append("Filled missing product_type with 'generic'")
        
        return df, processing_log
    
    def _ai_assisted_missing_value_handling(self, df: pd.DataFrame) -> tuple:
        """Handle missing values using AI assistance"""
        
        processing_log = []
        
        if not self.llm:
            return self._intelligent_missing_value_handling(df)
        
        try:
            # Get AI recommendations for missing value handling
            missing_summary = {}
            for col in df.columns:
                missing_count = df[col].isnull().sum()
                if missing_count > 0:
                    missing_summary[col] = {
                        "missing_count": int(missing_count),
                        "missing_percentage": round((missing_count / len(df)) * 100, 2),
                        "data_type": str(df[col].dtype),
                        "sample_values": df[col].dropna().head(3).tolist()
                    }
            
            if missing_summary:
                system_prompt = """You are an expert in LCA data preprocessing. For each column with missing values, suggest the best imputation strategy:
                
                Options:
                - "mean": Use mean value
                - "median": Use median value  
                - "mode": Use most frequent value
                - "forward_fill": Use previous value
                - "industry_default": Use domain-specific default
                - "drop": Remove rows with missing values
                
                Return JSON format: {"column_name": "strategy"}"""
                
                user_message = f"Missing value analysis: {json.dumps(missing_summary, indent=2)}"
                
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_message)
                ]
                
                response = self.llm.invoke(messages)
                ai_strategies = json.loads(response.content)
                
                # Apply AI-recommended strategies
                for col, strategy in ai_strategies.items():
                    if col in df.columns and df[col].isnull().any():
                        if strategy == "mean" and df[col].dtype in ['int64', 'float64']:
                            df[col].fillna(df[col].mean(), inplace=True)
                        elif strategy == "median" and df[col].dtype in ['int64', 'float64']:
                            df[col].fillna(df[col].median(), inplace=True)
                        elif strategy == "mode":
                            mode_val = df[col].mode().iloc[0] if not df[col].mode().empty else "unknown"
                            df[col].fillna(mode_val, inplace=True)
                        elif strategy == "industry_default":
                            # Apply domain-specific defaults
                            if col == "recycled_fraction":
                                df[col].fillna(0.3, inplace=True)
                            elif col == "region":
                                df[col].fillna("national_average", inplace=True)
                        
                        processing_log.append(f"Applied AI strategy '{strategy}' for column '{col}'")
                
        except Exception as e:
            logger.warning(f"AI-assisted missing value handling failed: {e}")
            # Fallback to intelligent handling
            return self._intelligent_missing_value_handling(df)
        
        return df, processing_log
    
    def _validate_and_convert_data(self, df: pd.DataFrame) -> tuple:
        """Validate and convert data types"""
        
        processing_log = []
        
        # Convert and validate production_kg
        if 'production_kg' in df.columns:
            df['production_kg'] = pd.to_numeric(df['production_kg'], errors='coerce')
            # Replace negative or zero values with median
            invalid_mask = (df['production_kg'] <= 0) | df['production_kg'].isnull()
            if invalid_mask.any():
                median_production = df[df['production_kg'] > 0]['production_kg'].median()
                df.loc[invalid_mask, 'production_kg'] = median_production
                processing_log.append(f"Fixed {invalid_mask.sum()} invalid production_kg values")
        
        # Convert and validate recycled_fraction
        if 'recycled_fraction' in df.columns:
            df['recycled_fraction'] = pd.to_numeric(df['recycled_fraction'], errors='coerce')
            # Ensure values are between 0 and 1
            df.loc[df['recycled_fraction'] < 0, 'recycled_fraction'] = 0
            df.loc[df['recycled_fraction'] > 1, 'recycled_fraction'] = 1
            # Convert percentages to fractions if needed
            high_values_mask = df['recycled_fraction'] > 1
            if high_values_mask.any():
                df.loc[high_values_mask, 'recycled_fraction'] /= 100
                processing_log.append("Converted percentage values to fractions for recycled_fraction")
        
        # Normalize metal_type
        if 'metal_type' in df.columns:
            df['metal_type'] = df['metal_type'].str.lower().str.strip()
            # Standardize variations
            df['metal_type'] = df['metal_type'].replace({
                'aluminium': 'aluminum',
                'al': 'aluminum',
                'cu': 'copper'
            })
            processing_log.append("Normalized metal_type values")
        
        # Normalize region
        if 'region' in df.columns:
            df['region'] = df['region'].str.lower().str.strip().str.replace(' ', '_')
            processing_log.append("Normalized region values")
        
        return df, processing_log
    
    def _add_derived_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add derived columns for analysis"""
        
        # Add row ID for tracking
        df['data_row_id'] = range(1, len(df) + 1)
        
        # Add batch processing timestamp
        df['processing_timestamp'] = datetime.now().isoformat()
        
        # Add data source indicator
        df['data_source'] = 'uploaded_file'
        
        # Add primary/secondary production split
        if 'recycled_fraction' in df.columns and 'production_kg' in df.columns:
            df['primary_fraction'] = 1 - df['recycled_fraction']
            df['primary_production_kg'] = df['production_kg'] * df['primary_fraction']
            df['secondary_production_kg'] = df['production_kg'] * df['recycled_fraction']
        
        return df
    
    def generate_data_report(self, ingestion_result: Dict[str, Any], 
                           preprocessing_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive data ingestion and preprocessing report"""
        
        report = {
            "data_ingestion_summary": {
                "file_info": ingestion_result.get("file_info", {}),
                "initial_assessment": ingestion_result.get("data_assessment", {}),
                "ai_insights": ingestion_result.get("ai_insights", {}),
                "ingestion_status": "success" if ingestion_result.get("success") else "failed"
            },
            "preprocessing_summary": {
                "processing_status": "success" if preprocessing_result.get("success") else "failed",
                "processing_log": preprocessing_result.get("processing_log", []),
                "data_summary": preprocessing_result.get("data_summary", {}),
                "final_data_shape": preprocessing_result.get("processed_data", pd.DataFrame()).shape
            },
            "data_quality_metrics": {},
            "recommendations": []
        }
        
        if preprocessing_result.get("success"):
            processed_data = preprocessing_result["processed_data"]
            
            # Calculate quality metrics
            report["data_quality_metrics"] = {
                "completeness_score": self._calculate_completeness_score(processed_data),
                "consistency_score": self._calculate_consistency_score(processed_data),
                "validity_score": self._calculate_validity_score(processed_data),
                "overall_quality_score": 0.0  # Will be calculated
            }
            
            # Calculate overall quality score
            metrics = report["data_quality_metrics"]
            metrics["overall_quality_score"] = np.mean([
                metrics["completeness_score"],
                metrics["consistency_score"],
                metrics["validity_score"]
            ])
            
            # Generate recommendations
            report["recommendations"] = self._generate_data_recommendations(processed_data, metrics)
        
        return report
    
    def _calculate_completeness_score(self, df: pd.DataFrame) -> float:
        """Calculate data completeness score"""
        required_fields = ['metal_type', 'production_kg', 'recycled_fraction']
        total_cells = len(df) * len(required_fields)
        missing_cells = sum(df[field].isnull().sum() for field in required_fields if field in df.columns)
        return max(0, (total_cells - missing_cells) / total_cells)
    
    def _calculate_consistency_score(self, df: pd.DataFrame) -> float:
        """Calculate data consistency score"""
        consistency_checks = []
        
        # Check metal_type consistency
        if 'metal_type' in df.columns:
            valid_metals = ['aluminum', 'copper']
            valid_count = df['metal_type'].isin(valid_metals).sum()
            consistency_checks.append(valid_count / len(df))
        
        # Check recycled_fraction range
        if 'recycled_fraction' in df.columns:
            valid_range = ((df['recycled_fraction'] >= 0) & (df['recycled_fraction'] <= 1)).sum()
            consistency_checks.append(valid_range / len(df))
        
        # Check production_kg positive values
        if 'production_kg' in df.columns:
            positive_values = (df['production_kg'] > 0).sum()
            consistency_checks.append(positive_values / len(df))
        
        return np.mean(consistency_checks) if consistency_checks else 1.0
    
    def _calculate_validity_score(self, df: pd.DataFrame) -> float:
        """Calculate data validity score"""
        validity_checks = []
        
        # Check for reasonable production quantities
        if 'production_kg' in df.columns:
            reasonable_range = ((df['production_kg'] >= 1) & (df['production_kg'] <= 1e9)).sum()
            validity_checks.append(reasonable_range / len(df))
        
        # Check for reasonable recycled fractions
        if 'recycled_fraction' in df.columns:
            reasonable_recycling = (df['recycled_fraction'] <= 0.9).sum()  # Max 90% recycling
            validity_checks.append(reasonable_recycling / len(df))
        
        return np.mean(validity_checks) if validity_checks else 1.0
    
    def _generate_data_recommendations(self, df: pd.DataFrame, metrics: Dict[str, float]) -> List[str]:
        """Generate data quality recommendations"""
        recommendations = []
        
        if metrics["completeness_score"] < 0.8:
            recommendations.append("Consider improving data collection processes to reduce missing values")
        
        if metrics["consistency_score"] < 0.9:
            recommendations.append("Review data entry procedures to improve consistency")
        
        if metrics["validity_score"] < 0.95:
            recommendations.append("Implement data validation rules at the source")
        
        # Check for specific issues
        if 'production_kg' in df.columns:
            cv = df['production_kg'].std() / df['production_kg'].mean() if df['production_kg'].mean() > 0 else 0
            if cv > 2:
                recommendations.append("High variability in production quantities - consider segmented analysis")
        
        if 'recycled_fraction' in df.columns:
            low_recycling = (df['recycled_fraction'] < 0.1).sum()
            if low_recycling > len(df) * 0.5:
                recommendations.append("Consider initiatives to increase recycled content")
        
        return recommendations

# Tools for the agent
@tool
def ingest_data_tool(file_path: str, sheet_name: str = None) -> Dict[str, Any]:
    """Tool to ingest data from CSV/Excel files"""
    agent = DataIngestionAgent()
    return agent.ingest_data(file_path, sheet_name)

@tool  
def preprocess_data_tool(raw_data_json: str, column_mapping_json: str, 
                        missing_value_strategy: str = "intelligent") -> Dict[str, Any]:
    """Tool to preprocess ingested data"""
    agent = DataIngestionAgent()
    
    # Convert JSON strings back to objects
    raw_data = pd.read_json(raw_data_json)
    column_mapping = json.loads(column_mapping_json)
    
    return agent.preprocess_data(raw_data, column_mapping, missing_value_strategy)

@tool
def generate_data_report_tool(ingestion_result_json: str, preprocessing_result_json: str) -> Dict[str, Any]:
    """Tool to generate comprehensive data report"""
    agent = DataIngestionAgent()
    
    ingestion_result = json.loads(ingestion_result_json)
    preprocessing_result = json.loads(preprocessing_result_json)
    
    return agent.generate_data_report(ingestion_result, preprocessing_result)