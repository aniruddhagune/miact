from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class BaseSiteExtractor(ABC):
    
    @abstractmethod
    def extract(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Extract content, tables, and opinions from the given URL.
        Must return a dict matching the schema:
        {
            "title": str,
            "text": str,
            "published_at": Optional[str],
            "method": str,
            "source": str,
            "tables": list[dict],      # [{"aspect": str, "value": str}]
            "opinions": list[dict]     # [{"text": str, "score": int}]  (optional)
        }
        """
        pass
