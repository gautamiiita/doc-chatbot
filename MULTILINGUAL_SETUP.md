# Multilingual Secutix Chatbot - Setup Guide

## 🌍 Current Status (Feb 25, 2026)

### Data
- ✅ **2,487 pages** extracted from 5 Confluence spaces
- ✅ **4 languages** supported: English, French, Spanish, German
- ✅ **4.4 MB** of documentation content
- ⏳ Vectorizing now (~15-20 minutes)

### Languages
```
English (en):  1,608 pages (RN + DOCEN spaces)
French (fr):     408 pages (DOCFR space)
Spanish (es):    237 pages (DOCES space)
German (de):     234 pages (DOCDE space)
────────────────────────────
TOTAL:         2,487 pages
```

## 🔍 Smart Language-Aware Search

### Strategy
1. **User's Language First**: Detect browser language, search within that language space
2. **Intelligent Fallback**: If <5 results, expand search to all languages
3. **No Translation**: Direct language matching (unlike older approach that translated)
4. **Better UX**: Native language answers, no translation artifacts

### Browser Language Detection
```javascript
// Automatically detects user's language from browser settings
const browserLang = navigator.language.split('-')[0];  // 'en', 'fr', 'es', 'de'
```

## 📋 Backend API

### Endpoints

#### GET `/search?q=<query>&lang=<language>`
Language-aware search with intelligent fallback.

**Parameters:**
- `q` (required): Search query
- `lang` (optional): Language code (en, fr, es, de). Defaults to 'en'

**Response:**
```json
{
  "query": "Zumstein features",
  "language_searched": "en",
  "results_count": 5,
  "results": [
    {
      "title": "Zumstein V4",
      "text": "...",
      "relevance": 0.89,
      "url": "https://confluence-secutix.atlassian.net/wiki/spaces/RN/pages/...",
      "language": "en",
      "space": "RN"
    }
  ]
}
```

#### POST `/query`
Full RAG with language-aware search + Claude answer generation.

**Body:**
```json
{
  "question": "What's new in Zumstein?",
  "language": "en"
}
```

#### POST `/summarize`
Language-aware search + formatted answer (fallback when query endpoint fails).

## 🧪 Testing

### Local Testing
```bash
# Search in English
curl "http://localhost:8001/search?q=Zumstein&lang=en"

# Search in French
curl "http://localhost:8001/search?q=Zumstein&lang=fr"

# Search in Spanish
curl "http://localhost:8001/search?q=Zumstein&lang=es"

# Search in German
curl "http://localhost:8001/search?q=Zumstein&lang=de"
```

### Public Testing
Open https://tandy-runic-nerissa.ngrok-free.dev in browsers with different language settings.

## 📊 Pinecone Configuration

### Index: `secutix-docs`
- **Vectors**: 2,487 (384-dimensional)
- **Metadata**: title, text, url, language, space, doc_id, type
- **Filter Support**: Language-aware queries using metadata filters

### Cost Estimate
- ~2,500 vectors @ 384 dims = minimal storage cost
- Query costs: ~$0.00001-0.0001 per search
- **Monthly estimate**: <$1 (search only) or $5-20 with answer generation

## 🚀 Deployment

### Docker
```bash
docker build -t secutix-chatbot .
docker run -p 8001:8001 secutix-chatbot
```

### Environment Variables
```bash
CONFLUENCE_EMAIL=your.email@secutix.com
CONFLUENCE_TOKEN=your_confluence_api_token
ANTHROPIC_API_KEY=your_anthropic_key
PINECONE_API_KEY=your_pinecone_key
```

## 🔐 Security Notes

- API keys in `.env` (protected by `.gitignore`)
- Confluence docs are public (no privacy issues)
- ngrok URL is temporary (for testing only)
- **Action**: Rotate tokens before production deployment

## 📈 Next Steps

1. ✅ Extract all 2,487 pages
2. ⏳ Vectorize with language metadata (in progress)
3. 🔄 Test language-aware search
4. 💳 Add Anthropic API credits for answer generation
5. 🚀 Deploy to production (Heroku/Docker/AWS)
6. 📊 Monitor usage and quality

## 🎯 Success Criteria for POC

- [ ] All 2,487 pages vectorized
- [ ] Language-aware search working (en, fr, es, de)
- [ ] Browser language detection working
- [ ] Public URL accessible
- [ ] Answer generation enabled (with API credits)
- [ ] Fallback chain working (query → summarize → search)
- [ ] Confluence links in results

