# Testing Medical Literature RAG

How to test the Medical Literature RAG feature (evidence hierarchy, embeddings, semantic search, RAG chat, and insights).

## 1. Prerequisites

### Database migration

Apply migration 012 so `research_articles` has `evidence_level` and `publication_types`, and `article_embeddings` has insert policy:

```bash
# If using Supabase CLI (from repo root)
supabase db push

# Or run the SQL manually in Supabase Dashboard → SQL Editor
# File: supabase/migrations/012_medical_literature_evidence_embeddings.sql
```

### Environment (MVP API)

In `apps/mvp_api` (or your env file for the API), set:

- **OPENAI_API_KEY** – required for embeddings, semantic search, RAG chat, and insights.
- **SUPABASE_URL** and **SUPABASE_SERVICE_KEY** – required for caching articles and embeddings.
- **USE_SANDBOX=true** (optional) – skips usage gating so you can call research endpoints without subscription checks.
- **JWT / Supabase auth** – so `Authorization: Bearer <token>` is valid (see “Get a JWT” below).

### Get a JWT

All research endpoints require a valid user token.

- **Option A – Frontend:** Log in via your app, then in DevTools → Application (or Network) copy the `access_token` (or the value sent in `Authorization: Bearer ...`).
- **Option B – Supabase:** If you use Supabase Auth, sign in and use `session.access_token` from the client or from a small script that calls `supabase.auth.signInWithPassword()` and prints the token.

Set for the examples below:

```bash
export TOKEN="your-jwt-here"
export BASE_URL="http://localhost:8000"   # or your MVP API base URL
```

---

## 2. Run the MVP API

```bash
cd apps/mvp_api
# Create venv and install deps if needed
pip install -r requirements.txt
# Run (default port often 8000)
uvicorn main:app --reload --port 8000
```

Or use your usual run command (e.g. from root with `python -m uvicorn apps.mvp_api.main:app --reload --port 8000`).

---

## 3. Test endpoints

Use `curl` (or Postman/Insomnia) with the same `TOKEN` and `BASE_URL`.

### 3.1 Keyword search (PubMed + cache + embeddings)

This fetches from PubMed, caches articles with **evidence_level** and **publication_types**, and generates embeddings for semantic search later.

```bash
curl -s -X POST "$BASE_URL/api/v1/research/search" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "magnesium supplementation blood pressure", "max_results": 5}' | jq .
```

Check:

- `articles[].evidence_level` (e.g. `meta_analysis`, `rct`, `observational`, `other`).
- `articles[].publication_types` (e.g. `["Meta-Analysis", "Randomized Controlled Trial"]`).
- Articles are ordered by evidence (meta_analysis first, then rct, etc.).

### 3.2 Get one article

Use an `id` from the search response:

```bash
ARTICLE_ID="<paste-id-from-search>"
curl -s "$BASE_URL/api/v1/research/articles/$ARTICLE_ID" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

You should see `evidence_level` and `publication_types` on the article.

### 3.3 Semantic search

Requires at least one prior keyword search so embeddings exist. Uses the same auth and usage gate as search.

```bash
curl -s -X POST "$BASE_URL/api/v1/research/search/semantic" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "vitamin D and cardiovascular outcomes", "max_results": 5}' | jq .
```

You should get articles ranked by similarity to the query (and still with evidence fields).

### 3.4 RAG chat

Send a message with context set to article IDs from a previous search. The model answers using only those articles and cites them as [Article 1], [Article 2], etc.

```bash
# Use 1–2 article IDs from search (or get_article)
curl -s -X POST "$BASE_URL/api/v1/research/rag/chat" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What do these studies say about dosage?",
    "context_article_ids": ["<article-uuid-1>", "<article-uuid-2>"]
  }' | jq .
```

Check:

- `messages` has user and assistant messages.
- Assistant `content` refers to [Article 1] / [Article 2].
- Assistant `sources` equals `context_article_ids`.

### 3.5 Insights generate

Synthesizes summary, key findings, and recommendations from the given article IDs.

```bash
curl -s -X POST "$BASE_URL/api/v1/research/insights/generate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Magnesium and hypertension",
    "insight_type": "literature_summary",
    "article_ids": ["<article-uuid-1>", "<article-uuid-2>"]
  }' | jq .
```

Check:

- `summary` is a short synthesis.
- `key_findings` and `recommendations` are arrays; entries can cite [Article N].
- `source_article_ids` matches the requested `article_ids`.

### 3.6 Cochrane/guideline source (501)

Requesting a non-PubMed source should return 501:

```bash
curl -s -X POST "$BASE_URL/api/v1/research/search" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "diabetes", "source": "cochrane"}' | jq .
```

Expected: HTTP 501 and a message that only PubMed is supported and Cochrane/guidelines are planned.

---

## 4. Test from the frontend

If your app has a Research / Medical Literature screen:

1. Open the Research view and run a **search** (e.g. “magnesium blood pressure”).
2. Confirm results show **evidence level** and **publication types** (if the UI displays them).
3. Select one or more articles and try **RAG chat** (ask a question about the selected papers).
4. Use **Generate insight** (or equivalent) with the same selection and check summary, findings, and recommendations.

Semantic search is not in `researchService` yet; you can add a method that calls `POST /api/v1/research/search/semantic` with `{ query, max_results }` and then use it from the Research UI.

---

## 5. Quick checklist

| What to test              | How |
|---------------------------|-----|
| Evidence on articles      | Search → check `evidence_level` and `publication_types`; get article by id. |
| Sort by evidence          | Search → confirm order: meta_analysis, rct, observational, other. |
| Semantic search           | Run keyword search once, then POST `/search/semantic` with a related query. |
| RAG chat with citations   | POST `/rag/chat` with `context_article_ids` and a question; check [Article N] in reply. |
| Insights with citations    | POST `/insights/generate` with `article_ids`; check summary/findings/recommendations. |
| Cochrane returns 501      | POST `/search` with `"source": "cochrane"`. |

If something fails:

- **401** – Invalid or missing JWT; re-check token and auth config.
- **403** – Usage gate (e.g. tier limit); use Pro+ or `USE_SANDBOX=true`.
- **503 on semantic / RAG / insights** – Usually missing or invalid `OPENAI_API_KEY`; check env and logs.
