# tools.py - Evidence retrieval tools
import os
import logging
from typing import List
from langchain_core.documents import Document
from langchain_community.tools import TavilySearchResults
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

tavily_api_key = os.getenv("TAVILY_API_KEY")
if not tavily_api_key:
    logger.warning("TAVILY_API_KEY not found in environment variables")


def retrieve_evidence(query: str, max_results: int = 8) -> List[Document]:
    """
    Retrieve evidence documents using Tavily search
    """
    try:
        if not tavily_api_key:
            logger.error("Tavily API key not configured")
            return _create_fallback_documents(query)

        search = TavilySearchResults(
            api_key=tavily_api_key,
            max_results=max_results,
            search_depth="advanced",
            include_answer=True,
            include_raw_content=False,
            include_images=False
        )

        logger.info(f"Searching for: {query}")
        results = search.invoke({"query": query})

        documents = []
        for i, result in enumerate(results):
            try:
                if isinstance(result, dict):
                    content = result.get('content', result.get('snippet', ''))
                    title = result.get('title', f'Result {i+1}')
                    url = result.get('url', '')
                else:
                    content = str(result)
                    title = f'Result {i+1}'
                    url = ''

                if content:
                    doc = Document(
                        page_content=content,
                        metadata={
                            'source': url,
                            'title': title,
                            'search_query': query,
                            'result_index': i
                        }
                    )
                    documents.append(doc)

            except Exception as e:
                logger.error(f"Error processing search result {i}: {e}")
                continue

        logger.info(f"Retrieved {len(documents)} documents")
        return documents

    except Exception as e:
        logger.error(f"Error in retrieve_evidence: {e}")
        return _create_fallback_documents(query)


def _create_fallback_documents(query: str) -> List[Document]:
    """
    Create fallback documents when search fails
    """
    logger.info("Using fallback documents due to search failure")

    fallback_content = [
        {
            'content': f"This is a placeholder document about {query}. The search service is currently unavailable.",
            'title': f"Fallback: {query}",
            'url': 'https://example.com/fallback'
        },
        {
            'content': f"General information about {query} would typically be found through web search.",
            'title': f"General Info: {query}",
            'url': 'https://example.com/general'
        }
    ]

    documents = []
    for i, item in enumerate(fallback_content):
        doc = Document(
            page_content=item['content'],
            metadata={
                'source': item['url'],
                'title': item['title'],
                'search_query': query,
                'result_index': i,
                'is_fallback': True
            }
        )
        documents.append(doc)

    return documents


# Alternative implementation using Google Custom Search (if you prefer)
def retrieve_evidence_google(query: str, max_results: int = 8) -> List[Document]:
    """
    Alternative implementation using Google Custom Search API
    Requires GOOGLE_API_KEY and GOOGLE_CSE_ID environment variables
    """
    try:
        from googleapiclient.discovery import build

        google_api_key = os.getenv("GOOGLE_API_KEY")
        google_cse_id = os.getenv("GOOGLE_CSE_ID")

        if not google_api_key or not google_cse_id:
            logger.error("Google Search API credentials not configured")
            return _create_fallback_documents(query)

        service = build("customsearch", "v1", developerKey=google_api_key)

        result = service.cse().list(
            q=query,
            cx=google_cse_id,
            num=min(max_results, 10)  # Google CSE API limits to 10 per request
        ).execute()

        documents = []
        for i, item in enumerate(result.get('items', [])):
            try:
                doc = Document(
                    page_content=item.get('snippet', ''),
                    metadata={
                        'source': item.get('link', ''),
                        'title': item.get('title', f'Result {i+1}'),
                        'search_query': query,
                        'result_index': i
                    }
                )
                documents.append(doc)
            except Exception as e:
                logger.error(f"Error processing Google search result {i}: {e}")
                continue

        logger.info(f"Retrieved {len(documents)} documents from Google Search")
        return documents

    except ImportError:
        logger.error("Google API client not installed. Run: pip install google-api-python-client")
        return _create_fallback_documents(query)
    except Exception as e:
        logger.error(f"Error in Google search: {e}")
        return _create_fallback_documents(query)
