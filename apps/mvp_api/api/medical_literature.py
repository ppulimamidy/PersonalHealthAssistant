"""
Medical Literature RAG API

Pro+ feature for searching medical literature, RAG conversations,
and AI-powered research insights.

Phase 2 of Health Intelligence Features
"""

import os
from datetime import datetime, timezone
from typing import Dict, List, Optional
from xml.etree import ElementTree as ET

import aiohttp
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from common.middleware.auth import get_current_user
from common.utils.logging import get_logger
from ..dependencies.usage_gate import (
    UsageGate,
    _supabase_get,
    _supabase_upsert,
    get_user_tier,
)

logger = get_logger(__name__)
router = APIRouter()

# PubMed E-utilities API
PUBMED_SEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_FETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
PUBMED_SUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

# API key for NCBI (optional but recommended for higher rate limits)
NCBI_API_KEY = os.environ.get("NCBI_API_KEY", "")

# OpenAI for embeddings and RAG
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


class PubMedSearchRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=500)
    max_results: int = Field(default=20, ge=1, le=100)
    date_from: Optional[str] = None  # YYYY/MM/DD
    date_to: Optional[str] = None  # YYYY/MM/DD
    sort: str = Field(default="relevance", pattern="^(relevance|date)$")


class ResearchArticle(BaseModel):
    id: str
    pubmed_id: Optional[str]
    doi: Optional[str]
    title: str
    abstract: Optional[str]
    authors: List[str]
    journal: Optional[str]
    publication_date: Optional[str]
    keywords: List[str]
    relevance_score: Optional[float]
    citation_count: int = 0
    source_url: Optional[str]
    fetched_at: str


class SearchResultsResponse(BaseModel):
    query: str
    total_results: int
    articles: List[ResearchArticle]
    query_id: Optional[str]


class BookmarkArticleRequest(BaseModel):
    article_id: str
    user_notes: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    relevance_rating: Optional[int] = Field(None, ge=1, le=5)


class ArticleBookmark(BaseModel):
    id: str
    article_id: str
    user_notes: Optional[str]
    tags: List[str]
    relevance_rating: Optional[int]
    bookmarked_at: str


class RAGMessageRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str = Field(..., min_length=1, max_length=2000)
    context_article_ids: List[str] = Field(default_factory=list)


class RAGMessage(BaseModel):
    role: str  # user or assistant
    content: str
    timestamp: str
    sources: List[str] = Field(default_factory=list)


class RAGConversation(BaseModel):
    id: str
    title: Optional[str]
    messages: List[RAGMessage]
    context_articles: List[str]
    created_at: str
    updated_at: str


class ResearchInsightRequest(BaseModel):
    topic: str
    insight_type: str = (
        "literature_summary"  # literature_summary, treatment_options, symptom_research
    )
    article_ids: List[str] = Field(default_factory=list)


class ResearchInsight(BaseModel):
    id: str
    insight_type: str
    topic: str
    summary: str
    key_findings: List[str]
    recommendations: List[str]
    source_article_ids: List[str]
    confidence_score: float
    generated_at: str


# ============================================================================
# PUBMED INTEGRATION
# ============================================================================


async def _pubmed_search(
    query: str,
    max_results: int = 20,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> List[str]:
    """Search PubMed and return list of PMIDs."""
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "retmode": "json",
        "sort": "relevance",
    }

    if NCBI_API_KEY:
        params["api_key"] = NCBI_API_KEY

    # Add date filter if provided
    if date_from or date_to:
        date_range = ""
        if date_from:
            date_range += date_from.replace("/", "")
        else:
            date_range += "1900"
        date_range += ":"
        if date_to:
            date_range += date_to.replace("/", "")
        else:
            date_range += "3000"
        params["datetype"] = "pdat"
        params["mindate"] = date_range.split(":")[0]
        params["maxdate"] = date_range.split(":")[1]

    timeout = aiohttp.ClientTimeout(total=10)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(PUBMED_SEARCH_URL, params=params) as resp:
                if resp.status != 200:
                    logger.error(f"PubMed search failed: {resp.status}")
                    return []
                data = await resp.json()
                pmids = data.get("esearchresult", {}).get("idlist", [])
                logger.info(
                    f"PubMed search returned {len(pmids)} results for query: {query}"
                )
                return pmids
    except (aiohttp.ClientError, TimeoutError) as exc:
        logger.error(f"PubMed search error: {exc}")
        return []


