from urllib.parse import urlparse

domain = urlparse(url).netloc

if "gsmarena.com" in domain:
    ...
elif "oneplus.com" in domain:
    ...