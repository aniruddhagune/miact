import json
import httpx
import os
import datetime
from backend.utils.logger import logger
from backend.config.variables import (
    OLLAMA_URL, OLLAMA_MODEL_INTENT, AI_PROVIDER, 
    NATIVE_MODEL_INTENT, NATIVE_MODEL_SUMMARY
)

# Providers
PROV_NATIVE = "native"
PROV_OLLAMA = "ollama"

# Global cache for native models to avoid re-loading
_NATIVE_MODELS = {
    "intent": None,
    "summary": None
}

async def _get_native_intent_model():
    if _NATIVE_MODELS["intent"] is None:
        try:
            logger.info("SYSTEM", f"Loading Featherweight Intent Model ({NATIVE_MODEL_INTENT})...")
            start = datetime.datetime.now()
            from transformers import pipeline
            # BERT-Tiny is ~18MB, extremely fast on i3 CPU
            _NATIVE_MODELS["intent"] = pipeline(
                "text-classification", 
                model=NATIVE_MODEL_INTENT, 
                device=-1 # Force CPU
            )
            duration = (datetime.datetime.now() - start).total_seconds()
            logger.info("SYSTEM", f"Intent model loaded in {duration:.2f}s")
        except Exception as e:
            logger.error("SYSTEM", f"Failed to load native intent model: {e}")
            return None
    return _NATIVE_MODELS["intent"]

async def _get_native_summary_model():
    if _NATIVE_MODELS["summary"] is None:
        try:
            logger.info("SYSTEM", f"Loading Featherweight Summary Model ({NATIVE_MODEL_SUMMARY})...")
            start = datetime.datetime.now()
            from transformers import pipeline
            # T5-Small is ~240MB, but very capable for news
            _NATIVE_MODELS["summary"] = pipeline(
                "summarization", 
                model=NATIVE_MODEL_SUMMARY, 
                device=-1 # Force CPU
            )
            duration = (datetime.datetime.now() - start).total_seconds()
            logger.info("SYSTEM", f"Summary model loaded in {duration:.2f}s")
        except Exception as e:
            logger.error("SYSTEM", f"Failed to load native summary model: {e}")
            return None
    return _NATIVE_MODELS["summary"]

async def classify_intent_ai(query: str):
    provider = globals().get("AI_PROVIDER", PROV_NATIVE)
    
    if provider == PROV_OLLAMA:
        return await _classify_intent_ollama(query)
    else:
        return await _classify_intent_native(query)

async def summarize_news_ai(content: str):
    provider = globals().get("AI_PROVIDER", PROV_NATIVE)
    
    if provider == PROV_OLLAMA:
        return await _summarize_news_ollama(content)
    else:
        return await _summarize_news_native(content)

# ---- NATIVE IMPLEMENTATIONS ----

async def _classify_intent_native(query: str):
    """
    Native intent classification. 
    """
    # Lightweight keyword heuristic for modes (backup for small models)
    query_l = query.lower()
    mode = "general"
    if any(k in query_l for k in ["news", "latest", "update", "happened"]):
        mode = "news"
    elif any(k in query_l for k in ["phone", "laptop", "spec", "vs", "compare"]):
        mode = "product"

    # Minimal logic to simulate LLM structure for the pipeline
    return {
        "intent": "QUERY",
        "entities": [],
        "focus": None,
        "mode": mode
    }

async def categorize_news_ai(content: str):
    """
    Extracts structured data from news content: Cause, Involved People, Places, Category.
    """
    provider = globals().get("AI_PROVIDER", PROV_NATIVE)
    
    if provider == PROV_OLLAMA:
        return await _categorize_news_ollama(content)
    else:
        return await _categorize_news_native(content)

