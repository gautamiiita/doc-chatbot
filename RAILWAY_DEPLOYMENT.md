# 🚂 Railway Deployment Guide

**Complete step-by-step guide to deploy the Secutix Chatbot on Railway.**

---

## Prerequisites

✅ Railway account (free tier available): https://railway.app  
✅ GitHub account with the repo connected  
✅ API keys ready:
- `ANTHROPIC_SUBTOKEN` (from your OpenClaw setup-token)
- `PINECONE_API_KEY` (from https://app.pinecone.io)
- `CONFLUENCE_USER` (optional, defaults to gautam.srivastava@secutix.com)
- `CONFLUENCE_TOKEN` (optional, only needed for re-crawling)

---

## Step 1: Connect GitHub Repository

1. Go to https://railway.app and log in
2. Click **"New Project"** → **"Deploy from GitHub"**
3. Search for `doc-chatbot` repository
4. Click **"Import Repository"**
5. Railway will auto-detect `Dockerfile` and `.railway.json`

---

## Step 2: Add Environment Variables

In Railway dashboard:

1. Click **Variables** tab
2. Add these environment variables:

| Variable | Value | Required |
|----------|-------|----------|
| `ANTHROPIC_SUBTOKEN` | `sk-ant-...` (from setup-token) | ✅ YES |
| `PINECONE_API_KEY` | `pcsk_...` | ✅ YES |
| `CONFLUENCE_USER` | `gautam.srivastava@secutix.com` | ❌ Optional |
| `CONFLUENCE_TOKEN` | Your Confluence API token | ❌ Optional |
| `PORT` | (auto-set by Railway) | ⚠️ Don't change |

**Getting Your Tokens**:

**ANTHROPIC_SUBTOKEN**:
```bash
# On your local machine:
openclaw setup-token
# Copy the token that appears (starts with sk-ant-oat-)
```

**PINECONE_API_KEY**:
- Go to https://app.pinecone.io
- Click your API key (top-right)
- Copy the key value

---

## Step 3: Configure Port

Railway automatically sets the `PORT` environment variable. The backend.py now reads it:

```python
port = int(os.getenv("PORT", 8001))
uvicorn.run(app, host="0.0.0.0", port=port)
```

✅ **No manual port configuration needed.**

---

## Step 4: Deploy

1. Click **"Deploy"** button
2. Railway will:
   - Pull code from GitHub
   - Build Docker image (uses `Dockerfile`)
   - Install Python dependencies (`pip install -r requirements.txt`)
   - Start `python backend.py`
   - Assign public URL

**Deployment takes ~2-5 minutes.**

---

## Step 5: Verify Deployment

Once deployed, Railway shows a **public URL** like:
```
https://doc-chatbot-production.up.railway.app
```

**Test the health endpoint**:
```bash
curl https://doc-chatbot-production.up.railway.app/health
```

**Expected response**:
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

## Step 6: Test the Chatbot

### Via Browser

1. Visit: `https://doc-chatbot-production.up.railway.app`
2. Type a question
3. See answer with sources

### Via API

```bash
curl -X POST https://doc-chatbot-production.up.railway.app/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is new in Zumstein V4?",
    "language": "en"
  }'
```

### Search Only (No API Cost)

```bash
curl "https://doc-chatbot-production.up.railway.app/search?q=installation"
```

---

## Step 7: Monitor & Logs

In Railway dashboard:

1. Click **"Deployments"** tab
2. See real-time logs
3. Monitor CPU/memory usage
4. View request counts

**Common issues**:
- **"ANTHROPIC_SUBTOKEN not configured"**: Add the env var and redeploy
- **"Pinecone API error"**: Check `PINECONE_API_KEY` is correct
- **502 Bad Gateway**: Wait 30 seconds, API might be initializing

---

## Step 8: Custom Domain (Optional)

To use your own domain:

1. In Railway, click **Settings** → **Domains**
2. Add custom domain (e.g., `chatbot.yourdomain.com`)
3. Update DNS records as instructed
4. SSL certificate auto-generated

---

## Advanced: Redeployment

### Automatic (Recommended)

Railway auto-redeploys when you push to GitHub:

```bash
git push origin main
# Railway automatically detects changes and rebuilds
```

### Manual

In Railway dashboard:
1. Click **Deployments**
2. Click **"Redeploy"** on any previous deployment
3. Or push new code to GitHub

---

## Advanced: Update Documentation

If you crawl new Confluence pages:

```bash
# Local machine
python3 confluence_crawler.py
python3 vectorizer.py

# Push to GitHub
git push origin main

# Railway auto-redeploys with new vectors
```

---

## Cost Breakdown

| Service | Cost | Notes |
|---------|------|-------|
| **Railway** | Free (up to $5/month CPU) | Generous free tier |
| **Anthropic API** | ~$0.008-0.015 per query | Sub-2¢ per answer |
| **Pinecone** | Free | Vector search included |
| **Confluence API** | Free (public docs) | No cost for read access |
| **Total** | ~$0.01-0.05 per query | Very cheap scale |

---

## Troubleshooting

### Issue: "Module not found: fastembed"

**Fix**: Restart the deployment. Railway should have installed `requirements.txt` correctly.

```bash
# In Railway: Click "Redeploy"
```

### Issue: "Connection timeout to Pinecone"

**Fix**: Check `PINECONE_API_KEY` is correct:
```bash
# Get key from https://app.pinecone.io
# Make sure there are no extra spaces
```

### Issue: "Anthropic API 401 Unauthorized"

**Fix**: Check token format. Should start with `sk-ant-oat-`:
```bash
# Get from: openclaw setup-token
# Copy entire token (no spaces)
```

### Issue: "Slow responses (>5 seconds)"

**Fix**:
1. Check API credits at https://console.anthropic.com/account/billing
2. Reduce `top_k` from 5 to 3 in frontend
3. Use `/search` endpoint instead for instant results

### Issue: "200 No Results Found"

**Fix**: Pinecone might not be initialized yet. Wait 1-2 minutes and retry.

---

## Performance Notes

**Expected response times**:
- Search only: ~200ms (instant)
- Search + answer: ~2-3 seconds
- Cold start after deployment: ~5-10 seconds (initializes models)

**Cost per query**:
- Answer generation: ~$0.008-0.015 (varies with document length)
- Search: Free
- Inference: Included with Anthropic subscription

---

## Security Checklist

✅ No API keys in code (all from environment variables)  
✅ CORS enabled for your domain  
✅ HTTPS by default (Railway)  
✅ No logging of user queries (see `backend.py`)  
✅ Credentials never exposed in logs  

---

## Next Steps

1. **Deploy** following steps above
2. **Test** via browser and API
3. **Monitor** logs in Railway dashboard
4. **Share** the public URL with your team
5. **Update** Confluence content when needed (auto-redeploy via git push)

---

## Support

**Railway Docs**: https://docs.railway.app  
**FastAPI Docs**: https://fastapi.tiangolo.com  
**Pinecone Docs**: https://docs.pinecone.io

**Questions?**
1. Check Railway logs (Deployments tab)
2. Verify all env variables are set
3. Test API with `curl` before Browser UI
