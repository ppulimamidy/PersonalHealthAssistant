"""
Medical Literature RAG API

Pro+ feature for searching medical literature, RAG conversations,
and AI-powered research insights.

Phase 2 of Health Intelligence Features
"""

import os
from datetime import datetime, timezone
from typing import Dict, List, Literal, Optional
from xml.etree import ElementTree as ET

import aiohttp
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from common.middleware.auth import get_current_user
from common.utils.logging import get_logger
from ..dependencies.usage_gate import (
    UsageGate,
    _supabase_get,
    _supabase_patch,
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

RAG_CONVERSATION_TITLE = "Research Conversation"


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


class PubMedSearchRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=500)
    max_results: int = Field(default=20, ge=1, le=100)
    date_from: Optional[str] = None  # YYYY/MM/DD
    date_to: Optional[str] = None  # YYYY/MM/DD
    sort: str = Field(default="relevance", pattern="^(relevance|date)$")
    # Source: only pubmed is implemented; cochrane/guideline planned
    source: Literal["pubmed", "cochrane", "guideline"] = "pubmed"


class SemanticSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    max_results: int = Field(default=20, ge=1, le=50)


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
    # Evidence hierarchy: meta_analysis > rct > observational > other
    evidence_level: Optional[str] = None
    publication_types: List[str] = Field(default_factory=list)


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


def _evidence_level_from_publication_types(types: List[str]) -> str:
    """Map PubMed publication types to evidence hierarchy: meta_analysis > rct > observational > other."""
    if not types:
        return "other"
    lower = [t.lower() for t in types]
    if any("meta-analysis" in t or "meta analysis" in t for t in lower):
        return "meta_analysis"
    if any(
        "randomized controlled trial" in t
        or "rct" in t
        or "controlled clinical trial" in t
        for t in lower
    ):
        return "rct"
    if any(
        "observational" in t
        or "cohort" in t
        or "case-control" in t
        or "cross-sectional" in t
        or "systematic review" in t
        for t in lower
    ):
        return "observational"
    return "other"


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

                # Extract publication types (evidence hierarchy)
                publication_types = []
                for pt_elem in article_elem.findall(".//PublicationType"):
                    if pt_elem.text:
                        publication_types.append(pt_elem.text.strip())
                evidence_level = _evidence_level_from_publication_types(
                    publication_types
                )

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
                        "publication_types": publication_types,
                        "evidence_level": evidence_level,
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
# EMBEDDINGS & SEMANTIC SEARCH
# ============================================================================

