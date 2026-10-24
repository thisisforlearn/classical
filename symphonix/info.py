"""Composer info from Wikipedia (no API key)."""
import json
import urllib.parse

import requests

UA = "symphonix/1.0 (cli music tool)"

def summary(page_title: str):
    """Wikipedia REST summary: title -> dict(title, extract, url)"""
    t = urllib.parse.quote(page_title.replace(" ", "_"))
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{t}"
    r = requests.get(url, headers={"User-Agent": UA}, timeout=(6, 20))
    if r.status_code == 200:
        d = r.json()
        return {
            "title": d.get("title", page_title),
            "extract": d.get("extract", ""),
            "url": d.get("content_urls", {}).get("desktop", {}).get("page", ""),
        }
    return None

def find(query: str):
    """opensearch then summary."""
    try:
        r = requests.get("https://en.wikipedia.org/w/api.php",
                         params={"action": "opensearch", "format": "json",
                                 "search": query, "limit": 1},
                         headers={"User-Agent": UA}, timeout=(6, 20))
        if r.status_code == 200:
            titles = r.json()
            if titles and titles[1]:
                return summary(titles[1][0])
    except Exception:
        pass
    return summary(query)
