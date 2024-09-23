import math
import multiprocessing
import random
import time

# from app.tetris_bot import TetrisBot
from app.fake_bot import TetrisBot
from app.worker import bots_think_then_move
from celery import Celery, group


def chunkify(lst, n):
    """Splits list into n chunks."""
    return [lst[i::n] for i in range(n)]


def main(number_of_bots: int, bot_opts: dict = None):

    bots = [TetrisBot(bot_id, **bot_opts) for bot_id in range(number_of_bots)]
    # serialize bots
    bots = [bot.to_json() for bot in bots]

    num_cores = multiprocessing.cpu_count()

    # Create a group of Celery tasks for each chunk
    job = group(
        bots_think_then_move.s(bots_slice) for bots_slice in chunkify(bots, num_cores)
    )

    return job
