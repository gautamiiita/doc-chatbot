# Secutix Documentation Chatbot - Deployment Guide

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│              User Query (Any Language)                   │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│         FastAPI Backend (backend.py)                     │
│  - Language Detection (langdetect)                       │
│  - Query Translation to English                          │
│  - Pinecone Vector Search                               │
│  - Claude API Answer Generation                          │
│  - Response Translation back to User Language           │
└──────────────────────┬──────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   ┌─────────┐  ┌──────────┐  ┌────────────┐
   │Pinecone │  │  Claude  │  │Anthropic   │
   │Index    │  │  2.1     │  │API         │
   └─────────┘  └──────────┘  └────────────┘

┌─────────────────────────────────────────────────────────┐
│      React Chat Widget (widget.jsx + widget.css)        │
│  - Embeddable on any website                            │
│  - Language selector                                    │
│  - Message history with sources                         │
│  - Responsive design (mobile + desktop)                 │
└─────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Install Dependencies

```bash
cd doc-chatbot
pip install -r requirements.txt
pip install langdetect  # For multilingual support
```

### 2. Start the FastAPI Backend

```bash
python3 backend.py
```

Server runs on `http://localhost:8000`

**API Endpoints:**

- `POST /query` - Ask a question (supports multilingual input)
- `GET /search` - Vector search only (no answer generation)
- `GET /pages` - List all indexed pages
- `GET /health` - Health check

### 3. Test the Backend

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is new in Zumstein V4?",
    "language": "en",
    "top_k": 5
  }'
```

### 4. Use the React Widget

```jsx
import SecutixChatbot from './widget.jsx';
import './widget.css';

function App() {
  return (
    <div>
      <h1>My Website</h1>
      <SecutixChatbot 
        apiUrl="https://your-api.com"
        theme="light"
      />
    </div>
  );
}

export default App;
```

## Deployment Options

### Option 1: Heroku (Easy)

```bash
# Create Procfile
echo "web: python3 backend.py" > Procfile

# Deploy
git push heroku main
```

### Option 2: Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt && pip install langdetect

COPY . .

CMD ["python3", "backend.py"]
```

```bash
docker build -t secutix-chatbot .
docker run -p 8000:8000 \
  -e ANTHROPIC_API_KEY=sk-ant-... \
  -e PINECONE_API_KEY=pcsk_... \
  secutix-chatbot
```

### Option 3: AWS Lambda + API Gateway

```bash
pip install -r requirements.txt -t ./package
cp backend.py ./package/
cd package && zip -r ../lambda.zip . && cd ..

# Upload lambda.zip to AWS Lambda
# Configure API Gateway trigger
```

### Option 4: Google Cloud Run

```bash
gcloud run deploy secutix-chatbot \
  --source . \
  --platform managed \
  --region us-central1 \
  --set-env-vars ANTHROPIC_API_KEY=sk-ant-... \
  --set-env-vars PINECONE_API_KEY=pcsk_...
```

## Multilingual Support

### How It Works

1. **Query Language Detection**: Uses `langdetect` to identify user's language
2. **Translation to English**: Translates non-English queries to English using Claude API
3. **Vector Search**: Searches Pinecone embeddings (trained on English)
4. **Answer Generation**: Claude generates answer based on retrieved documents
5. **Response Translation**: Translates answer back to user's language

### Supported Languages

- English (en)
- French (fr)
- German (de)
- Spanish (es)
- Italian (it)
- + Any language supported by langdetect

### Example: French Query

```json
{
  "question": "Qu'y a-t-il de nouveau dans Zumstein V4?",
  "language": "fr",
  "top_k": 5
}
```

**Flow:**
1. Detect: French
2. Translate: "What is new in Zumstein V4?"
3. Search & retrieve English documents
4. Generate answer in English
5. Translate answer back to French
6. Return to user

### Adding More Languages

1. Add translated pages to Pinecone with language tags
2. Update `LANGUAGE_NAMES` in `backend.py`
3. Test with `langdetect`

## Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-api03-...
PINECONE_API_KEY=pcsk_...

# Optional
UVICORN_HOST=0.0.0.0
UVICORN_PORT=8000
```

## API Response Examples

### Query Request

```json
{
  "question": "How do I install Zumstein?",
  "language": "en",
  "top_k": 5
}
```

### Query Response

```json
{
  "question": "How do I install Zumstein?",
  "answer": "To install Zumstein... [Claude's answer]",
  "sources": [
    {
      "title": "SecuTix 360° Weisshorn V1",
      "text": "Installation steps...",
      "relevance": 0.892
    }
  ],
  "language": "en",
  "detected_language": "en"
}
```

## Performance Metrics

| Operation | Time | Cost |
|-----------|------|------|
| Vector Embedding (FastEmbed) | ~20ms | $0 |
| Pinecone Search | ~50ms | $0.0001 |
| Claude API Call | ~1-2s | $0.01-0.05 |
| **Total Query** | **~2s** | **$0.01-0.05** |

## Security

### API Protection

Add rate limiting and authentication:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/query")
@limiter.limit("10/minute")
async def query(request: QueryRequest):
    # Your code
```

### CORS Configuration

Already set to allow all origins for embedding. Restrict if needed:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],
    allow_methods=["POST"],
)
```

## Monitoring

### Health Check

```bash
curl http://localhost:8000/health
```

### Logging

Check logs in `backend.py`:

```python
logger.info(f"Query: {question}")
logger.error(f"Error: {str(e)}")
```

## Troubleshooting

### Issue: "API key not found"

**Solution:** Set environment variables:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
export PINECONE_API_KEY=pcsk_...
```

### Issue: "Credit balance too low"

**Solution:** Add credits to Anthropic account at https://console.anthropic.com/account/billing

### Issue: Slow responses

**Solution:**
- Check Pinecone index performance
- Reduce `top_k` from 5 to 3
- Cache frequent queries

## Next Steps

1. ✅ Deploy backend to cloud (Heroku/Docker/AWS)
2. ✅ Build React app with widget
3. ✅ Add authentication (optional)
4. ✅ Monitor usage and costs
5. ✅ Collect user feedback
6. ✅ Add more languages by crawling translated docs

## Support

For issues:
1. Check logs: `python3 backend.py`
2. Test API: `curl http://localhost:8000/health`
3. Verify credentials: `.env` file has valid keys
