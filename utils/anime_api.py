import requests
import random
from .cache import get_top_anime

def search_anime(query, limit=5):
    try:
        url = f"https://api.jikan.moe/v4/anime?q={query}&limit={limit}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json().get('data', [])
        return [{
            'title': anime.get('title', 'Unknown Title'),
            'score': anime.get('score', 'N/A'),
            'episodes': anime.get('episodes', 'Null'),
            'synopsis': anime.get('synopsis', 'Unknown'),
            'genres': ', '.join(g['name'] for g in anime.get('genres', [])),
            'image_url': anime.get('images', {}).get('jpg', {}).get('image_url', ''),
            'anime_url': anime.get('url', 'https://.')
        } for anime in data]
    except:
        return []

async def fetch_valid_anime():
    try:
        top_anime = get_top_anime()
        if not top_anime:
            return None
            
        anime = random.choice(top_anime)
        return {
            'title': anime.get('title', 'Unknown'),
            'title_english': anime.get('title_english', ''),
            'score': anime.get('score', 'N/A'),
            'episodes': anime.get('episodes', 'Unknown'),
            'genres': anime.get('genres', []),
            'image_url': anime.get('images', {}).get('jpg', {}).get('image_url', '')
        }
    except:
        return None