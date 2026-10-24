"""Composer-roulette quiz: play a recording, guess who wrote it."""
import random
import time
from .art import COMPOSERS, ORDER as ART_ORDER, art_lines
from .config import get_config, set_config
from .search import search as do_search

class QuizRunner:
    def __init__(self, ui):
        """ui: object with banner(), palette(), playback_shell(player, track) etc."""
        self.ui = ui

    def one_round(self, idx: int, total: int) -> int:
        import symphonix.search as S
        key = random.choice(ART_ORDER)
        name, era, blurb, art = COMPOSERS[key]
        pal = self.ui.palette(key)
        decoys = random.sample([k for k in ART_ORDER if k != key], 3)
        opts = [key] + decoys
        random.shuffle(opts)

        tracks = []
        try:
            tracks = S.search(query=name.split()[-1], limit=2) or []
        except Exception:
            tracks = []
        player = self.ui.player
        if tracks:
            player.play(tracks[0])
        else:
            self.ui.warn("( couldn't fetch a recording - answer by deduction )")

        self.ui.quiz_question(idx, total, era, name.split()[-1][0], opts)
        ans = input("  your guess [1-4 / s=kip]: ").strip().lower()[:1]
        player.stop()
        if ans == "s":
            return 0
        try:
            pick = opts[int(ans) - 1] if ans and ans.isdigit() else None
        except (ValueError, IndexError):
            pick = None
        correct = pick == key
        self.ui.quiz_reveal(key, correct, name, era, blurb)
        return 1 if correct else 0

    def run(self, rounds=5):
        score = 0
        for i in range(rounds):
            score += self.one_round(i + 1, rounds)
            time.sleep(1.0)
        cfg = get_config()
        best = int(cfg.get("best_quiz_score", 0) or 0)
        if score > best:
            set_config(best_quiz_score=score)
        return score, rounds, best
