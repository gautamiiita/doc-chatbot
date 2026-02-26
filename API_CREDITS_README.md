# API Credits & Authentication

## Current Status ⚠️

Your Anthropic API key is **valid and authenticated**, but the associated account has **insufficient credits**.

**Error when attempting to query:**
```
❌ Your credit balance is too low to access the Anthropic API.
   Please go to Plans & Billing to upgrade or purchase credits.
```

---

## What's Working ✅

- ✅ `/search` endpoint (free - uses semantic search only)
- ✅ `/health` endpoint  
- ✅ Authentication to Anthropic (key is valid)
- ✅ Pinecone integration (all 2,487 pages indexed)

## What's Blocked ❌

- ❌ `/query` endpoint (needs Claude API call)
- ❌ `/summarize` endpoint (needs Claude API call)

---

## How to Fix

### Option 1: Add Credits (Recommended)

1. **Go to**: https://console.anthropic.com/account/billing/overview
2. **Add credits**: $20-50 recommended for testing/demo phase
3. **Restart backend**:
   ```bash
   cd /Users/gautam/.openclaw/agents/turing/doc-chatbot
   python3 backend.py
   ```
4. **Test**:
   - Visit: http://localhost:8001
   - Ask a question
   - You should see a full LLM-generated answer with PM persona + sources

### Option 2: Use a Different API Key

If you have another Anthropic account with credits:

1. Go to: https://console.anthropic.com/account/keys
2. Create a new API key (or copy existing one)
3. Update `.env` file:
   ```bash
   ANTHROPIC_API_KEY=sk-ant-api03-YOUR-NEW-KEY-HERE
   ```
4. Restart backend and test

---

## Cost Estimates

**Per query** (typical):
- Input tokens: ~2,000-3,000 (documents + prompt)
- Output tokens: ~400-600 (answer)
- Model: Claude 3.5 Sonnet (~$3/1M input, ~$15/1M output)
- **Cost per query**: ~$0.008-0.015 (less than 2¢)

**For testing**:
- $5 = ~400-600 queries
- $20 = ~1,500-2,000 queries
- $50 = ~4,000-5,000 queries

---

## Authentication Details

**Current setup:**
```
ANTHROPIC_API_KEY=sk-ant-api03-...
Authentication: x-api-key header
Endpoint: https://api.anthropic.com/v1/messages
Model: claude-3-5-sonnet-20241022
```

**This is the standard Anthropic API approach:**
- No gateway routing needed
- No special headers required
- Direct REST calls to Anthropic's servers
- All standard Anthropic tooling applies

---

## Testing Without Credits

If you don't want to add credits yet, you can still:

1. **Search documentation**: Works perfectly
   - `http://localhost:8001` → Ask a question → See search results

2. **View the chatbot UI**: Fully functional for search

3. **Once credits added**: Answer generation kicks in automatically

---

## Questions?

- **API key issues?** Check: https://console.anthropic.com/account/keys
- **Billing?** Visit: https://console.anthropic.com/account/billing
- **Account status?** Run: `curl -H "x-api-key: YOUR-KEY" https://api.anthropic.com/v1/models`

---

**Note**: This is a separate, independent application with its own API key. It doesn't use OpenClaw's subscription routing. It's the cleanest approach for a standalone service.
