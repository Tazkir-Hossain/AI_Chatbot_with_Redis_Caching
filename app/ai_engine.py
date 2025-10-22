import asyncio
import os
from groq import AsyncGroq

groq_client = None

def get_groq_client():
    """Get or create Groq client (singleton pattern)"""
    global groq_client
    if groq_client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key or api_key.strip() == "":
            print("⚠️ GROQ_API_KEY missing — using mock AI response instead.")
            return None
        groq_client = AsyncGroq(api_key=api_key)
    return groq_client


async def generate_ai_response(query: str) -> str:
    """Generate AI response using Groq or fallback mock"""
    try:
        client = get_groq_client()
        if client is None:
            return await generate_mock_response(query)

        model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

        chat_completion = await client.chat.completions.create(
            messages=[
                {"role": "system",
                 "content": "You are a helpful AI assistant. Provide clear, concise, and accurate responses."},
                {"role": "user", "content": query}
            ],
            model=model,
            temperature=0.7,
            max_tokens=1024,
            top_p=1,
            stream=False
        )

        return chat_completion.choices[0].message.content

    except Exception as e:
        print(f"❌ Error generating AI response: {e}")
        return await generate_mock_response(query)


async def generate_mock_response(query: str) -> str:
    """Fallback mock response"""
    await asyncio.sleep(0.5)
    return f"Mock AI response to: {query}. (Configure GROQ_API_KEY for real responses)"
