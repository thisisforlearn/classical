"""symphonix - public-domain classical music for your terminal."""
__version__ = "1.0.0"
__repo__ = "https://github.com/thisisforlearn/classical"

def __getattr__(name):
    if name == "search":
        from .search import search
        return search
    if name == "Track":
        from .track import Track
        return Track
    raise AttributeError(name)

__all__ = ["search", "Track"]
