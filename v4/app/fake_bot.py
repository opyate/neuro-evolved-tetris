import random
import time


class FakeEngine:
    def __init__(
        self,
    ):
        self.is_game_over = False

    def to_json(self):
        return {"is_game_over": self.is_game_over}

    @classmethod
    def from_json(cls, data):
        engine = cls()
        engine.is_game_over = data["is_game_over"]
        return engine


class TetrisBot:
    def __init__(self, bot_id: int, **kwargs):
        self.id = bot_id
        self.engine = FakeEngine()
        self.state = ["new"]

    def __repr__(self):
        return f"TetrisBot({self.id})"

    def think_then_move(self, do_tick: bool):
        if not self.engine.is_game_over:
            rnd = random.random()
            self.state.append(rnd)
            time.sleep(rnd / 100)
            self.engine.is_game_over = rnd < 0.01
            return True
        return False

    def get_state(self):
        return {"id": self.id, "state": self.state, "engine": self.engine.to_json()}

    def to_json(self):
        return {"id": self.id, "state": self.state, "engine": self.engine.to_json()}

    @classmethod
    def from_json(cls, data):
        bot = cls(data["id"])
        bot.state = data["state"]
        bot.engine = FakeEngine.from_json(data["engine"])
        bot.engine.is_game_over = data["engine"]["is_game_over"]
        return bot
