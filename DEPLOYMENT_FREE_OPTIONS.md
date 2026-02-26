# Free & Cheap Deployment Options for Doc-Chatbot

## Quick Answer

**Best Free Option**: Railway.app (free tier with $5 monthly credits)
- ✅ Deploy FastAPI backend easily
- ✅ Custom domain support
- ✅ No credit card required for free tier
- ✅ ~15 minutes to deploy

**Cheapest Paid Option**: DigitalOcean ($4-5/month)
- ✅ Very reliable
- ✅ Cheap and simple
- ✅ Great documentation

**Current Problem with ngrok**:
- URL changes every time you restart
- Can't share permanently ("this URL won't work tomorrow")
- Limited bandwidth
- Not ideal for production

---

## Option 1: Railway.app (FREE - RECOMMENDED)

### Why Railway?
- ✅ Free tier: $5/month credits (covers most small apps)
- ✅ Simple deployment (GitHub auto-deploy)
- ✅ Custom domain support
- ✅ Permanent URL (doesn't change like ngrok)
- ✅ Very fast to set up
- ✅ Good for projects like yours

### Step 1: Sign Up
1. Go to railway.app
2. Sign up with GitHub account
3. Connect your GitHub repo (doc-chatbot)

### Step 2: Deploy
```
In Railway dashboard:
1. New Project
2. Deploy from GitHub
3. Select your doc-chatbot repo
4. Select "Dockerfile" (or auto-detect)
5. Configure environment variables:
   - ANTHROPIC_SUBTOKEN
   - PINECONE_API_KEY
6. Click "Deploy"
```

### Step 3: Get Custom Domain
```
1. Go to your app settings
2. Click "Domain"
3. Generate domain (e.g., doc-chatbot-abc123.railway.app)
4. Or: Add custom domain (yourdomain.com - requires DNS)
```

### Step 4: Share
Send link: `https://doc-chatbot-abc123.railway.app`
- URL is permanent (won't change)
- Anyone can access
- Works 24/7

### Cost
- **Free tier**: $5 monthly credits (covers ~200 requests/day)
- For Secutix chatbot: Likely free (low traffic)
- If you exceed: Can upgrade to pay-as-you-go (~$0.0008/minute when running)

### Time to Deploy
- **5-10 minutes** total

### Dockerfile Needed?
Yes, but you likely need to create one. See "Step 5" below.

---

## Step 5: Create Dockerfile for Deployment

Create `Dockerfile` in your doc-chatbot directory:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Expose port
EXPOSE 8001

# Run app
CMD ["python", "backend.py"]
```

Create `.dockerignore`:
```
__pycache__
*.pyc
.git
.env.local
venv
.vscode
```

Create `.railway.json` (optional, for Railway settings):
```json
{
  "build": {
    "builder": "dockerfile"
  }
}
```

---

## Option 2: Render (FREE with Paid Tier)

### Why Render?
- ✅ Free tier available
- ✅ Auto-deploy from GitHub
- ✅ Custom domain support
- ⚠️ Free tier spins down after 15 minutes of inactivity (slow first load)

### Pros
- Simple UI
- Good documentation
- Can use free tier indefinitely

### Cons
- Free tier = slow (spins down)
- Paid tier: $7/month (faster)

### Deployment
1. Go to render.com
2. Sign up with GitHub
3. "New +" → Web Service
4. Connect GitHub repo
5. Configure:
   - Build command: `pip install -r requirements.txt`
   - Start command: `python backend.py`
   - Environment variables
6. Deploy

### Time to Deploy
- **10-15 minutes**

---

## Option 3: DigitalOcean App Platform (CHEAP - $7+/month)

### Why DigitalOcean?
- ✅ $4-5/month (very cheap)
- ✅ No free tier, but super affordable
- ✅ Reliable and fast
- ✅ Great documentation
- ✅ Apps always running (no cold start)
- ✅ Custom domain easy

### Pros
- Always fast (no spin-down)
- Cheap and reliable
- Great control/flexibility
- Proven hosting platform

### Cons
- Requires payment (credit card)
- Not free

### Deployment
1. Go to digitalocean.com
2. Sign up with email
3. Add payment method
4. Apps → Create App
5. Connect GitHub repo
6. Configure:
   - Dockerfile or Python buildpack
   - Environment variables
   - Port 8001
7. Deploy

### Cost Breakdown
- **App Platform**: ~$12/month (1 basic container)
- **BUT**: You can get this down to $4-5/month by using:
  - Basic tier container
  - Free managed database (if needed)
  - Optimizing FastAPI (lightweight)

### Time to Deploy
- **15-20 minutes**

---

## Option 4: Replit (FREE)

### Why Replit?
- ✅ Completely free
- ✅ Easy for beginners
- ✅ Browser-based IDE
- ⚠️ Slower than paid options

### Pros
- Free
- Super easy
- No local setup needed

### Cons
- Slow performance
- Free tier has limits
- Might need Replit Hacker (paid) for good performance

### Deployment
1. Go to replit.com
2. Create new Repl (Python)
3. Upload your code
4. Create `.replit` file:
```
run = "python backend.py"
```
5. Click Run
6. Get URL: `https://[project-name].[username].repl.co`

### Time to Deploy
- **5-10 minutes**

---

## Option 5: Heroku (Paid - $7+/month)

### Note: Heroku removed free tier in 2022

### Current Pricing
- **Basic Dyno**: $7/month (cheapest paid)
- Very reliable
- Used to be THE platform for this

### If You Want Heroku
```bash
# Install Heroku CLI
brew install heroku/brew/heroku

# Login
heroku login

# Create app
heroku create doc-chatbot

# Set environment variables
heroku config:set ANTHROPIC_SUBTOKEN=sk-ant-oat01-...
heroku config:set PINECONE_API_KEY=pcsk_...

# Deploy
git push heroku main

# Open
heroku open
```

### Time to Deploy
- **10-15 minutes**

---

## Option 6: AWS/Google Cloud Free Tier (COMPLEX - 12 months)

### AWS Free Tier
- ✅ 12 months free
- ⚠️ Requires credit card
- ⚠️ Complex setup
- ⚠️ Easy to accidentally go over limits

### Google Cloud Free Tier
- ✅ Always free (not just 12 months)
- ⚠️ Limited resources
- ⚠️ Complex setup
- ⚠️ Need to manage carefully

### Not Recommended For This Project
- Too complex for simple chatbot
- Overkill for your needs
- Takes 1-2 hours to set up

---

## Comparison Matrix

| Option | Cost | Speed | Ease | Permanence | Cold Start |
|--------|------|-------|------|-----------|-----------|
| **Railway** | Free ($5 credits) | Fast | Very Easy | ✅ Permanent | No |
| **Render Free** | Free | Medium | Easy | ✅ Permanent | 15 min ⏳ |
| **DigitalOcean** | $4-7/mo | Very Fast | Easy | ✅ Permanent | No |
| **Replit** | Free | Slow | Very Easy | ✅ Permanent | No |
| **Heroku** | $7+/mo | Fast | Easy | ✅ Permanent | No |
| **AWS Free** | Free (12mo) | Fast | Hard | ✅ Permanent | No |
| **ngrok** | Free | Fast | Very Easy | ❌ Changes | No |

---

## My Recommendation: Railway.app

**For your situation**:
- ✅ Free ($5 monthly credits covers your usage)
- ✅ Easiest to set up (GitHub auto-deploy)
- ✅ Permanent URL (can share/bookmark)
- ✅ Custom domain if you want
- ✅ No cold start issues
- ✅ ~10 minutes total

**Setup Steps** (summary):
1. Create `Dockerfile` (copy from above)
2. Push to GitHub
3. Sign up at Railway.app
4. Connect GitHub repo
5. Done! (takes 3-5 minutes to deploy)
6. Share the URL

---

## If You Want Custom Domain

### With Railway
```
1. Buy domain (Namecheap, GoDaddy, etc.) - $1-12/year
2. In Railway: Add custom domain
3. Point DNS to Railway nameservers
4. 5 minutes setup
5. Your app at: chatbot.yourdomain.com
```

### Cost
- Domain: $10/year
- Hosting: Free (Railway credits)
- **Total: ~$1/month**

---

## Step-by-Step for Railway Deployment

### 1. Create Dockerfile
```bash
cd /Users/gautam/.openclaw/agents/turing/doc-chatbot
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8001

CMD ["python", "backend.py"]
EOF
```

### 2. Create .dockerignore
```bash
cat > .dockerignore << 'EOF'
__pycache__
*.pyc
.git
.env.local
venv
.vscode
backend_old.py
.DS_Store
EOF
```

### 3. Push to GitHub
```bash
git add Dockerfile .dockerignore
git commit -m "Add Dockerfile for Railway deployment"
git push origin main
```

### 4. Deploy on Railway
1. Go to railway.app
2. Sign up with GitHub
3. Create new project → Deploy from GitHub
4. Select your doc-chatbot repo
5. Configure environment:
   ```
   ANTHROPIC_SUBTOKEN=sk-ant-oat01-...
   PINECONE_API_KEY=pcsk_...
   ```
6. Click Deploy
7. Wait 3-5 minutes
8. Get URL from Dashboard
9. Share! 🎉

### 5. Share the URL
```
Public URL: https://doc-chatbot-[random].railway.app
Share this link with anyone!
```

---

## Environment Variables Needed

For any deployment platform, you need:

```
ANTHROPIC_SUBTOKEN=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
PINECONE_API_KEY=pcsk_zK6XK_6J1gHwo5RBeQCE7CjXVGwRrK714tWZxydx4t3PVBCh71xeETBTECAu1fKukFQHF
```

**Keep these secret!** Don't put in code, only in deployment platform's secrets.

---

## Monitoring & Updates

### After Deployment

**See logs**:
- Railway: Dashboard → App → Logs
- Render: Dashboard → App → Logs
- DigitalOcean: Dashboard → App → Logs

**Update app**:
1. Make changes locally
2. `git push origin main`
3. Platform auto-deploys (if GitHub connected)
4. Wait 2-3 minutes
5. Changes live!

**Monitor uptime**:
- Most platforms have uptime monitors
- Railway: Shows uptime in dashboard
- Can add Uptime Robot (free) for monitoring

---

## Cost Summary (Monthly)

| Option | Cost | Best For |
|--------|------|----------|
| Railway | Free | Small projects, demos |
| Render Free | Free | Low-traffic projects |
| Render Paid | $7/mo | Always-fast, production |
| DigitalOcean | $5-12/mo | Production, reliability |
| Replit | Free | Learning, quick demos |

---

## My Final Recommendation

**Use Railway for now:**
1. ✅ Free
2. ✅ Fast to set up (10 minutes)
3. ✅ Permanent URL (shareable)
4. ✅ Good enough for testing with universities
5. If you need custom domain: Add later ($10/year)

**Later, if you want to scale:**
- Move to DigitalOcean ($5-12/month) for better performance
- Or keep Railway if traffic is low

---

## Next Steps

1. Create `Dockerfile` in doc-chatbot directory
2. Push to GitHub
3. Sign up at Railway.app
4. Deploy (5 minutes)
5. Get permanent public URL
6. Share with Swiss universities!

Want me to help with any specific step?