async def _pubmed_fetch_articles(pmids: List[str]) -> List[Dict]:
    """Fetch article details from PubMed."""
    if not pmids:
        return []

    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml",
        "rettype": "abstract",
    }

    if NCBI_API_KEY:
        params["api_key"] = NCBI_API_KEY

    timeout = aiohttp.ClientTimeout(total=15)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(PUBMED_FETCH_URL, params=params) as resp:
                if resp.status != 200:
                    logger.error(f"PubMed fetch failed: {resp.status}")
                    return []

                xml_text = await resp.text()
                return _parse_pubmed_xml(xml_text)
    except (aiohttp.ClientError, TimeoutError) as exc:
        logger.error(f"PubMed fetch error: {exc}")
        return []


def _parse_pubmed_xml(xml_text: str) -> List[Dict]:
    """Parse PubMed XML response into article dictionaries."""
    articles = []
    try:
        root = ET.fromstring(xml_text)
        for article_elem in root.findall(".//PubmedArticle"):
            try:
                # Extract PMID
                pmid_elem = article_elem.find(".//PMID")
                pmid = pmid_elem.text if pmid_elem is not None else None

                # Extract title
                title_elem = article_elem.find(".//ArticleTitle")
                title = title_elem.text if title_elem is not None else "No title"

                # Extract abstract
                abstract_parts = []
                for abstract_elem in article_elem.findall(".//AbstractText"):
                    text = abstract_elem.text or ""
                    label = abstract_elem.get("Label", "")
                    if label:
                        abstract_parts.append(f"{label}: {text}")
                    else:
                        abstract_parts.append(text)
                abstract = " ".join(abstract_parts) if abstract_parts else None

                # Extract authors
                authors = []
                for author_elem in article_elem.findall(".//Author"):
                    last_name = author_elem.findtext("LastName", "")
                    initials = author_elem.findtext("Initials", "")
                    if last_name:
                        authors.append(f"{last_name} {initials}".strip())

                # Extract journal
                journal_elem = article_elem.find(".//Journal/Title")
                journal = journal_elem.text if journal_elem is not None else None

                # Extract publication date
                pub_date_elem = article_elem.find(".//PubDate")
                pub_date = None
                if pub_date_elem is not None:
                    year = pub_date_elem.findtext("Year")
                    month = pub_date_elem.findtext("Month", "01")
                    day = pub_date_elem.findtext("Day", "01")
                    if year:
                        # Convert month name to number if needed
                        month_map = {
                            "Jan": "01",
                            "Feb": "02",
                            "Mar": "03",
                            "Apr": "04",
                            "May": "05",
                            "Jun": "06",
                            "Jul": "07",
                            "Aug": "08",
                            "Sep": "09",
                            "Oct": "10",
                            "Nov": "11",
                            "Dec": "12",
                        }
                        month = month_map.get(month, month)
                        pub_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"

                # Extract DOI
                doi = None
                for id_elem in article_elem.findall(".//ArticleId"):
                    if id_elem.get("IdType") == "doi":
                        doi = id_elem.text
                        break

                # Extract keywords
                keywords = []
                for keyword_elem in article_elem.findall(".//Keyword"):
                    if keyword_elem.text:
                        keywords.append(keyword_elem.text)

                articles.append(
                    {
                        "pubmed_id": pmid,
                        "doi": doi,
                        "title": title,
                        "abstract": abstract,
                        "authors": authors,
                        "journal": journal,
                        "publication_date": pub_date,
                        "keywords": keywords,
                        "source_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                        if pmid
                        else None,
                    }
                )
            except Exception as e:
                logger.warning(f"Error parsing PubMed article: {e}")
                continue

        logger.info(f"Parsed {len(articles)} articles from PubMed XML")
        return articles
    except ET.ParseError as e:
        logger.error(f"XML parsing error: {e}")
        return []


