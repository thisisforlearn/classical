"""sx random - roulette of the great masterpieces."""
from .art import COMPOSERS, match_composer
from .search import search as do_search
from .masterpieces import MASTERPIECES, random_composer, random_piece, signature_piece


class RandomNobody(Exception):
    pass


def _resolve_key(name):
    if not name or name == "max":
        raise RandomNobody("no composer")
    key = match_composer(name)
    if not key or key not in MASTERPIECES:
        raise RandomNobody(name or "?")
    return key


def compute_random_piece(name=None, max_mode=False):
    """Returns (composer_key, query_string, mode_label).

    - sx random              -> random maestro, random famous work
    - sx random bach         -> random famous work BY bach
    - sx random max bach     -> bach's signature masterpiece only
    """
    name = " ".join((name or "").split()) or None
    tokens = name.split() if name else []
    if tokens and tokens[0].lower() == "max":
        max_mode = True
        tokens = tokens[1:]
        name = " ".join(tokens).strip() or None
    if name and name.lower() == "max" and not max_mode:
        name = None
        max_mode = True
    if max_mode:
        if name:
            key = _resolve_key(name)
        else:
            key = random_composer()
        sig = signature_piece(key)
        if sig:
            return key, f"{sig} {COMPOSERS[key][0].split()[-1]}", "signature masterpiece"
    if name:
        key = _resolve_key(name)
    else:
        key = random_composer()
    key, work = random_piece(key)
    return key, f"{work} {COMPOSERS[key][0].split()[-1]}".strip(), "random masterpiece"


def fetch_tracks(key, query, limit=4):
    """Find real recordings of the chosen piece; archive first, all as fallback."""
    results = []
    try:
        results = do_search(query, limit=limit, which="archive")
    except Exception:
        results = []
    if len(results) < 2:
        try:
            extra = do_search(query, limit=limit, which="all")
        except Exception:
            extra = []
        results = results + extra
    from .scoring import rank
    return rank(results, query)[:limit]


def list_masterpieces(key):
    return MASTERPIECES.get(key, [])
