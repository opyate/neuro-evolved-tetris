import multiprocessing

# from app.tetris_bot import TetrisBot
from app.fake_bot import TetrisBot
from app.worker import bots_next_round, bots_think_then_move
from celery import chord
from celery.result import AsyncResult

# TODO free up a core for server?
num_cores = multiprocessing.cpu_count()


def chunkify(lst, n):
    """Splits list into n chunks."""
    return [lst[i::n] for i in range(n)]


def main(bots: list[TetrisBot] | list[dict]) -> AsyncResult:
    """Hand bots off to Celery workers.

    If this is 0th round, bots should be a list of TetrisBot objects, as
    they would have been initialised in the server.
    If this is not 0th round, bots should be a list of dicts, as they
    would have been read from Redis.
    """

    # Check if the list contains TetrisBot objects
    # if all(isinstance(bot, TetrisBot) for bot in bots):
    if isinstance(bots[0], TetrisBot):
        bots = [bot.to_json() for bot in bots]

    return chord(
        (bots_think_then_move.s(bots_slice) for bots_slice in chunkify(bots, num_cores))
    )(bots_next_round.s())