async def _cache_article(article_data: Dict) -> Optional[str]:
    """Cache article in database and return article ID."""
    # Check if article already exists
    if article_data.get("pubmed_id"):
        existing = await _supabase_get(
            "research_articles",
            f"pubmed_id=eq.{article_data['pubmed_id']}&select=id&limit=1",
        )
        if existing:
            return existing[0]["id"]

    # Insert new article
    payload = {
        **article_data,
        "source": "pubmed",
        "relevance_score": 0.8,  # Default relevance
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }

    result = await _supabase_upsert("research_articles", payload)
    if result:
        return result.get("id")
    return None


# ============================================================================
# API ENDPOINTS
# ============================================================================


@router.post("/search", response_model=SearchResultsResponse)
async def search_literature(
    request: PubMedSearchRequest,
    current_user: dict = Depends(UsageGate("medical_literature")),
):
    """
    Search medical literature via PubMed.
    Pro+ only - limited to 20 searches per week for Pro, unlimited for Pro+.
    """
    user_id = current_user["id"]

    # Search PubMed
    pmids = await _pubmed_search(
        request.query,
        max_results=request.max_results,
        date_from=request.date_from,
        date_to=request.date_to,
    )

    if not pmids:
        return SearchResultsResponse(
            query=request.query,
            total_results=0,
            articles=[],
            query_id=None,
        )

    # Fetch article details
    article_data_list = await _pubmed_fetch_articles(pmids[: request.max_results])

    # Cache articles and build response
    articles = []
    article_ids = []
    for article_data in article_data_list:
        article_id = await _cache_article(article_data)
        if article_id:
            article_ids.append(article_id)
            articles.append(
                ResearchArticle(
                    id=article_id,
                    pubmed_id=article_data.get("pubmed_id"),
                    doi=article_data.get("doi"),
                    title=article_data["title"],
                    abstract=article_data.get("abstract"),
                    authors=article_data.get("authors", []),
                    journal=article_data.get("journal"),
                    publication_date=article_data.get("publication_date"),
                    keywords=article_data.get("keywords", []),
                    relevance_score=0.8,
                    citation_count=0,
                    source_url=article_data.get("source_url"),
                    fetched_at=datetime.now(timezone.utc).isoformat(),
                )
            )

    # Save query to database
    query_payload = {
        "user_id": user_id,
        "query_text": request.query,
        "query_type": "general",
        "article_ids": article_ids,
        "result_count": len(articles),
        "is_saved": False,
    }
    query_result = await _supabase_upsert("research_queries", query_payload)
    query_id = query_result.get("id") if query_result else None

    return SearchResultsResponse(
        query=request.query,
        total_results=len(pmids),
        articles=articles,
        query_id=query_id,
    )


