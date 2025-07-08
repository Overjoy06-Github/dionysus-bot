from .cache import get_top_anime
import aiohttp
import random

async def search_anime(query, limit=5):
    try:
        url = f"https://api.jikan.moe/v4/anime?q={query}&limit={limit}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                response.raise_for_status()
                data = await response.json()
                
                anime_list = data.get('data', [])
                return "None" if not anime_list else [{
                    'title': anime.get('title', 'Unknown Title'),
                    'type': anime.get('type', 'N/A'),
                    'score': anime.get('score', 'N/A'),
                    'episodes': anime.get('episodes', 'Null'),
                    'synopsis': anime.get('synopsis', 'Unknown'),
                    'genres': ', '.join(g['name'] for g in anime.get('genres', [])) if anime.get('genres') else 'None',
                    'image_url': anime.get('images', {}).get('jpg', {}).get('image_url', ''),
                    'anime_url': anime.get('url', 'https://.')
                } for anime in anime_list]
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
            'type': anime.get('type', 'Unknown'),
            'title_english': anime.get('title_english', ''),
            'score': anime.get('score', 'N/A'),
            'episodes': anime.get('episodes', 'Unknown'),
            'genres': anime.get('genres', []),
            'image_url': anime.get('images', {}).get('jpg', {}).get('image_url', '')
        }
    except:
        return None
