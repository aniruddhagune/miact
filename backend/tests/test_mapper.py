import json
from backend.services.mapper_aspect_sentiment import analyze_aspect_sentiment

text = "The screen is bright and sharp. But the battery drains too fast. It feels premium. Does the battery last even a day? That is just terrible."
res = analyze_aspect_sentiment(text)
print(json.dumps(res, indent=2))
