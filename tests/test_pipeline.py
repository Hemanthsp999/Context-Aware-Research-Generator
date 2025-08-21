import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from langchain_core.documents import Document
from tools import retrieve_evidence, retrieve_evidence_google
from dotenv import load_dotenv

os.getenv("TAVILY_API_KEY")


def test_retrieve_evidence_real():
    """
    Integration test against Tavily API (requires TAVILY_API_KEY in .env).
    """
    query = "fastapi unit testing"
    docs = retrieve_evidence(query, max_results=3)

    assert isinstance(docs, list)
    assert len(docs) > 0, "Expected at least one document from Tavily API"
    assert all(isinstance(d, Document) for d in docs)

    # Validate metadata
    for doc in docs:
        assert "search_query" in doc.metadata
        assert doc.metadata["search_query"] == query
        assert "title" in doc.metadata
        assert "source" in doc.metadata


def test_retrieve_evidence_google_real():
    """
    Integration test against Google Custom Search (requires GOOGLE_API_KEY and GOOGLE_CSE_ID).
    """
    query = "python asyncio tutorial"
    docs = retrieve_evidence_google(query, max_results=3)

    assert isinstance(docs, list)
    assert len(docs) > 0, "Expected at least one document from Google CSE"
    assert all(isinstance(d, Document) for d in docs)

    # Validate metadata
    for doc in docs:
        assert "search_query" in doc.metadata
        assert doc.metadata["search_query"] == query
        assert "title" in doc.metadata
        assert "source" in doc.metadata

