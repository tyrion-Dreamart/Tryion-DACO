import httpx
import asyncio
from dotenv import load_dotenv
import os

load_dotenv()

async def test():
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    print(f"API Key presente: {'SI' if api_key else 'NO'}")
    print(f"Key empieza con: {api_key[:15] if api_key else 'VACIA'}")
    
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 100,
                "messages": [{"role": "user", "content": "Di solo: OK"}],
            },
        )
        print("Status:", r.status_code)
        print("Response:", r.text[:200])

asyncio.run(test())