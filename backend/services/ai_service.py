import json
import httpx
from backend.utils.logger import logger
from backend.config.variables import OLLAMA_URL, OLLAMA_MODEL_INTENT, OLLAMA_MODEL_SUMMARY

# Default values if not in .env
DEFAULT_URL = "http://localhost:11434/api/generate"
DEFAULT_INTENT_MODEL = "qwen2.5:0.5b"
DEFAULT_SUMMARY_MODEL = "qwen2.5:0.5b"

async def call_ollama(prompt: str, model: str = None, system: str = None, json_format: bool = True):
    """Generic async caller for Ollama API."""
    url = globals().get("OLLAMA_URL", DEFAULT_URL)
    model = model or DEFAULT_INTENT_MODEL
    
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,  # Low temp for consistency
            "num_ctx": 2048      # Small context for speed on low-end CPU
        }
    }
    
    if system:
        payload["system"] = system
    
    if json_format:
        payload["format"] = "json"

    try:
        logger.debug("NLP", f"Calling Ollama ({model}) with prompt: {prompt[:100]}...")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            raw_response = data.get("response", "")
            
            if json_format:
                try:
                    return json.loads(raw_response)
                except json.JSONDecodeError:
                    logger.error("NLP", f"Failed to parse JSON from Ollama: {raw_response}")
                    return None
            return raw_response
            
    except Exception as e:
        logger.error("NLP", f"Ollama API call failed: {e}")
        return None

async def classify_intent_ai(query: str):
    """Use AI to classify query intent."""
    system_prompt = """
    You are an intent classifier for a search aggregator. 
    Classify the user query into one of these types:
    - PRODUCT_SPECS: Searching for technical specs of a product.
    - PRODUCT_COMPARISON: Comparing two or more products.
    - HOW_TO: Asking for instructions or solutions.
    - LIST_REQUEST: Asking for a list of items, materials, or solutions.
    - NEWS_QUERY: Asking for latest updates or events.
    - GENERAL_INFO: Biographies, history, or general facts.
    
    Return ONLY a JSON object with:
    {
      "intent": "INTENT_TYPE",
      "entities": ["entity1", "entity2"],
      "focus": "specific attribute or problem",
      "mode": "product" | "news" | "general"
    }
    """
    
    return await call_ollama(query, model=DEFAULT_INTENT_MODEL, system=system_prompt)

async def summarize_news_ai(content: str):
    """Summarize news content using AI."""
    system_prompt = "Summarize the following news content concisely. Focus on facts, figures, and key events."
    return await call_ollama(f"Content: {content}", model=DEFAULT_SUMMARY_MODEL, system=system_prompt, json_format=False)