async def _categorize_news_native(content: str):
    # Lightweight fallback for native: uses keywords to guess categories
    content_l = content.lower()
    categories = []
    
    # Categorization logic
    if any(k in content_l for k in ["court", "legal", "law", "judge", "lawsuit"]):
        categories.append("Legal")
    if any(k in content_l for k in ["geopolitical", "international", "summit", "relations", "treaty"]):
        categories.append("Geopolitical")
    if any(k in content_l for k in ["science", "research", "discovery", "space"]):
        categories.append("Science")
    if any(k in content_l for k in ["market", "stock", "economy", "finance"]):
        categories.append("Financial")
        
    # We return a dict for the pipeline to use
    return {
        "category": categories[0] if categories else "General News",
        "involved_people": "N/A", # Hard for small T5 to extract without specific NER
        "places": "N/A",
        "cause": "N/A"
    }

async def _categorize_news_ollama(content: str):
    url = globals().get("OLLAMA_URL", "http://localhost:11434/api/generate")
    model = "qwen2.5:0.5b"
    system_prompt = "Extract news facts in JSON: category (legal/geopolitical/etc), involved_people (list), places (list), cause (short string)."
    payload = {
        "model": model,
        "prompt": f"Analyze this news and extract facts: {content}",
        "system": system_prompt,
        "stream": False,
        "format": "json"
    }
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload)
            return json.loads(resp.json().get("response", "{}"))
    except Exception:
        return {}

async def _summarize_news_native(content: str):
    try:
        summarizer = await _get_native_summary_model()
        if not summarizer:
            return content[:200] + "..."
            
        # Truncate content to fit T5's 512 token limit for speed on i3
        input_text = content[:2000] 
        summary = summarizer(input_text, max_length=150, min_length=30, do_sample=False)
        return summary[0]['summary_text']
    except Exception as e:
        logger.error("NLP", f"Native summarization failed: {e}")
        return content[:200] + "..." # Fallback to snippet

# ---- OLLAMA IMPLEMENTATIONS (Opt-in) ----

async def _classify_intent_ollama(query: str):
    url = globals().get("OLLAMA_URL", "http://localhost:11434/api/generate")
    model = globals().get("OLLAMA_MODEL_INTENT", "qwen2.5:0.5b")
    
    system_prompt = "You are an intent classifier. Return ONLY JSON with: intent, entities, focus, mode."
    payload = {
        "model": model,
        "prompt": query,
        "system": system_prompt,
        "stream": False,
        "format": "json"
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload)
            return resp.json().get("response")
    except Exception as e:
        logger.error("NLP", f"Ollama Intent failed: {e}")
        return None

async def summarize_news_ollama(content: str):
    url = globals().get("OLLAMA_URL", "http://localhost:11434/api/generate")
    model = "qwen2.5:0.5b"
    system_prompt = "Summarize the news article. Use double newlines between paragraphs. If there are key points, use bullet points starting with '- '."
    payload = {
        "model": model,
        "prompt": f"Summarize this news: {content}",
        "system": system_prompt,
        "stream": False
    }
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload)
            return resp.json().get("response")
    except Exception:
        return None

async def generate_global_news_summary(summaries: list):
    """
    Takes multiple individual article summaries and creates one master overview.
    """
    if not summaries:
        return None
        
    combined_text = "\n---\n".join(summaries)
    provider = globals().get("AI_PROVIDER", PROV_NATIVE)
    
    if provider == PROV_OLLAMA:
        url = globals().get("OLLAMA_URL", "http://localhost:11434/api/generate")
        model = "qwen2.5:0.5b"
        system_prompt = "You are a news editor. Synthesize these multiple news summaries into one single, cohesive Executive Summary. Use clear paragraphs and bullet points for key events."
        payload = {
            "model": model,
            "prompt": f"Synthesize these reports into one master summary:\n\n{combined_text}",
            "system": system_prompt,
            "stream": False
        }
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(url, json=payload)
                return resp.json().get("response")
        except Exception:
            return "Unable to generate master summary."
    else:
        # Native fallback: just join them with better formatting
        return "\n\n".join([f"• {s}" for s in summaries[:3]])