EMBEDDING_MODEL = "text-embedding-3-small"


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    """Cosine similarity between two vectors."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


async def _generate_embedding(text: str) -> Optional[List[float]]:
    """Generate embedding for text via OpenAI API."""
    if not OPENAI_API_KEY or not text or not text.strip():
        return None
    text = (text or "").strip()[:8000]
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                "https://api.openai.com/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={"model": EMBEDDING_MODEL, "input": text},
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                emb = data.get("data", [{}])[0].get("embedding")
                return emb if isinstance(emb, list) else None
        except Exception as e:
            logger.warning("Embedding generation failed: %s", e)
            return None


async def _store_embedding(
    article_id: str,
    text_content: str,
    embedding: List[float],
    embedding_type: str = "abstract",
) -> bool:
    """Store or replace embedding for an article (one row per article, type=abstract)."""
    if not text_content or not embedding:
        return False
    payload = {
        "article_id": article_id,
        "embedding_type": embedding_type,
        "section_name": None,
        "text_content": text_content[:10000],
        "embedding": embedding,
    }
    # Upsert by article_id + embedding_type so we don't duplicate
    existing = await _supabase_get(
        "article_embeddings",
        f"article_id=eq.{article_id}&embedding_type=eq.{embedding_type}&select=id&limit=1",
    )
    if existing:
        await _supabase_patch(
            "article_embeddings",
            f"id=eq.{existing[0]['id']}",
            {
                "text_content": payload["text_content"],
                "embedding": payload["embedding"],
            },
        )
        return True
    result = await _supabase_upsert("article_embeddings", payload)
    return bool(result)


async def _ensure_article_embedding(article_id: str, article_data: Dict) -> None:
    """Generate and store embedding for title+abstract if we have OpenAI key."""
    text_parts = [article_data.get("title") or "", article_data.get("abstract") or ""]
    text = " ".join(p for p in text_parts if p).strip()
    if not text:
        return
    emb = await _generate_embedding(text)
    if emb:
        await _store_embedding(article_id, text, emb, "abstract")


async def _fetch_articles_by_ids(article_ids: List[str]) -> List[Dict]:
    """Fetch research_articles by list of IDs. Returns list of row dicts."""
    if not article_ids:
        return []
    ids_param = ",".join(article_ids)
    rows = await _supabase_get(
        "research_articles",
        f"id=in.({ids_param})&select=*",
    )
    return rows or []


def _build_articles_context(article_rows: List[Dict]) -> str:
    """Build a single context string from article rows for RAG/insights."""
    parts = []
    for i, r in enumerate(article_rows, 1):
        title = r.get("title") or "No title"
        abstract = r.get("abstract") or ""
        pub = r.get("publication_date") or ""
        journal = r.get("journal") or ""
        parts.append(
            f"[Article {i}] {title}\n"
            + (f"Journal: {journal}. Date: {pub}.\n" if journal or pub else "")
            + (f"Abstract: {abstract}\n" if abstract else "")
        )
    return "\n".join(parts)


async def _openai_chat_completion(
    system_content: str,
    user_content: str,
    model: str = "gpt-4o-mini",
) -> Optional[str]:
    """Call OpenAI chat and return assistant content."""
    if not OPENAI_API_KEY or not OPENAI_API_KEY.strip():
        logger.warning("OpenAI chat skipped: OPENAI_API_KEY is not set")
        return None
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_content},
                        {"role": "user", "content": user_content},
                    ],
                    "max_tokens": 1024,
                },
                timeout=aiohttp.ClientTimeout(total=60),
            ) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    logger.warning(
                        "OpenAI chat failed: status=%s body=%s",
                        resp.status,
                        body[:500] if body else "",
                    )
                    return None
                data = await resp.json()
                choice = (data.get("choices") or [{}])[0]
                return (choice.get("message") or {}).get("content")
        except Exception as e:
            logger.warning("OpenAI chat failed: %s", e)
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
    Search medical literature. Only PubMed is implemented; Cochrane and guidelines are planned.
    Pro+ only - limited to 20 searches per week for Pro, unlimited for Pro+.
    """
    if request.source != "pubmed":
        raise HTTPException(
            status_code=501,
            detail="Only PubMed is supported. Cochrane and guideline sources are planned for a future release.",
        )
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
            await _ensure_article_embedding(article_id, article_data)
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
                    evidence_level=article_data.get("evidence_level"),
                    publication_types=article_data.get("publication_types", []),
                )
            )

    # Sort by evidence hierarchy: meta_analysis > rct > observational > other
    _order = {"meta_analysis": 0, "rct": 1, "observational": 2, "other": 3}
    articles.sort(
        key=lambda a: _order.get(a.evidence_level or "other", 3),
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


@router.post("/search/semantic", response_model=SearchResultsResponse)
async def semantic_search(
    request: SemanticSearchRequest,
    current_user: dict = Depends(UsageGate("medical_literature")),
):
    """
    Semantic search over cached article embeddings.
    Pro+ only. Requires embeddings to have been created (e.g. via prior keyword search).
    """
    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Semantic search is not configured (missing OPENAI_API_KEY).",
        )
    query_embedding = await _generate_embedding(request.query)
    if not query_embedding:
        raise HTTPException(
            status_code=503,
            detail="Could not generate query embedding.",
        )
    # Load cached embeddings (limit to avoid huge response)
    rows = await _supabase_get(
        "article_embeddings",
        "embedding_type=eq.abstract&select=article_id,embedding&limit=500",
    )
    if not rows:
        return SearchResultsResponse(
            query=request.query,
            total_results=0,
            articles=[],
            query_id=None,
        )
    # Compute similarity for each
    scored = []
    for row in rows:
        emb = row.get("embedding")
        if isinstance(emb, list) and len(emb) == len(query_embedding):
            score = _cosine_similarity(query_embedding, emb)
            scored.append((str(row["article_id"]), score))
    scored.sort(key=lambda x: -x[1])
    top_ids = [aid for aid, _ in scored[: request.max_results]]
    if not top_ids:
        return SearchResultsResponse(
            query=request.query,
            total_results=0,
            articles=[],
            query_id=None,
        )
    # Fetch articles by id (PostgREST in filter: id=in.(uuid1,uuid2,...))
    ids_param = ",".join(top_ids)
    article_rows = await _supabase_get(
        "research_articles",
        f"id=in.({ids_param})&select=*",
    )
    # Preserve order from top_ids
    by_id = {str(r["id"]): r for r in article_rows}
    articles = []
    for aid in top_ids:
        r = by_id.get(aid)
        if not r:
            continue
        fetched = r.get("fetched_at")
        if hasattr(fetched, "isoformat"):
            fetched = fetched.isoformat()
        elif not isinstance(fetched, str):
            fetched = datetime.now(timezone.utc).isoformat()
        articles.append(
            ResearchArticle(
                id=str(r["id"]),
                pubmed_id=r.get("pubmed_id"),
                doi=r.get("doi"),
                title=r["title"],
                abstract=r.get("abstract"),
                authors=r.get("authors", []),
                journal=r.get("journal"),
                publication_date=r.get("publication_date"),
                keywords=r.get("keywords", []),
                relevance_score=r.get("relevance_score"),
                citation_count=r.get("citation_count", 0),
                source_url=r.get("source_url"),
                fetched_at=fetched,
                evidence_level=r.get("evidence_level"),
                publication_types=r.get("publication_types", []),
            )
        )
    return SearchResultsResponse(
        query=request.query,
        total_results=len(scored),
        articles=articles,
        query_id=None,
    )


