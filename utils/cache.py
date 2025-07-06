import json
import os

def load_top_anime(path="data/top_anime_cache.json"):
    try:
        if not os.path.exists(path):
            return []
            
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_top_anime(data, path="data/top_anime_cache.json"):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

def get_top_anime():
    return load_top_anime()