@router.get("/articles/{article_id}", response_model=ResearchArticle)
async def get_article(article_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific research article by ID."""
    rows = await _supabase_get("research_articles", f"id=eq.{article_id}&limit=1")

    if not rows:
        raise HTTPException(status_code=404, detail="Article not found")

    article = rows[0]
    return ResearchArticle(
        id=article["id"],
        pubmed_id=article.get("pubmed_id"),
        doi=article.get("doi"),
        title=article["title"],
        abstract=article.get("abstract"),
        authors=article.get("authors", []),
        journal=article.get("journal"),
        publication_date=article.get("publication_date"),
        keywords=article.get("keywords", []),
        relevance_score=article.get("relevance_score"),
        citation_count=article.get("citation_count", 0),
        source_url=article.get("source_url"),
        fetched_at=article.get("fetched_at"),
    )


@router.post("/bookmarks", response_model=ArticleBookmark, status_code=201)
async def bookmark_article(
    request: BookmarkArticleRequest, current_user: dict = Depends(get_current_user)
):
    """Bookmark an article with notes and tags."""
    user_id = current_user["id"]

    payload = {
        "user_id": user_id,
        "article_id": request.article_id,
        "user_notes": request.user_notes,
        "tags": request.tags,
        "relevance_rating": request.relevance_rating,
        "bookmarked_at": datetime.now(timezone.utc).isoformat(),
    }

    result = await _supabase_upsert("article_bookmarks", payload)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to bookmark article")

    return ArticleBookmark(
        id=result["id"],
        article_id=result["article_id"],
        user_notes=result.get("user_notes"),
        tags=result.get("tags", []),
        relevance_rating=result.get("relevance_rating"),
        bookmarked_at=result["bookmarked_at"],
    )


@router.get("/bookmarks", response_model=List[ArticleBookmark])
async def list_bookmarks(current_user: dict = Depends(get_current_user)):
    """List user's bookmarked articles."""
    user_id = current_user["id"]

    rows = await _supabase_get(
        "article_bookmarks", f"user_id=eq.{user_id}&order=bookmarked_at.desc"
    )

    return [
        ArticleBookmark(
            id=row["id"],
            article_id=row["article_id"],
            user_notes=row.get("user_notes"),
            tags=row.get("tags", []),
            relevance_rating=row.get("relevance_rating"),
            bookmarked_at=row["bookmarked_at"],
        )
        for row in rows
    ]


@router.post("/rag/chat", response_model=RAGConversation)
async def rag_chat(
    request: RAGMessageRequest,
    current_user: dict = Depends(UsageGate("medical_literature")),
):
    """
    Chat with AI about research articles using RAG.
    Pro+ feature - AI-powered research conversations.
    """
    user_id = current_user["id"]

    # TODO: Implement RAG chat logic with OpenAI
    # For now, return placeholder
    conversation_id = request.conversation_id or "new_conversation"

    # Mock response
    assistant_message = RAGMessage(
        role="assistant",
        content="RAG chat functionality coming soon. This will provide AI-powered insights based on the research articles you've selected.",
        timestamp=datetime.now(timezone.utc).isoformat(),
        sources=request.context_article_ids,
    )

    return RAGConversation(
        id=conversation_id,
        title="Research Conversation",
        messages=[
            RAGMessage(
                role="user",
                content=request.message,
                timestamp=datetime.now(timezone.utc).isoformat(),
                sources=[],
            ),
            assistant_message,
        ],
        context_articles=request.context_article_ids,
        created_at=datetime.now(timezone.utc).isoformat(),
        updated_at=datetime.now(timezone.utc).isoformat(),
    )


@router.post("/insights/generate", response_model=ResearchInsight)
async def generate_insight(
    request: ResearchInsightRequest,
    current_user: dict = Depends(UsageGate("medical_literature")),
):
    """
    Generate AI-powered research insights.
    Pro+ feature - synthesizes insights from multiple articles.
    """
    user_id = current_user["id"]

    # TODO: Implement AI insight generation
    # For now, return placeholder
    return ResearchInsight(
        id="placeholder_insight",
        insight_type=request.insight_type,
        topic=request.topic,
        summary=f"AI-generated insights for {request.topic} will appear here. This feature synthesizes findings from multiple research articles.",
        key_findings=[
            "Key finding 1 from literature review",
            "Key finding 2 based on recent studies",
            "Key finding 3 with clinical relevance",
        ],
        recommendations=[
            "Recommendation 1 based on evidence",
            "Recommendation 2 for further research",
        ],
        source_article_ids=request.article_ids,
        confidence_score=0.85,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
