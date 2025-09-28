"""
Compliance Agent with RAG - ISO 14040/14044 LCA Standards Compliance Checker
Using Cerebras LLM + Pinecone Vector DB
Provides detailed compliance report and percentage scores
"""

import logging
import os
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Pinecone
from langchain.chains import RetrievalQA
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_cerebras import ChatCerebras

import pinecone

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class ComplianceAgent:
    def __init__(self, cerebras_api_key: str = None, pinecone_api_key: str = None, docs_folder: str = None):
        self.cerebras_api_key = cerebras_api_key or os.getenv("CEREBRAS_API_KEY")
        self.pinecone_api_key = pinecone_api_key or os.getenv("PINECONE_API_KEY")
        self.docs_folder = Path(docs_folder) if docs_folder else None

        if not self.cerebras_api_key:
            raise ValueError("Cerebras API key required")

        if not self.pinecone_api_key:
            raise ValueError("Pinecone API key required")

        # Initialize Cerebras LLM
        self.llm = ChatCerebras(api_key=self.cerebras_api_key, model="llama3.1-8b")

        # Embeddings for vector search
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

        # Initialize Pinecone
        pinecone.init(api_key=self.pinecone_api_key, environment="us-east1-gcp")

        self.index_name = "lca-compliance-standards"
        if self.index_name not in pinecone.list_indexes():
            pinecone.create_index(
                name=self.index_name,
                dimension=384,  # embedding dimension
                metric="cosine"
            )

        self.vector_store = Pinecone(
            index=pinecone.Index(self.index_name),
            embedding_function=self.embeddings.embed_query,
            text_key="text"
        )

        if self.docs_folder:
            self._ingest_local_pdfs()

    def _ingest_local_pdfs(self):
        """Load PDFs into Pinecone vector database"""
        all_docs = []
        for pdf_file in self.docs_folder.glob("*.pdf"):
            loader = PyPDFLoader(str(pdf_file))
            docs = loader.load()
            all_docs.extend(docs)

        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        split_docs = splitter.split_documents(all_docs)

        # Add to Pinecone
        self.vector_store.add_documents(split_docs)
        logger.info("RAG system initialized successfully with local PDFs in Pinecone.")

    def check_lca_compliance(self, lca_study_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check LCA compliance and return structured % scores + text report"""
        # Build professional prompt with all LCA details
        prompt = f"""
You are an ISO 14040/14044 LCA compliance expert. 
Evaluate this LCA study for compliance with ISO 14040/14044.

**LCA Study Details:**
Functional Unit: {lca_study_data.get('functional_unit', 'Not specified')}
Analysis Type / System Boundaries: {lca_study_data.get('analysis_type', 'Not specified')}
Scenarios: {lca_study_data.get('scenarios', 'Not specified')}

Provide:
- Compliance % for each phase: Goal & Scope, Inventory, Impact Assessment, Interpretation, Reporting
- Issues / Missing Information
- Recommendations
- Overall Compliance %
- Professional structured report
"""

        # Use RAG if vector store exists
        retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=False
        )
        report_text = qa_chain.run(prompt)

        # Extract numeric compliance percentages (try to parse from LLM text)
        # For simplicity, we will also calculate a basic % based on data completeness
        phases = ["goal_and_scope", "inventory", "impact", "interpretation", "reporting"]
        completeness_score = {}
        scenarios = lca_study_data.get("scenarios", [])
        total_fields = len(phases)
        for phase in phases:
            score = 0
            if phase == "goal_and_scope":
                score = 1 if lca_study_data.get("functional_unit") else 0
            elif phase == "inventory":
                score = 1 if all(s.get("energy_intensity") is not None for s in scenarios) else 0
            elif phase == "impact":
                score = 1 if scenarios and any(s.get("material_emission_factors") for s in scenarios) else 0
            elif phase == "interpretation":
                score = 1 if scenarios else 0
            elif phase == "reporting":
                score = 1 if lca_study_data.get("analysis_type") else 0
            completeness_score[phase] = score * 100

        overall_score = sum(completeness_score.values()) / total_fields

        return {
            "compliance_percentages": completeness_score,
            "overall_compliance_percent": overall_score,
            "professional_report": report_text
        }


# --------------------- Example Usage ---------------------
#if __name__ == "__main__":
#    sample_lca_data = {
#        "functional_unit": "1 kg of aluminum",
#        "analysis_type": "cradle_to_gate",
#       "scenarios": [
#            {"material_type": "aluminum", "mass_kg": 1,
#             "energy_intensity": 50, "transport": {"distance_km": 500},
#             "recycling": {"rate": 0.3}, "material_emission_factors": {"CO2": 1.5}}
#        ]
#    }
#
#    agent = ComplianceAgent(
#        cerebras_api_key=os.getenv("CEREBRAS_API_KEY"),
#        pinecone_api_key=os.getenv("PINECONE_API_KEY"),
#        docs_folder="docs/iso_standards"
#    )

#    result = agent.check_lca_compliance(sample_lca_data)
#    print("\n===== Compliance Result =====\n")
#    print(f"Compliance Percentages per Phase: {result['compliance_percentages']}")
#    print(f"Overall Compliance: {result['overall_compliance_percent']:.2f}%")
#    print("\nProfessional Report:\n")
#   print(result['professional_report'])
