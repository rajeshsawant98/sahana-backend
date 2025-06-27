import os
import json

# 🔍 Detect Cloud Run by checking for GCP project env var
if os.getenv("K_SERVICE") or os.getenv("GOOGLE_CLOUD_PROJECT"):
    CACHE_FILE = "/tmp/seen_event_urls.json"
else:
    CACHE_FILE = "app/cache/seen_event_urls.json"

def load_url_cache():
    if not os.path.exists(CACHE_FILE):
        return set()
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except json.JSONDecodeError:
        return set()

def save_url_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(list(cache), f, indent=2)