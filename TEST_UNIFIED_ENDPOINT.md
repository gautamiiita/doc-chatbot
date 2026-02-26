# Test Unified /query Endpoint

## What's New

**Single unified `/query` endpoint** that does everything:
1. Searches Pinecone
2. Filters documents (>50% relevance, max 3)
3. Calls LLM with PM persona
4. Returns answer + sources with links

**No fallback chains. No complexity. Just one call.**

---

## Quick Start

### 1. Start Backend
```bash
cd /Users/gautam/.openclaw/agents/turing/doc-chatbot
python3 backend.py
```

Expected output:
```
INFO: Uvicorn running on http://0.0.0.0:8001
INFO: Application startup complete
```

### 2. Test with curl (Direct API Call)
```bash
curl -X POST http://localhost:8001/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is S-360?",
    "language": "en"
  }' | python3 -m json.tool
```

**Expected Response** (full LLM answer + sources):
```json
{
  "question": "What is S-360?",
  "answer": "[Full professional answer from LLM with PM perspective]",
  "sources": [
    {
      "title": "Source 1 Title",
      "url": "https://confluence-secutix.atlassian.net/wiki/spaces/...",
      "relevance_percentage": "68.6%",
      "relevance_score": 69
    },
    {
      "title": "Source 2 Title",
      "url": "...",
      "relevance_percentage": "65.3%"
    },
    {
      "title": "Source 3 Title",
      "url": "...",
      "relevance_percentage": "62.1%"
    }
  ],
  "detected_language": "en",
  "num_sources": 3
}
```

### 3. Test in Browser
```
http://localhost:8001
```

Type a question → See LLM answer + sources instantly

---

## Test Cases

### Test 1: Simple English Question
```bash
curl -X POST http://localhost:8001/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the new features in S-360 v4?",
    "language": "en"
  }'
```

**Expected**: Full answer with 3 Confluence links

### Test 2: French Question
```bash
curl -X POST http://localhost:8001/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Quels sont les nouvelles fonctionnalités de S-360 v4?",
    "language": "fr"
  }'
```

**Expected**: Answer generated in French + sources

### Test 3: Unknown Query
```bash
curl -X POST http://localhost:8001/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How to build a spaceship?",
    "language": "en"
  }'
```

**Expected**: Either "I couldn't find relevant documentation..." or best-effort answer from available sources

### Test 4: Check Health
```bash
curl http://localhost:8001/health | python3 -m json.tool
```

**Expected**:
```json
{
  "status": "ok",
  "chatbot": "Secutix Documentation",
  "pages_indexed": 2487,
  "model": "claude-sonnet-4-6",
  "auth": "OpenClaw SubToken"
}
```

---

## Process Flow (What Happens Inside)

```
User Question
    ↓
1. Detect Language (langdetect)
    ↓
2. If not English: Translate question to English for search
    ↓
3. Embed question (FastEmbed) → Get vector
    ↓
4. Search Pinecone (top 10 results)
    ↓
5. Filter documents (>50% relevance score, max 3)
    ↓
6. If no documents found → Return "No relevant documentation"
    ↓
7. Build context from 3 selected documents
    ↓
8. Call Claude Sonnet 4.6 with PM persona system prompt
    ↓
9. Get answer from LLM
    ↓
10. If original language ≠ English: Translate answer back
    ↓
11. Format response with source links + relevance scores
    ↓
Return to Browser
    ↓
Display: LLM Answer + 3 Sources with Confluence Links
```

---

## Endpoints

### POST `/query` (Main Endpoint)
**Input**:
```json
{
  "question": "Your question here",
  "language": "en"  // Optional, default "en"
}
```

**Output**:
```json
{
  "question": "...",
  "answer": "...",
  "sources": [...],
  "detected_language": "en",
  "num_sources": 3
}
```

### GET `/health`
Quick status check

### GET `/search?q=<query>`
Quick semantic search (without LLM)

---

## Troubleshooting

### Backend won't start
```bash
# Check Python version
python3 --version  # Should be 3.8+

# Check dependencies
pip install -r requirements.txt

# Check .env
cat .env | grep ANTHROPIC_SUBTOKEN
```

### "ANTHROPIC_SUBTOKEN not configured"
The token is missing from `.env`. Add it:
```bash
echo 'ANTHROPIC_SUBTOKEN=sk-ant-oat01-...' >> .env
python3 backend.py
```

### API returns 500 error
Check backend logs for stack trace. Common issues:
- SubToken expired (regenerate with `claude setup-token`)
- Pinecone connection issue
- Invalid JSON in request

### LLM answer seems incomplete
- Check that SubToken is fresh (`claude setup-token`)
- Verify max_tokens is sufficient (currently 1024)
- Check LLM response in logs

---

## What Changed

**Before** (Complex):
- Frontend: calls `/query` → fails → calls `/summarize` → fails → calls `/search`
- Backend: 3 separate endpoints with duplicate logic
- Response: Sometimes search results, sometimes LLM answer

**Now** (Simple):
- Frontend: calls `/query` once
- Backend: 1 unified endpoint that does everything
- Response: Always LLM answer + sources

**Result**: Faster, cleaner, more reliable ✅

---

## File Structure

```
doc-chatbot/
├── backend.py              # Unified RAG endpoint (300 lines)
├── public.html             # Chat UI (simplified)
├── .env                    # Config (SubToken + API keys)
├── requirements.txt        # Dependencies
├── test_rag.py            # Endpoint tests
├── READY_TO_DEPLOY.md     # Deployment guide
└── TEST_UNIFIED_ENDPOINT.md  # This file
```

---

## Success Criteria ✅

- [x] One `/query` endpoint handles everything
- [x] Pinecone search + filtering works
- [x] LLM answer generation works  
- [x] Source attribution with Confluence links
- [x] Multilingual support
- [x] Frontend calls only `/query` (no fallbacks)
- [x] curl test returns proper JSON
- [x] Browser UI shows answer + sources
- [x] SubToken authentication works

**Everything is ready for production!** 🚀
