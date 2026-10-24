"""Track scoring: title relevance for queries, podcast/collection penalties.

`best_track(results, query)` -> the most likely real performance first.
"""
BAD_MARKS = ("pcast", "podcast", "episode", "frequency", "va - ", "compilation",
             "collection", "librivox", "wikipedia", "lecture", "spiel",
             "audiobook", "npr", "radio drama", "kids classics")
STOPWORDS = {"the", "a", "in", "of", "and", "no", "op", "bwv", "k", "by",
             "from", "symphony", "concerto", "over"}


def _tokens(text):
    return set("".join(c if c.isalnum() else " " for c in text.lower()).split())


def score_track(track, query):
    title = (track.title or "").lower()
    notes = getattr(track, "performer", "") or ""
    tset = _tokens(title + " " + str(notes)[:120])
    qset = _tokens(query)
    hard_stop = {"symphony", "concerto", "overture", "prelude", "andante",
                 "allegro", "minor", "major", "in", "of", "the", "no"}
    qwords = {w for w in qset if w not in hard_stop}
    if not qwords:
        qwords = qset - {"the", "a", "of", "in", "and"}
    overlap = len(tset & qwords) / max(len(qwords), 1)
    score = overlap * 100.0
    low = title
    if any(b in low for b in BAD_MARKS):
        score -= 60.0
    if track.duration:
        m, s = track.duration.split(":")[:2] if ":" in track.duration else ("0", "0")
        try:
            dur = int(m) * 60 + float(s)
        except ValueError:
            dur = 0
        if 60 <= dur <= 1500:          # single work sweet spot
            score += 12.0
        elif dur and dur < 45:
            score -= 15.0
    if track.size:
        if track.size > 48 * 1024 * 1024:      # >48MB = file-of-everything
            score -= 18.0
        elif track.size < 512 * 1024:
            score -= 8.0
    if getattr(track, "source", "") == "archive":
        score += 3.0
    return score


def rank(results, query):
    return sorted(results, key=lambda t: (score_track(t, query) * -1,
                                          t.source != "archive"), )


def best_track(results, query):
    if not results:
        return None
    return rank(results, query)[0]
