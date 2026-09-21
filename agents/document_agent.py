"""Document Analysis Agent for analyzing documents and extracting insights."""

import logging
from typing import List, Dict, Any, Optional
from openai import OpenAI
from models.context import ResearchContext
from models.findings import Finding, Citation

logger = logging.getLogger(__name__)


class DocumentAnalysisAgent:
    """Agent that analyzes documents to extract relevant insights."""

    def __init__(self, client: OpenAI, model: str = "gpt-4-turbo"):
        self.client = client
        self.model = model
        self.name = "Document Analysis Agent"

    async def research(
        self,
        context: ResearchContext,
        documents: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze documents for insights related to the research topic.

        Args:
            context: ResearchContext with topic and focus areas
            documents: Optional list of documents with 'path' and 'content' keys

        Returns:
            Dictionary with findings, citations, and summary
        """
        logger.info(f"Document Analysis Agent: Analyzing documents for '{context.topic}'")

        if not documents:
            logger.warning("No documents provided for analysis")
            return {
                "agent": self.name,
                "topic": context.topic,
                "findings": "No documents provided for analysis.",
                "citations": [],
                "status": "skipped",
            }

        # Build the system prompt
        system_prompt = f"""You are a document analysis specialist. Your task is to analyze provided documents
and extract information relevant to the research topic.

{context.to_prompt()}

ANALYSIS INSTRUCTIONS:
1. Carefully read through all provided documents
2. Extract key information related to the focus areas
3. Note the document source and section for each finding
4. Identify connections between documents
5. Summarize insights with clear citations to the source documents

Cite documents by name and section. Format: [Document Name, Section]"""

        # Build messages with system prompt and documents
        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": self._build_document_message(
                    context.topic, documents
                ),
            }
        ]

        # Run the API call with OpenAI
        findings_text = ""
        citations = []

        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=4096,
            messages=messages,
        )

        # Extract text from response
        if response.choices and response.choices[0].message.content:
            findings_text = response.choices[0].message.content

        # Extract document citations from findings
        for doc in documents:
            if doc.get("path") in findings_text or doc.get("name") in findings_text:
                citation = Citation(
                    url=f"document://{doc.get('path', 'unknown')}",
                    title=doc.get("name", doc.get("path", "Unknown Document")),
                    source_type="document",
                    confidence=0.95,
                )
                citations.append(citation)

        logger.debug(f"Document analysis completed. Extracted {len(citations)} citations")

        return {
            "agent": self.name,
            "topic": context.topic,
            "findings": findings_text,
            "citations": citations,
            "status": "completed",
        }

    def _build_document_message(self, topic: str, documents: List[Dict]) -> str:
        """Build a message containing all documents."""
        message = f"Analyze the following documents for information about: {topic}\n\n"

        for doc in documents:
            message += f"--- DOCUMENT: {doc.get('name', doc.get('path', 'Unknown'))} ---\n"
            message += f"{doc.get('content', 'No content')}\n\n"

        message += "Please extract and summarize all relevant information with source citations."
        return message