@router.get("/articles/{article_id}", response_model=ResearchArticle)
async def get_article(article_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific research article by ID."""
    rows = await _supabase_get("research_articles", f"id=eq.{article_id}&limit=1")

    if not rows:
        raise HTTPException(status_code=404, detail="Article not found")

    article = rows[0]
    return ResearchArticle(
        id=str(article["id"]),
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
        evidence_level=article.get("evidence_level"),
        publication_types=article.get("publication_types", []),
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
    Pro+ feature - AI-powered research conversations with citations.
    """
    conversation_id = request.conversation_id or "new_conversation"
    now = datetime.now(timezone.utc).isoformat()

    user_msg = RAGMessage(
        role="user",
        content=request.message,
        timestamp=now,
        sources=[],
    )

    # Build context from selected articles and call OpenAI
    context_article_ids = request.context_article_ids or []
    if not context_article_ids:
        assistant_message = RAGMessage(
            role="assistant",
            content="Please select one or more research articles to use as context for this conversation.",
            timestamp=now,
            sources=[],
        )
        return RAGConversation(
            id=conversation_id,
            title=RAG_CONVERSATION_TITLE,
            messages=[user_msg, assistant_message],
            context_articles=[],
            created_at=now,
            updated_at=now,
        )

    article_rows = await _fetch_articles_by_ids(context_article_ids)
    if not article_rows:
        assistant_message = RAGMessage(
            role="assistant",
            content="Could not load the selected articles. They may have been removed.",
            timestamp=now,
            sources=[],
        )
        return RAGConversation(
            id=conversation_id,
            title=RAG_CONVERSATION_TITLE,
            messages=[user_msg, assistant_message],
            context_articles=context_article_ids,
            created_at=now,
            updated_at=now,
        )

    context_text = _build_articles_context(article_rows)
    system = (
        "You are a medical research assistant. Answer the user's question using ONLY the following research articles. "
        "Cite articles by number, e.g. [Article 1]. If the articles do not contain relevant information, say so. "
        "Keep answers concise and evidence-based.\n\n---\nCONTEXT (research articles):\n\n"
        + context_text
    )
    assistant_content = await _openai_chat_completion(system, request.message)
    if not assistant_content:
        assistant_content = (
            "I couldn't generate a response right now. Please try again."
        )
    assistant_message = RAGMessage(
        role="assistant",
        content=assistant_content,
        timestamp=now,
        sources=context_article_ids,
    )
    return RAGConversation(
        id=conversation_id,
        title=RAG_CONVERSATION_TITLE,
        messages=[user_msg, assistant_message],
        context_articles=context_article_ids,
        created_at=now,
        updated_at=now,
    )


async def _openai_generate_insight(
    topic: str,
    insight_type: str,
    context_text: str,
) -> Optional[Dict]:
    """Call OpenAI to synthesize insight from article context. Returns dict with summary, key_findings, recommendations."""
    if not OPENAI_API_KEY or not OPENAI_API_KEY.strip():
        logger.warning("Insight generation skipped: OPENAI_API_KEY is not set")
        return None
    prompt = (
        f"Topic: {topic}. Insight type: {insight_type}.\n\n"
        "Using ONLY the following research articles, produce a short structured insight.\n"
        "Cite articles by number, e.g. [Article 1].\n\n"
        "Respond with exactly this format (plain text, no markdown):\n"
        "SUMMARY: <2-4 sentences>\n"
        "KEY_FINDINGS:\n- <finding 1 with citation>\n- <finding 2>\n- <finding 3>\n"
        "RECOMMENDATIONS:\n- <recommendation 1>\n- <recommendation 2>\n\n"
        "---\nCONTEXT:\n\n" + context_text
    )
    content = await _openai_chat_completion(
        "You are a medical research synthesizer. Output only the requested format.",
        prompt,
        model="gpt-4o-mini",
    )
    if not content:
        return None
    summary = ""
    key_findings = []
    recommendations = []
    current: Optional[str] = None
    for line in content.split("\n"):
        line_stripped = line.strip()
        if not line_stripped:
            continue
        if line_stripped.upper().startswith("SUMMARY:"):
            current = "summary"
            summary = line_stripped[8:].strip()
            continue
        if line_stripped.upper().startswith("KEY_FINDINGS"):
            current = "findings"
            rest = line_stripped[12:].strip()
            if rest and rest.startswith("-"):
                key_findings.append(rest[1:].strip())
            continue
        if line_stripped.upper().startswith("RECOMMENDATIONS"):
            current = "recommendations"
            rest = line_stripped[14:].strip()
            if rest and rest.startswith("-"):
                recommendations.append(rest[1:].strip())
            continue
        if current == "summary" and not summary:
            summary = line_stripped
        elif current == "findings" and line_stripped.startswith("-"):
            key_findings.append(line_stripped[1:].strip())
        elif current == "recommendations" and line_stripped.startswith("-"):
            recommendations.append(line_stripped[1:].strip())
    if not summary and content:
        summary = content[:500]
    return {
        "summary": summary or "No summary generated.",
        "key_findings": key_findings[:10],
        "recommendations": recommendations[:5],
    }


@router.post("/insights/generate", response_model=ResearchInsight)
async def generate_insight(
    request: ResearchInsightRequest,
    current_user: dict = Depends(UsageGate("medical_literature")),
):
    """
    Generate AI-powered research insights from selected articles.
    Pro+ feature - synthesizes findings and recommendations with citations.
    """
    user_id = current_user["id"]
    now = datetime.now(timezone.utc).isoformat()
    article_ids = request.article_ids or []

    if not article_ids:
        return ResearchInsight(
            id="no_articles",
            insight_type=request.insight_type,
            topic=request.topic,
            summary="Please select one or more articles to generate an insight.",
            key_findings=[],
            recommendations=[],
            source_article_ids=[],
            confidence_score=0.0,
            generated_at=now,
        )

    article_rows = await _fetch_articles_by_ids(article_ids)
    if not article_rows:
        return ResearchInsight(
            id="articles_not_found",
            insight_type=request.insight_type,
            topic=request.topic,
            summary="Could not load the selected articles.",
            key_findings=[],
            recommendations=[],
            source_article_ids=article_ids,
            confidence_score=0.0,
            generated_at=now,
        )

    context_text = _build_articles_context(article_rows)
    result = await _openai_generate_insight(
        request.topic,
        request.insight_type,
        context_text,
    )
    if not result:
        reason = (
            "OPENAI_API_KEY is not set or invalid. Set it in the API environment to enable insight generation."
            if not (OPENAI_API_KEY and OPENAI_API_KEY.strip())
            else "OpenAI API request failed. Check server logs for details (e.g. invalid key, rate limit, or network error)."
        )
        logger.warning(
            "Insight generation failed for topic=%s: %s", request.topic, reason
        )
        return ResearchInsight(
            id="generation_failed",
            insight_type=request.insight_type,
            topic=request.topic,
            summary=f"Insight generation is temporarily unavailable. {reason}",
            key_findings=[],
            recommendations=[],
            source_article_ids=article_ids,
            confidence_score=0.0,
            generated_at=now,
        )

    payload = {
        "user_id": user_id,
        "insight_type": request.insight_type,
        "topic": request.topic,
        "summary": result["summary"],
        "key_findings": result["key_findings"],
        "recommendations": result["recommendations"],
        "source_article_ids": article_ids,
        "confidence_score": 0.85,
        "is_current": True,
    }
    saved = await _supabase_upsert("research_insights", payload)
    insight_id = str(saved["id"]) if saved else "generated"

    return ResearchInsight(
        id=insight_id,
        insight_type=request.insight_type,
        topic=request.topic,
        summary=result["summary"],
        key_findings=result["key_findings"],
        recommendations=result["recommendations"],
        source_article_ids=article_ids,
        confidence_score=0.85,
        generated_at=now,
    )
