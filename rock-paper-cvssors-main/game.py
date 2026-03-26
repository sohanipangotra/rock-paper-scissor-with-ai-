from ai import AI

WINNER = {
    ("Rock", "Scissors"): "player",
    ("Scissors", "Paper"): "player",
    ("Paper", "Rock"): "player",
    ("Scissors", "Rock"): "ai",
    ("Paper", "Scissors"): "ai",
    ("Rock", "Paper"): "ai",
}


class Game:
    def __init__(self):
        self.ai = AI()
        self.score = {"wins": 0, "losses": 0, "draws": 0}
        self.round = 0
        self.last_player_move = None
        self.last_ai_move = None
        self.last_result = None  # "win", "loss", "draw"

    def set_difficulty(self, difficulty):
        self.ai.set_difficulty(difficulty)

    def play_round(self, player_move):
        """
        pass in player gesture ("Rock", "Paper", "Scissors")
        returns result string: "win", "loss", or "draw"
        """
        ai_move = self.ai.pick_move()
        self.ai.record(player_move)

        self.last_player_move = player_move
        self.last_ai_move = ai_move
        self.round += 1

        if player_move == ai_move:
            result = "draw"
            self.score["draws"] += 1
        else:
            winner = WINNER.get((player_move, ai_move))
            if winner == "player":
                result = "win"
                self.score["wins"] += 1
            else:
                result = "loss"
                self.score["losses"] += 1

        self.last_result = result
        return result

    def get_score(self):
        return self.score

    def get_last_round(self):
        """handy for displaying results on the frame"""
        return {
            "player": self.last_player_move,
            "ai": self.last_ai_move,
            "result": self.last_result,
            "round": self.round,
        }

    def reset(self):
        self.ai.reset()
        self.score = {"wins": 0, "losses": 0, "draws": 0}
        self.round = 0
        self.last_player_move = None
        self.last_ai_move = None
        self.last_result = None
