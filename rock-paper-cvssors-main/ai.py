import random
from collections import Counter

COUNTER_MOVE = {
    "Rock": "Paper",
    "Paper": "Scissors",
    "Scissors": "Rock",
}


class AI:
    def __init__(self):
        self.history = []
        self.difficulty = "easy"

    def set_difficulty(self, difficulty):
        """easy, medium, hard"""
        self.difficulty = difficulty.lower()

    def record(self, player_move):
        """call this after every round with what the player threw"""
        self.history.append(player_move)

    def pick_move(self):
        """returns AI's move based on current difficulty"""
        if self.difficulty == "easy":
            return self._easy()
        elif self.difficulty == "medium":
            return self._medium()
        elif self.difficulty == "hard":
            return self._hard()

    def reset(self):
        """clear history between sessions if needed"""
        self.history = []

    def _easy(self):
        # pure random, no memory
        return random.choice(["Rock", "Paper", "Scissors"])

    def _medium(self):
        # look at last 5 moves only
        # counter the most frequent one 50% of the time
        recent = self.history[-5:]

        if not recent or random.random() < 0.5:
            return random.choice(["Rock", "Paper", "Scissors"])

        most_common = Counter(recent).most_common(1)[0][0]
        return COUNTER_MOVE[most_common]

    def _hard(self):
        # full session history
        # counter the most frequent move 80% of the time
        if not self.history or random.random() < 0.2:
            return random.choice(["Rock", "Paper", "Scissors"])

        most_common = Counter(self.history).most_common(1)[0][0]
        return COUNTER_MOVE[most_common]
