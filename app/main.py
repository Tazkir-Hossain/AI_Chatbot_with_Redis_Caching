from fastapi import FastAPI, Request
from pydantic import BaseModel
import time
from app.cache import get_cached_response, set_cached_response
from app.ai_engine import generate_ai_response
import logging

from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
print("✅ Env Loaded | GROQ_API_KEY:", bool(os.getenv("GROQ_API_KEY")))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Chatbot API", version="1.0.0")


class ChatRequest(BaseModel):
    query: str


class ChatResponse(BaseModel):
    query: str
    response: str
    cached: bool
    response_time: float = None


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Middleware to track request processing time"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(round(process_time, 3))
    return response


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat_request: ChatRequest):
    """
    Main chat endpoint with Redis caching
    - Checks cache first
    - Generates AI response if cache miss
    - Stores response in cache with expiration
    """
    start_time = time.time()
    query = chat_request.query.strip()
    
    # Check Redis cache
    cached_response = await get_cached_response(query)
    
    if cached_response:
        logger.info(f"✅ CACHE HIT: Query '{query}'")
        response_time = round(time.time() - start_time, 3)
        return ChatResponse(
            query=query,
            response=cached_response,
            cached=True,
            response_time=response_time
        )
    
    # Cache miss - generate AI response
    logger.info(f"❌ CACHE MISS: Query '{query}'")
    ai_response = await generate_ai_response(query)
    
    # Store in Redis cache
    await set_cached_response(query, ai_response)
    
    response_time = round(time.time() - start_time, 3)
    return ChatResponse(
        query=query,
        response=ai_response,
        cached=False,
        response_time=response_time
    )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "AI Chatbot"}


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "AI Chatbot API",
        "endpoints": {
            "/chat": "POST - Send a chat query",
            "/health": "GET - Health check",
            "/docs": "GET - API documentation"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)